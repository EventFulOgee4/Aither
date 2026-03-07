print("✅ LOADED NEW AitherBrain from backend/ml/brain.py")

import re
import torch
import time
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
      - memory context
      - a local text-generation model
    """

    def __init__(self):
        self.model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=True)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print("Aither device:", self.device)
        self.model.to(self.device)
        self.model.eval()

        self.memory = AitherMemory(tokenizer=self.tokenizer, model=self.model)
        self.safety = AitherSafety(self.memory)
        self.rag = AitherRAG()
        self.emotion = AitherEmotionalTones()

        if self.tokenizer.pad_token_id is None and self.tokenizer.eos_token_id is not None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _build_system_style(self) -> str:
        return (
            "You are Aither, a warm and supportive AI companion.\n"
            "Reply directly to the user as Aither.\n"
            "Do not describe what you are about to write.\n"
            "Do not say things like 'Here is a response', 'We can write', "
            "'To respond to this user request', or similar meta commentary.\n"
            "Do not write labels like 'Aither:', 'Assistant:', 'User:', or 'Response:'.\n"
            "Do not simulate both sides of the conversation.\n"
            "Do not produce a transcript.\n"
            "Speak naturally, clearly, and compassionately.\n"
            "Usually write 4 to 7 sentences.\n"
            "Acknowledge the user's feeling and then offer practical help.\n"
            "Ask at most one gentle follow-up question.\n"
            "Usually write 2 to 4 sentences.\n"
        )

    def _format_history(self, history) -> str:
        if not history:
            return ""

        lines = []
        for item in history[-8:]:
            sender = item.get("sender", "")
            message = (item.get("message") or "").strip()
            if not message:
                continue

            if sender == "user":
                lines.append(f"User said: {message}")
            else:
                lines.append(f"Aither replied: {message}")

        return "\n".join(lines)

    def _format_context(self, user_message: str, history=None) -> str:
        rag_snippets = []
        blocks = []

        hist_block = self._format_history(history)
        if hist_block:
            blocks.append("Recent conversation:\n" + hist_block)

        use_rag = any(word in user_message.lower() for word in [
            "tips", "advice", "help", "how", "cope", "stress", "anxiety", "depression"
        ])

        if use_rag:
            try:
                rag_results = self.rag.retrieve(user_message)
                for r in rag_results[:2]:
                    txt = (r.get("text") or "").strip()
                    if txt:
                        rag_snippets.append(txt)
            except Exception as e:
                print("⚠️ RAG retrieval failed:", repr(e))

        if rag_snippets:
            blocks.append("Helpful background:\n" + "\n---\n".join(rag_snippets))

        return "\n\n".join(blocks).strip()

    def _build_chat_prompt(self, system: str, extra: str, user_message: str) -> str:
        user_content = user_message.strip()

        if extra:
            user_content = (
                f"{extra}\n\n"
                f"User message:\n{user_content}\n\n"
                f"Now reply as Aither directly to the user."
            )
        else:
            user_content = (
                f"User message:\n{user_content}\n\n"
                f"Now reply as Aither directly to the user."
            )

        messages = [
            {"role": "system", "content": system.strip()},
            {"role": "user", "content": user_content},
        ]

        if hasattr(self.tokenizer, "apply_chat_template"):
            try:
                return self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                pass

        return (
            f"<|system|>\n{system.strip()}\n"
            f"<|user|>\n{user_content}\n"
            f"<|assistant|>\n"
        )

    def _clean_model_output(self, text: str) -> str:
        cleaned = ""

        if not text:
            return ""

        text = text.replace("[INST]", "").replace("[/INST]", "")
        text = text.replace("<<SYS>>", "").replace("<</SYS>>", "")
        text = text.replace("<s>", "").replace("</s>", "")

        stop_patterns = [
            r"\n\s*User\s*:",
            r"\n\s*Assistant\s*:",
            r"\n\s*Aither\s*:",
            r"\n\s*System\s*:",
            r"<\|user\|>",
            r"<\|assistant\|>",
            r"<\|system\|>",
        ]

        cut = len(text)
        for pattern in stop_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                cut = min(cut, match.start())

        cleaned = text[:cut].strip()

        meta_prefixes = [
            r"^\s*Response\s*:\s*",
            r"^\s*Assistant\s*:\s*",
            r"^\s*Aither(\s*\(AI\))?\s*:\s*",
            r"^\s*To respond to this user request, we can write\s*:\s*",
            r"^\s*Here'?s a response\s*:\s*",
            r"^\s*We can write\s*:\s*",
            r"^\s*Suggested response\s*:\s*",
        ]

        for pattern in meta_prefixes:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

        cleaned = re.sub(r"\b(User|Assistant|Aither|AI)\s*:\s*", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\bUser\s*\.\s*", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        if len(cleaned) > 1600:
            cleaned = cleaned[:1600].rsplit(" ", 1)[0].strip() + "..."

        return cleaned

    def _generate(self, prompt: str) -> str:
        raw = ""
        cleaned = ""

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        input_len = inputs["input_ids"].shape[1]

        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=140,
                min_new_tokens=24,
                do_sample=True,
                temperature=0.65,
                top_p=0.9,
                repetition_penalty=1.08,
                no_repeat_ngram_size=3,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                use_cache=True,
            )

        new_tokens = out[0][input_len:]
        raw = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        cleaned = self._clean_model_output(raw)

        return cleaned or "I’m here with you. Tell me a little more."

    def respond(self, user_message: str, history=None) -> str:
        assessment = self.safety.detect_crisis(user_message)
        if getattr(assessment, "riskLevel", None) in (RiskAssessment.CRITICAL, RiskAssessment.URGENT):
            return (
                "I’m really sorry you’re feeling this way. You don’t have to deal with it alone. "
                "If you feel like you might hurt yourself or you’re not safe, please reach out to local emergency services "
                "or someone you trust right now. Tell me your country or city and I’ll help you find the right support."
            )

        try:
            if hasattr(self.emotion, "analyze"):
                self.emotion.analyze(user_message)
            elif hasattr(self.emotion, "detect_tone"):
                self.emotion.detect_tone(user_message)
            elif hasattr(self.emotion, "get_tone"):
                self.emotion.get_tone(user_message)
        except Exception as e:
            print("⚠️ emotion analysis failed:", repr(e))

        system = self._build_system_style()
        extra = self._format_context(user_message, history=history)
        prompt = self._build_chat_prompt(system, extra, user_message)

        return self._generate(prompt)