# memory.py
# When running with Groq/Anthropic API, tokenizer and model are both None.
# In that case we skip all the heavy aither_config imports entirely.

class AitherMemory():
    HISTORY_BUFFER = 600

    def __init__(self, tokenizer, model):
        self.messages = []
        self.tokenizer = tokenizer
        self.model = model

        # Only load aither_config settings if we have a real local model
        if tokenizer is not None and model is not None:
            try:
                from aither_config.setup.config import AitherTrainingConfig as settings
                self.max_history_tokens = settings.contextWindow - self.HISTORY_BUFFER
            except Exception as e:
                print("⚠️ AitherMemory: could not load config, using default:", repr(e))
                self.max_history_tokens = 2048 - self.HISTORY_BUFFER
        else:
            # API mode — no local model, memory is managed by the API's context window
            self.max_history_tokens = 2048 - self.HISTORY_BUFFER

    def addMessageToContext(self, role, content):
        self.messages.append({"role": role, "content": content})

    def getCurrentTokens(self):
        if self.tokenizer is None:
            # Rough estimate: 1 token ≈ 4 characters
            text = "".join(m["role"] + m["content"] for m in self.messages)
            return len(text) // 4
        try:
            text = ""
            for message in self.messages:
                text += message["role"] + ": " + message["content"] + "\n"
            self.current_tokens = self.tokenizer.encode(text)
            return len(self.current_tokens["input_ids"][0])
        except Exception:
            return 0

    def compact(self):
        if self.tokenizer is None or self.model is None:
            # In API mode, just keep the last 10 messages
            if len(self.messages) > 10:
                self.messages = self.messages[-10:]
            return

        if self.getCurrentTokens() < self.max_history_tokens:
            return

        recent_messages   = 6
        summary_messages  = self.messages[:-recent_messages]
        current_messages  = self.messages[-recent_messages:]

        conversation_text = ""
        for message in summary_messages:
            conversation_text += message["role"] + ": " + message["content"] + "\n"

        summary_prompt = f"""You are Aither, an AI Therapist specializing in Mental Health and Psychology.

Summarize the following conversation between you and the user. Capture:
- Key issues or concerns the user expressed
- Emotional states mentioned
- Important personal details shared
- Any progress or insights reached

Keep the summary concise (2-3 sentences).

Conversation:
{conversation_text}

Summary:"""

        try:
            inputText = self.tokenizer.tokenizer(summary_prompt, return_tensors="pt")
            output    = self.model.generate(inputText["input_ids"])
            response  = self.tokenizer.tokenizer.decode(output[0])
            self.messages = [{"role": "system", "content": response}] + current_messages
        except Exception as e:
            print("⚠️ Memory compact failed:", repr(e))
            self.messages = current_messages

    def toString(self):
        result = ""
        for message in self.messages:
            result += message["role"] + ": " + message["content"] + "\n"
        return result