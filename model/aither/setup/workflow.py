import os
import torch
from datasets import load_dataset
from aither.setup.config import AitherTrainingConfig as config
from aither.setup.tokenization import AitherTokenizer as tokenizer
from aither.setup.model import AitherModel as model


class AitherWorkflow():
    DATASETS = {
        "Amod/mental_health_counseling_conversations": "conversations",
        "heliosbrahma/mental_health_chatbot_dataset": "text",
        "mpingale/mental-health-chat-dataset": "qa",
        "nbertagnolli/counsel-chat": "qa"
    }

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = tokenizer()
        self.training_data = []
        self.aither = None
        self.optimizer = None
        self.savePath = os.path.join(os.path.dirname(__file__), "../../aither_trained")
