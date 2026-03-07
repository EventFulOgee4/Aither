from ml.brain import AitherBrain
from ml.safety import AitherSafety


class BrainRagAdapter:
    """
    Makes AitherBrain look like a RAG model with .generate().
    """

    def __init__(self, brain: AitherBrain):
        self.brain = brain

    def generate(self, user_text: str, history=None) -> str:
        try:
            return self.brain.respond(user_text, history=history)
        except TypeError:
            return self.brain.respond(user_text)


def get_model():
    brain = AitherBrain()

    return {
        "rag": BrainRagAdapter(brain),
        "safety": AitherSafety(brain.memory),
    }