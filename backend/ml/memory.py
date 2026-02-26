from model.aither.setup.tokenization import AitherTokenizer as tok
from model.aither.setup.config import AitherTrainingConfig as settings
from model.aither.setup.model import AitherModel as model


class AitherMemory():
    HISTORY_BUFFER = 600 # Reserve this amount for Compacting conversation within the scope of allocated window
    def __init__(self, tokenizer, model):
        self.messages = []
        self.max_history_tokens = settings.contextWindow - self.HISTORY_BUFFER
        self.tokenizer = tokenizer
        self.model = model

    #Adds message to context
    def addMessageToContext(self, role, content):
        self.messages.append({"role" : role, "content" : content})
    
    #Gets number of current tokens remaining
    def getCurrentTokens(self):
        text = ""
        for message in self.messages:
            role = message["role"]
            content = message["content"]
            text += role + ": " + content + "\n"
        self.current_tokens = self.tokenizer.encode(text)
        return len(self.current_tokens["input_ids"][0]) 
    
    #Checks if the tokens have hit the threshold and need to compact which summarizes the previous messages
    def compact(self):
        if self.getCurrentTokens() < self.max_history_tokens:
            return
        
        recent_messages = 6
        summary_messages = self.messages[:-recent_messages]
        current_messages = self.messages[-recent_messages:]

        conversation_text = ""
        for message in summary_messages:
            conversation_text += message["role"] + ": " + message["content"] + "\n"
    
        summary_prompt = summary_prompt = f"""You are Aither, an AI Therapist specializing in Mental Health and Psychology.

        Summarize the following conversation between you and the user. Capture:
        - Key issues or concerns the user expressed
        - Emotional states mentioned
        - Important personal details shared
        - Any progress or insights reached

        Keep the summary concise (2-3 sentences).

        Conversation:
        {conversation_text}

        Summary:"""

        #call the model for compaction
        inputText = self.tokenizer.tokenizer(summary_prompt, return_tensors="pt")
        output = self.model.generate(inputText["input_ids"])
        response = self.tokenizer.tokenizer.decode(output[0])

        self.messages = [{"role": "system", "content": response}] + current_messages
            

    #Returns toString of the Message History
    def toString(self):
        result = ""
        for message in self.messages:
            role = message["role"]
            context = message["content"]
            result += role + ": " + context + "\n"
        return result