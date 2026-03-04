print("✅ LOADED NEW AitherBrain from backend/ml/brain.py")
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from ml.emotion import AitherEmotionalTones
from ml.rag import AitherRAG
from ml.safety import AitherSafety, RiskAssessment
from ml.memory import AitherMemory


class AitherBrain:
    """
    Produces an assistant reply using:
      - safety check
      - optional RAG context
      - memory context (message history + optional compaction)
      - a local text-generation model
    """

    def __init__(self):
        # Local LLM (lightweight)
        self.model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

        # Device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()

        # Memory MUST receive tokenizer + model (your AitherMemory signature)
        self.memory = AitherMemory(tokenizer=self.tokenizer, model=self.model)

        # Other modules
        self.safety = AitherSafety(self.memory)
        self.rag = AitherRAG()
        self.emotion = AitherEmotionalTones()

    def _build_system_style(self) -> str:
        return (
            "You are Aither, a supportive mental-health style assistant.\n"
            "- Be empathetic, curious, and practical.\n"
            "- Ask 1-2 thoughtful follow-up questions.\n"
            "- Avoid repeating the same generic sentence.\n"
            "- Keep responses concise (3-8 sentences).\n"
            "- Do not give medical/legal instructions.\n"
            "- If the user seems in immediate danger, encourage reaching out to trusted people or local emergency services.\n"
        )

    def _format_context(self, user_message: str) -> str:
        # RAG snippets (optional)
        rag_snippets = []
        try:
            rag_results = self.rag.retrieve(user_message, k=3)
            for r in rag_results:
                txt = (r.get("text") or "").strip()
                if txt:
                    rag_snippets.append(txt)
        except Exception:
            pass

        rag_block = ""
        if rag_snippets:
            rag_block = "\n\nRelevant context:\n" + "\n---\n".join(rag_snippets[:3]) + "\n"

        # Memory context (use your AitherMemory.toString())
        mem_block = ""
        try:
            # Compact if needed (your memory module does nothing if under token limit)
            self.memory.compact()
            history_text = self.memory.toString().strip()
            if history_text:
                mem_block = f"\n\nConversation so far:\n{history_text}\n"
        except Exception:
            pass

        return rag_block + mem_block

    def _generate(self, prompt: str) -> str:
        enc = self.tokenizer(prompt, return_tensors="pt")
        input_ids = enc["input_ids"].to(self.device)
        attention_mask = enc.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.device)

        with torch.no_grad():
            out = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=140,
                do_sample=True,
                temperature=0.8,
                top_p=0.92,
                repetition_penalty=1.12,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        full = self.tokenizer.decode(out[0], skip_special_tokens=True)

        # Strip prompt if echoed (works for some models; harmless if not)
        if full.startswith(prompt):
            full = full[len(prompt):].strip()

        return full.strip() or "I’m here with you. What’s been on your mind lately?"

    def respond(self, user_message: str) -> str:
        # 1) safety check
        assessment = self.safety.detect_crisis(user_message)
        if getattr(assessment, "riskLevel", None) in (RiskAssessment.CRITICAL, RiskAssessment.URGENT):
            return (
                "I’m really sorry you’re feeling this way. You don’t have to deal with it alone. "
                "If you feel like you might hurt yourself or you’re not safe, please reach out to local emergency services "
                "or someone you trust right now. If you want, tell me your country/city and I can help you find support options."
            )

        # 2) emotion tagging (optional)
        try:
            _emo = self.emotion.analyze(user_message)
        except Exception:
            _emo = None

        # 3) store user message into memory (your method name)
        try:
            self.memory.addMessageToContext("user", user_message)
        except Exception:
            pass

        # 4) build prompt with history + rag
        system = self._build_system_style()
        extra = self._format_context(user_message)

        prompt = (
            "<s>[INST] <<SYS>>\n"
            "You are Aither, an empathetic AI therapist.\n\n"
            "Rules:\n"
            "- Validate the user's feelings\n"
            "- Ask thoughtful follow-up questions\n"
            "- Avoid repeating generic phrases\n"
            "- Keep responses 4–6 sentences\n"
            "- Be warm and supportive\n"
            "<</SYS>>\n\n"
            f"User: {user_message}\n"
            "[/INST]\n"
        )

        # 5) generate
        reply = self._generate(prompt)

        # 6) store assistant reply
        try:
            self.memory.addMessageToContext("assistant", reply)
        except Exception:
            pass

        return reply