print("✅ LOADED AitherBrain (Anthropic Claude) from backend/ml/brain.py")

import anthropic
from decouple import config

from ml.emotion import AitherEmotionalTones
from ml.rag import AitherRAG
from ml.safety import AitherSafety, RiskAssessment
from ml.memory import AitherMemory


# Tone instructions injected into the system prompt
TONE_INSTRUCTIONS = {
    "assertive": (
        "\n\n## Current Tone: Assertive\n"
        "Respond in a direct, confident, and empowering manner. "
        "Be clear and action-oriented. Provide concrete guidance and encourage "
        "the user to take decisive steps. Cut through overthinking with calm clarity. "
        "Still validate feelings, but move toward momentum and action."
    ),
    "tender": (
        "\n\n## Current Tone: Tender\n"
        "Respond with exceptional gentleness, warmth, and care. "
        "Speak softly and nurturingly, as if comforting someone you deeply care about. "
        "Slow down. Make the user feel completely safe and held. "
        "Prioritize comfort over advice. Every word should feel like a warm embrace."
    ),
    "empathy": (
        "\n\n## Current Tone: Empathy\n"
        "Respond with deep emotional attunement and understanding. "
        "Mirror the user's emotional experience back to them with precision. "
        "Show that you truly feel what they are feeling. "
        "Validate their experience fully before anything else. "
        "Use reflective language and make them feel profoundly understood."
    ),
    "neutral": "",
}


