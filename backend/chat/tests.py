import json
import os
from unittest.mock import patch
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from .models import ChatMessage, MoodEntry, TherapySession


class ChatTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner')
        self.other = User.objects.create_user(username='other')
        self.session = TherapySession.objects.create(user=self.user, title='Existing')
        self.foreign = TherapySession.objects.create(user=self.other, title='Private')
        self.client.force_authenticate(self.user)

    def test_session_privacy(self):
        result = self.client.get('/api/chat/sessions/').data['results']
        self.assertEqual([s['id'] for s in result], [self.session.id])
        self.assertEqual(self.client.delete(f'/api/chat/sessions/{self.foreign.id}/').status_code, 404)

    def test_mood_ownership_and_range(self):
        for session, intensity in [(self.foreign.id, 5), (self.session.id, 0), (self.session.id, 11)]:
            result = self.client.post('/api/chat/moods/', {'session': session, 'mood': 'happy', 'intensity': intensity})
            self.assertEqual(result.status_code, 400)
        self.assertFalse(MoodEntry.objects.exists())
        self.assertEqual(self.client.post('/api/chat/moods/', {'session': self.session.id, 'mood': 'happy', 'intensity': 8}).status_code, 201)

    def test_stream_validation(self):
        for message in ['', '  ', [], {'text': 'hello'}, 'x' * 2001]:
            result = self.client.post('/api/chat/stream/', {'message': message}, format='json')
            self.assertEqual(result.status_code, 400)
        self.assertEqual(self.client.post('/api/chat/stream/', {'session': 'invalid', 'message': 'Hi'}).status_code, 400)
        self.assertFalse(ChatMessage.objects.exists())

    def test_stream_ownership(self):
        result = self.client.post('/api/chat/stream/', {'session': self.foreign.id, 'message': 'Hi'})
        self.assertEqual(result.status_code, 404)

    @patch('chat.views.get_brain')
    def test_stream_tone_and_persistence(self, get_brain):
        brain = get_brain.return_value
        brain.respond_stream.return_value = iter(['Hello ', 'there'])
        result = self.client.post('/api/chat/stream/', {'session': self.session.id, 'message': 'Hi', 'tone': 'tender'})
        events = [json.loads(line[6:]) for line in b''.join(result.streaming_content).decode().splitlines() if line.startswith('data: ')]
        self.assertEqual(events[-1]['type'], 'done')
        self.assertEqual(ChatMessage.objects.get(sender='ai').message, 'Hello there')
        self.assertEqual(brain.respond_stream.call_args.kwargs['tone'], 'tender')
        self.session.refresh_from_db()
        self.assertEqual(self.session.message_count, 2)

    @patch('chat.views.get_brain')
    def test_stream_failure_is_explicit(self, get_brain):
        get_brain.return_value.respond_stream.side_effect = RuntimeError('provider unavailable')
        result = self.client.post('/api/chat/stream/', {'session': self.session.id, 'message': 'Hi'})
        content = b''.join(result.streaming_content).decode()
        self.assertIn('"type": "error"', content)
        self.assertFalse(ChatMessage.objects.filter(sender='ai').exists())
        self.session.refresh_from_db()
        self.assertEqual(self.session.message_count, 1)

    @patch('chat.views.generate_ai_response', return_value=('Hello', 'test-model'))
    def test_standard_chat(self, generate):
        result = self.client.post('/api/chat/messages/', {'session': self.session.id, 'message': 'Hi', 'sender': 'ai'})
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.data['user_message']['sender'], 'user')
        self.assertEqual(result.data['session']['message_count'], 2)
        self.assertEqual(self.client.post('/api/chat/messages/', {'session': self.foreign.id, 'message': 'Hi'}).status_code, 400)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post('/api/chat/stream/', {'message': 'Hi'}).status_code, 401)

    def test_empty_session_metadata(self):
        result = self.client.get(f'/api/chat/sessions/{self.session.id}/metadata/')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['session_duration_seconds'], 0)
        self.assertIsNone(result.data['average_mood'])
        self.assertEqual(self.client.get(f'/api/chat/sessions/{self.foreign.id}/metadata/').status_code, 404)

    @patch.dict(os.environ, {'AITHER_MODEL_PROVIDER': 'openai_compatible', 'AITHER_MODEL_NAME': 'test-model'})
    def test_api_engine_initializes_without_local_model_packages(self):
        from ml.brain import AitherBrain
        brain = AitherBrain()
        self.assertIsNone(brain.rag)
        self.assertIsNone(brain.model)
        self.assertEqual(brain.provider, 'openai_compatible')
        history = [{'sender': 'user', 'message': 'Earlier'}, {'sender': 'ai', 'message': 'Hello'}]
        self.assertEqual(brain._build_messages('Now', history)[-1], {'role': 'user', 'content': 'Now'})
