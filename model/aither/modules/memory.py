from aither.setup.model import AitherModel as assistant
from aither.setup.tokenization import AitherTokenizer as tok


class AitherMemory():
    def __init__(self, assistant.model):
        self.messages = # obtain from the database
        self.max_history_tokens = # compaction