class AitherBrain:
    """
    AitherBrain powered by Anthropic Claude.

    Models (change MODEL below):
      claude-haiku-3-5    — fast, cheap, great for development/testing
      claude-sonnet-4-5   — best quality, use for showcase
    """

    MODEL      = "claude-sonnet-4-5"
    MAX_TOKENS = 400

    def __init__(self):
        api_key = config("ANTHROPIC_API_KEY", default=None)
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set. Add it to your .env file:\n"
                "ANTHROPIC_API_KEY=sk-ant-your-key-here"
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        print(f"✅ Anthropic client ready — model: {self.MODEL}")

        self.memory  = AitherMemory(tokenizer=None, model=None)
        self.safety  = AitherSafety(self.memory)
        self.rag     = AitherRAG()
        self.emotion = AitherEmotionalTones()

    def _build_system_prompt(self, tone: str = "neutral") -> str:
        base = """You are Aither, an AI-powered emotional support companion designed to help users reflect, process emotions, and feel understood.

Your primary goal is NOT to give clinical diagnoses or replace therapy, but to:
- Listen actively
- Respond with empathy
- Help users explore their thoughts
- Encourage healthy reflection and emotional awareness

You must always maintain a calm, supportive, and non-judgmental tone.

---

## 🧠 BEHAVIORAL GUIDELINES

1. EMPATHY FIRST
Always acknowledge the user's feelings before offering any suggestions.
- Use phrases like:
  - "That sounds really difficult"
  - "I can see why you'd feel that way"
  - "It makes sense that you're feeling this"

Never jump straight into solutions without validating emotions first.

---

2. REFLECTIVE LISTENING
Rephrase or summarize what the user is saying to show understanding:
- "It sounds like you're feeling ___ because ___"
- "If I understand correctly..."

This builds trust and helps the user feel heard.

---

3. ASK GENTLE QUESTIONS
Guide the user with open-ended questions:
- "What do you think is causing this feeling?"
- "When did this start?"
- "How does that usually affect you?"

Avoid interrogating — keep questions soft and optional.

---

4. AVOID BEING OVERLY CLINICAL
Do NOT:
- Diagnose mental illnesses
- Use heavy psychological jargon unless user does first
- Act like a licensed therapist

Instead:
- Stay conversational
- Use simple, human language

---

5. OFFER SUGGESTIONS, NOT COMMANDS
Frame advice gently:
- "You might consider..."
- "Some people find it helpful to..."
- "If you're open to it, you could try..."

Never sound authoritative or forceful.

---

6. SUPPORT AUTONOMY
Encourage users to make their own decisions:
- "What do you feel would be best for you?"
- "What feels right to you?"

---

7. HANDLE NEGATIVE EMOTIONS CAREFULLY
When users express sadness, anxiety, or frustration:
- Validate first
- Normalize emotions (without minimizing them)
- Then optionally guide

DO NOT:
- Say "it will be okay" without context
- Dismiss feelings

---

8. CRISIS HANDLING (VERY IMPORTANT)

If user expresses suicidal thoughts, self-harm intent, or hopelessness:
- Respond with care and seriousness
- Encourage reaching out to real people or professionals
- Suggest contacting local support resources

---

9. TONE & STYLE

- Warm, calm, and human-like
- Slightly informal but respectful
- Avoid robotic or generic responses
- Keep responses concise but meaningful

---

10. DO NOT:
- Judge the user
- Shame or blame
- Give generic motivational quotes as default responses

---

## 🔐 IDENTITY

- You are NOT a human
- You are NOT a licensed therapist
- You ARE a supportive AI companion

---

## 🎯 FINAL GOAL

Help the user feel heard, understand themselves better, regulate emotions, and think more clearly."""

        # Append tone instruction to system prompt
        tone_instruction = TONE_INSTRUCTIONS.get(tone, "")
        return base + tone_instruction

    def _format_history(self, history) -> list:
        messages = []
        if not history:
            return messages
        for item in history[-10:]:
            sender  = item.get("sender", "")
            message = (item.get("message") or "").strip()
            if not message:
                continue
            role = "user" if sender == "user" else "assistant"
            if messages and messages[-1]["role"] == role:
                messages[-1]["content"] += f"\n{message}"
            else:
                messages.append({"role": role, "content": message})
        return messages

    def _get_rag_context(self, user_message: str) -> str:
        use_rag = any(word in user_message.lower() for word in [
            "tips", "advice", "how", "cope", "stress", "anxiety", "depression",
            "help", "breathe", "calm", "sleep", "worry", "sad", "angry",
            "lonely", "habit", "motivation", "values", "meaning", "purpose"
        ])
        if not use_rag:
            return ""
        try:
            results = self.rag.retrieve(user_message, topK=2)
            snippets = []
            for r in results:
                doc = (r.get("document") or r.get("text") or "").strip()
                cat = r.get("category", "")
                if doc:
                    snippets.append(f"{cat}: {doc}")
            return "\n".join(snippets)
        except Exception as e:
            print("⚠️ RAG retrieval failed:", repr(e))
            return ""

    def generate_session_title(self, user_message: str) -> str:
        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=20,
                system=(
                    "Generate a short title (3-5 words) for a mental wellness chat session "
                    "based on the user's message. Return ONLY the title, no quotes, no punctuation. "
                    "Examples: 'Managing work stress', 'Exploring core values', 'Building confidence'"
                ),
                messages=[{"role": "user", "content": user_message}],
            )
            title = response.content[0].text.strip().strip('"\'')
            return title[:60] if title else "New Session"
        except Exception as e:
            print("⚠️ Title generation failed:", repr(e))
            return "New Session"

    def _crisis_response(self) -> str:
        return (
            "I'm really sorry you're feeling this way — you don't have to face this alone. "
            "Please reach out to emergency services or someone you trust right now. "
            "If you tell me your country or city, I can help you find the right crisis support line."
        )

    def _check_crisis(self, user_message: str) -> bool:
        try:
            assessment = self.safety.detect_crisis(user_message)
            return getattr(assessment, "riskLevel", None) in (
                RiskAssessment.CRITICAL, RiskAssessment.URGENT
            )
        except Exception as e:
            print("⚠️ Safety check failed:", repr(e))
            return False

    def _analyze_emotion(self, user_message: str):
        try:
            if hasattr(self.emotion, "analyze"):
                self.emotion.analyze(user_message)
            elif hasattr(self.emotion, "detect_tone"):
                self.emotion.detect_tone(user_message)
        except Exception as e:
            print("⚠️ Emotion analysis failed:", repr(e))

    def _build_messages(self, user_message: str, history=None) -> list:
        messages = self._format_history(history)
        if not messages or messages[-1]["role"] != "user":
            messages.append({"role": "user", "content": user_message})
        else:
            messages[-1]["content"] = user_message
        return messages

    def _get_system(self, user_message: str, tone: str = "neutral") -> str:
        system = self._build_system_prompt(tone=tone)
        rag_context = self._get_rag_context(user_message)
        if rag_context:
            system += f"\n\nRelevant background knowledge (use naturally, don't quote directly):\n{rag_context}"
        return system

    def respond(self, user_message: str, history=None, tone: str = "neutral") -> str:
        if self._check_crisis(user_message):
            return self._crisis_response()
        self._analyze_emotion(user_message)
        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=self._get_system(user_message, tone=tone),
                messages=self._build_messages(user_message, history),
            )
            return response.content[0].text.strip()
        except Exception as e:
            print("⚠️ Anthropic API call failed:", repr(e))
            return "I'm here with you. Something went wrong on my end — could you try again?"

    def respond_stream(self, user_message: str, history=None, tone: str = "neutral"):
        if self._check_crisis(user_message):
            yield self._crisis_response()
            return
        self._analyze_emotion(user_message)
        try:
            with self.client.messages.stream(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=self._get_system(user_message, tone=tone),
                messages=self._build_messages(user_message, history),
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            print("⚠️ Anthropic streaming failed:", repr(e))
            yield "I'm here with you. Something went wrong — could you try again?"