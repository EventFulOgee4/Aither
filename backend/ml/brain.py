from ml.emotion import AitherEmotionalTones
from ml.rag import AitherRAG
from ml.safety import AitherSafety
from ml.memory import AitherMemory

class AitherBrain:

    def __init__(self):
        self.rag = AitherRAG()
        self.safety = AitherSafety(None)
        self.tone = AitherEmotionalTones()

    def respond(self, message):

        safety_report = self.safety.detect_crisis(message)

        if safety_report.riskLevel.value >= 3:
            return "I am really concerned about what you shared. Would you consider reaching out to someone you trust or a professional?"

        context = self.rag.augment(message)

        prompt = f"""
        You are Aither Therapist AI.

        Context:
        {context}

        User message:
        {message}

        Respond in a {safety_report.toneChange} tone.
        """

        return prompt