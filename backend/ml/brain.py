print("✅ LOADED NEW AitherBrain from backend/ml/brain.py")

import re
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
        self.model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=True)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()

        # Your memory module expects tokenizer + model
        self.memory = AitherMemory(tokenizer=self.tokenizer, model=self.model)

        self.safety = AitherSafety(self.memory)
        self.rag = AitherRAG()
        self.emotion = AitherEmotionalTones()

        # If pad token is missing, set it to eos to avoid warnings/errors
        if self.tokenizer.pad_token_id is None and self.tokenizer.eos_token_id is not None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _build_system_style(self) -> str:
        return (
            "You are Aither, an empathetic AI mental-health companion.\n"
            "Your role is to help users reflect on their emotions and feel understood.\n\n"

            "Guidelines:\n"
            "- Respond like a supportive conversation partner, not a self-help article.\n"
            "- Do NOT produce numbered lists or long step-by-step guides unless explicitly requested.\n"
            "- Focus first on understanding the user's feelings before giving advice.\n"
            "- Validate the emotion the user expresses.\n"
            "- Keep answers short (3–5 sentences).\n"
            "- Ask one gentle follow-up question to encourage reflection.\n"
            "- Do not include labels like 'Assistant:', 'Response', 'AI:', or 'Aither:'.\n"
            "- Output only the assistant's reply.\n"
            "- Do not give more than 5 suggestions at once.\n"
            "- Prefer short paragraphs over lists.\n"
            "-If you feel like it is necessary add some emojis based on the mood of the user which can cheer them up\n"
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
            rag_block = "Relevant context:\n" + "\n---\n".join(rag_snippets[:3])

        # Memory context (use your AitherMemory.toString())
        mem_block = ""
        try:
            self.memory.compact()
            history_text = self.memory.toString().strip()
            if history_text:
                mem_block = f"Conversation so far:\n{history_text}"
        except Exception:
            pass

        parts = [p for p in [mem_block, rag_block] if p]
        return ("\n\n".join(parts)).strip()

    def _build_chat_prompt(self, system: str, extra: str, user_message: str) -> str:
        """
        Prefer tokenizer.apply_chat_template if available (best for chat models).
        Fallback to TinyLlama-style tags.
        """
        content_user = user_message.strip()
        if extra:
            content_user = f"{extra}\n\nUser message:\n{content_user}"

        messages = [
            {"role": "system", "content": system.strip()},
            {"role": "user", "content": content_user},
        ]

        # Best-case: tokenizer knows the model's chat template
        if hasattr(self.tokenizer, "apply_chat_template"):
            try:
                return self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                pass

        # Fallback (works well for many TinyLlama/Llama-chat variants)
        return (
            f"<|system|>\n{system.strip()}\n"
            f"<|user|>\n{content_user}\n"
            f"<|assistant|>"
        )

    def _clean_reply(self, text: str) -> str:
        """
        Remove prompt artifacts and prevent the model from continuing with new roles.
        """
        if not text:
            return ""

        # Strip common artifacts/tags if they leak
        text = text.replace("[INST]", "").replace("[/INST]", "")
        text = text.replace("<<SYS>>", "").replace("<</SYS>>", "")

        # Hard stop if the model starts writing new roles / transcript
        stop_markers = [
            "\nUser:", "\nuser:", "\nUSER:",
            "\nAssistant:", "\nassistant:", "\nASSISTANT:",
            "\nAither:", "\nAI:", "\nSystem:", "\nSYSTEM:",
            "<|user|>", "<|system|>", "<|assistant|>",
        ]
        cut = len(text)
        for m in stop_markers:
            idx = text.find(m)
            if idx != -1:
                cut = min(cut, idx)

        text = text[:cut].strip()

        # Remove accidental leading role labels
        text = re.sub(r"^(Aither|Assistant|AI)\s*:\s*", "", text, flags=re.IGNORECASE).strip()

        return text
    
    def _clean_model_output(self, text: str) -> str:
        if not text:
            return ""

        # Cut off if the model starts continuing the conversation/log
        stop_markers = [
            "\nUser:", "\nUSER:", "\nuser:",
            "\nAither:", "\nAI:", "\nAssistant:", "\nASSISTANT:",
            "[INST]", "[/INST]", "<<SYS>>", "<</SYS>>",
            "<s>", "</s>"
        ]

        cut = len(text)
        for m in stop_markers:
            idx = text.find(m)
            if idx != -1:
                cut = min(cut, idx)

        cleaned = text[:cut].strip()

        # Sometimes it starts with a leftover label
        for prefix in ("Aither:", "AI:", "Assistant:"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()

        return cleaned

    def _generate(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        input_len = inputs["input_ids"].shape[1]

        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=True,
                temperature=0.55,
                top_p=0.9,
                repetition_penalty=1.12,
                no_repeat_ngram_size=4,  # helps reduce looping / transcript continuation
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # Only decode tokens generated AFTER the prompt
        new_tokens = out[0][input_len:]
        raw = self.tokenizer.decode(new_tokens, skip_special_tokens=True)

        cleaned = self._clean_model_output(raw)

        return cleaned or "I’m here with you. What’s been on your mind lately?"

    def respond(self, user_message: str) -> str:
        # TEMP FIX: avoid cross-turn / cross-session contamination
        try:
            self.memory.messages = []
        except Exception:
            pass
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

        # 3) store user message into memory
        try:
            self.memory.addMessageToContext("user", user_message)
        except Exception:
            pass

        # 4) build prompt with history + rag
        system = self._build_system_style()
        extra = self._format_context(user_message)
        prompt = self._build_chat_prompt(system, extra, user_message)

        # 5) generate
        reply = self._generate(prompt)

        # 6) store assistant reply
        try:
            self.memory.addMessageToContext("assistant", reply)
        except Exception:
            pass

        return reply