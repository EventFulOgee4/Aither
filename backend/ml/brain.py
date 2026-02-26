print("✅ LOADED NEW AitherBrain from backend/ml/brain.py")
import time
from dataclasses import asdict

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

from ml.emotion import AitherEmotion
from ml.rag import AitherRAG
from ml.safety import AitherSafety, RiskAssessment
from ml.memory import AitherMemory


class AitherBrain:
    """
    Produces an assistant reply using:
      - safety check
      - optional RAG context
      - optional memory summary
      - a real local text-generation model
    """

    def __init__(self):
        # Core modules
        self.memory = AitherMemory()
        self.safety = AitherSafety(self.memory)
        self.rag = AitherRAG()
        self.emotion = AitherEmotion()

        # Local LLM (lightweight)
        self.model_name = "microsoft/DialoGPT-medium"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

        # CPU by default (works everywhere)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()

    def _build_system_style(self) -> str:
        # Keep it “therapy-like” but safe, not medical.
        return (
            "You are Aither, a supportive mental-health style assistant.\n"
            "- Be empathetic, curious, and practical.\n"
            "- Ask 1-2 thoughtful follow-up questions.\n"
            "- Do NOT repeat the same generic sentence every time.\n"
            "- Keep responses concise (3-8 sentences).\n"
            "- Do not give medical/legal instructions.\n"
            "- If user seems in danger, encourage reaching out to trusted people or local emergency services.\n"
        )

    def _format_context(self, user_message: str) -> str:
        # RAG (if you have docs indexed)
        rag_snippets = []
        try:
            rag_results = self.rag.retrieve(user_message, k=3)
            for r in rag_results:
                txt = r.get("text") or ""
                if txt.strip():
                    rag_snippets.append(txt.strip())
        except Exception:
            pass

        rag_block = ""
        if rag_snippets:
            rag_block = "\n\nRelevant context:\n" + "\n---\n".join(rag_snippets[:3]) + "\n"

        # Memory summary (if your memory module supports it)
        mem_block = ""
        try:
            summary = self.memory.get_summary()  # if exists
            if summary:
                mem_block = f"\n\nKnown user context:\n{summary}\n"
        except Exception:
            pass

        return rag_block + mem_block

    def _generate(self, prompt: str) -> str:
        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            out = self.model.generate(
                inputs,
                max_new_tokens=140,
                do_sample=True,
                temperature=0.8,
                top_p=0.92,
                repetition_penalty=1.12,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        full = self.tokenizer.decode(out[0], skip_special_tokens=True)

        # Strip the prompt prefix if it’s echoed back
        if full.startswith(prompt):
            full = full[len(prompt):].strip()

        # Safety: don’t return empty
        return full.strip() or "I’m here with you. What’s been on your mind lately?"

    def respond(self, user_message: str) -> str:
        # 1) safety check
        assessment = self.safety.detect_crisis(user_message)
        if assessment.riskLevel in (RiskAssessment.CRITICAL, RiskAssessment.URGENT):
            # Keep it safe (no graphic details, no “how-to”)
            return (
                "I’m really sorry you’re feeling this way. You don’t have to deal with it alone. "
                "If you feel like you might hurt yourself or you’re not safe, please reach out to local emergency services "
                "or someone you trust right now. If you want, tell me where you are (country/city) and I can help you find the right support options."
            )

        # 2) emotion tagging (optional)
        try:
            emo = self.emotion.analyze(user_message)  # if your module returns dict/tuple
        except Exception:
            emo = None

        # 3) store message into memory if your module supports it
        try:
            self.memory.add_turn(user_message=user_message)
        except Exception:
            pass

        # 4) build prompt
        system = self._build_system_style()
        extra = self._format_context(user_message)

        prompt = (
            f"{system}\n"
            f"{extra}\n"
            f"User: {user_message}\n"
            f"Aither:"
        )

        # 5) generate
        reply = self._generate(prompt)

        # 6) store assistant reply
        try:
            self.memory.add_turn(assistant_message=reply)
        except Exception:
            pass

        return reply