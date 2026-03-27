print("✅ LOADED AitherBrain (Groq API) from backend/ml/brain.py")

import re
from groq import Groq
from decouple import config

from ml.emotion import AitherEmotionalTones
from ml.rag import AitherRAG
from ml.safety import AitherSafety, RiskAssessment
from ml.memory import AitherMemory


class AitherBrain:
    """
    AitherBrain powered by Groq API (llama-3.1-8b-instant).
    - Zero local RAM usage for the LLM
    - Much better response quality than TinyLlama
    - Free tier: 14,400 requests/day, 500,000 tokens/minute
    """

    MODEL = "llama-3.1-8b-instant"

    def __init__(self):
        api_key = config("GROQ_API_KEY", default=None)
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY not set. Add it to your .env file:\n"
                "GROQ_API_KEY=your_key_here"
            )
        self.client = Groq(api_key=api_key)
        print(f"✅ Groq client ready — model: {self.MODEL}")

        # These still run locally but are tiny (~200MB total)
        self.memory = AitherMemory(tokenizer=None, model=None)
        self.safety = AitherSafety(self.memory)
        self.rag = AitherRAG()
        self.emotion = AitherEmotionalTones()

    def _build_system_prompt(self) -> str:
        return (
            "You are Aither, a warm, empathetic, and supportive AI companion "
            "focused on mental wellness and personal growth.\n"
            "Guidelines:\n"
            "- Respond directly and naturally, as if talking to a friend\n"
            "- Acknowledge the user's feelings before offering advice\n"
            "- Keep responses concise: 3-5 sentences unless more detail is needed\n"
            "- Ask at most one gentle follow-up question per response\n"
            "- Never use labels like 'Aither:', 'User:', or 'Assistant:'\n"
            "- Never say things like 'As an AI...' or 'I cannot...'\n"
            "- If the user seems distressed, prioritize emotional support over advice\n"
            "- Draw on evidence-based approaches (CBT, mindfulness, DBT) when relevant"
        )

    def _format_history(self, history) -> list:
        """Convert Django chat history to Groq message format."""
        messages = []
        if not history:
            return messages
        for item in history[-8:]:  # Last 8 turns
            sender = item.get("sender", "")
            message = (item.get("message") or "").strip()
            if not message:
                continue
            role = "user" if sender == "user" else "assistant"
            messages.append({"role": role, "content": message})
        return messages

    def _get_rag_context(self, user_message: str) -> str:
        """Get relevant knowledge base snippets for the message."""
        use_rag = any(word in user_message.lower() for word in [
            "tips", "advice", "how", "cope", "stress", "anxiety",
            "depression", "help", "breathe", "calm", "sleep", "worry",
            "sad", "angry", "lonely", "habit", "motivation"
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

    def respond(self, user_message: str, history=None) -> str:
        # Crisis check first
        try:
            assessment = self.safety.detect_crisis(user_message)
            if getattr(assessment, "riskLevel", None) in (
                RiskAssessment.CRITICAL, RiskAssessment.URGENT
            ):
                return (
                    "I'm really sorry you're feeling this way — you don't have to face it alone. "
                    "Please reach out to emergency services or someone you trust right now. "
                    "If you tell me your country or city, I can help you find the right crisis support line."
                )
        except Exception as e:
            print("⚠️ Safety check failed:", repr(e))

        # Emotion analysis
        try:
            if hasattr(self.emotion, "analyze"):
                self.emotion.analyze(user_message)
            elif hasattr(self.emotion, "detect_tone"):
                self.emotion.detect_tone(user_message)
        except Exception as e:
            print("⚠️ Emotion analysis failed:", repr(e))

        # Build messages for Groq
        system = self._build_system_prompt()
        rag_context = self._get_rag_context(user_message)

        if rag_context:
            system += f"\n\nRelevant knowledge you can draw on:\n{rag_context}"

        messages = [{"role": "system", "content": system}]
        messages += self._format_history(history)
        messages.append({"role": "user", "content": user_message})

        # Call Groq API
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                max_tokens=300,
                temperature=0.75,
                top_p=0.9,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print("⚠️ Groq API call failed:", repr(e))
            return "I'm here with you. Something went wrong on my end — could you try again?"