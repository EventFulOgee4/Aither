# backend/ml/loader.py
from functools import lru_cache


class BrainRagAdapter:
    """
    Adapts AitherBrain to the interface views.py expects:
      - rag.generate(text, history=...) -> reply
    """
    def __init__(self, brain):
        self.brain = brain

    def generate(self, user_text: str, history=None) -> str:
        # If we have history, prepend a short transcript so the model varies more.
        # (Keeps it small so DialoGPT doesn't get overwhelmed.)
        if history:
            # history items look like: {"sender": "user"/"ai", "message": "..."}
            transcript_lines = []
            for h in history[-8:]:  # last 8 messages max
                sender = "User" if h.get("sender") == "user" else "Aither"
                msg = (h.get("message") or "").strip()
                if msg:
                    transcript_lines.append(f"{sender}: {msg}")

            transcript = "\n".join(transcript_lines).strip()
            if transcript:
                user_text = f"{transcript}\nUser: {user_text}"

        return self.brain.respond(user_text)


@lru_cache(maxsize=1)
def get_model():
    """
    Load everything once per Django process.
    Returns a dict with keys expected by views.py: {"rag": ..., "safety": ...}
    """
    from ml.brain import AitherBrain

    brain = AitherBrain()

    # Expose an adapter that has .generate()
    rag = BrainRagAdapter(brain)

    # Optional: expose safety module if views.py wants it
    safety = getattr(brain, "safety", None)

    print("✅ loader.get_model(): using AitherBrain + BrainRagAdapter")
    return {"rag": rag, "safety": safety}