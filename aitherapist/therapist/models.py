from django.db import models
from django.contrib.auth.models import User


class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_sessions")
    title = models.CharField(max_length=120, default="New Session")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=12, choices=ROLE_CHOICES)
    content = models.TextField()

    # emotion signals for UI/avatar
    emotion = models.CharField(max_length=32, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    avatar_state = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class MoodEntry(models.Model):
    MOOD_CHOICES = [
        ("very_bad", "Very Bad"),
        ("bad", "Bad"),
        ("neutral", "Neutral"),
        ("good", "Good"),
        ("very_good", "Very Good"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mood_entries")
    mood = models.CharField(max_length=16, choices=MOOD_CHOICES)
    intensity = models.IntegerField(default=3)  # 1..5
    note = models.TextField(blank=True)

    # optional AI inference
    ai_inferred = models.BooleanField(default=False)
    ai_emotion = models.CharField(max_length=32, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
