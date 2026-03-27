# ml/loader.py
#
# Previously this called AitherBrain() directly, which caused the model
# to be loaded TWICE (once here, once in brain.py's own import) — doubling
# RAM usage and triggering os error 1455 on low-RAM machines.
#
# Fix: use a module-level singleton so the brain is only ever loaded once.

from ml.safety import AitherSafety

_brain_instance = None


def _get_brain():
    """Load AitherBrain once and reuse it forever."""
    global _brain_instance
    if _brain_instance is None:
        from ml.brain import AitherBrain
        _brain_instance = AitherBrain()
    return _brain_instance


class BrainRagAdapter:
    """
    Makes AitherBrain look like a RAG model with .generate()
    so views.py can call rag.generate(text, history=history).
    """

    def __init__(self, brain):
        self.brain = brain

    def generate(self, user_text: str, history=None) -> str:
        try:
            return self.brain.respond(user_text, history=history)
        except TypeError:
            return self.brain.respond(user_text)
        except Exception as e:
            print("⚠️ BrainRagAdapter.generate failed:", repr(e))
            return "I'm here with you. Tell me a little more."


def get_model():
    brain = _get_brain()

    return {
        "rag": BrainRagAdapter(brain),
        "safety": AitherSafety(brain.memory),
    }