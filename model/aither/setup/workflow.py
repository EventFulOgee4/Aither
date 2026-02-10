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

    def prepareData(self):
        for datasetName in self.DATASETS:
            datasetType = self.DATASETS[datasetName]
            data = load_dataset(datasetName, split="train")

            for example in data:
                if datasetType == "conversations":
                    formatted = self.formatConversations(example)
                elif datasetType == "text":
                    formatted = self.formatText(example)
                elif datasetType == "qa":
                    formatted = self.formatQA(example)
                else:
                    formatted = None

                if formatted:
                    token = self.tokenizer.encode(formatted)
                    self.training_data.append(token)

            print(f"Loaded {datasetName} — Total samples: {len(self.training_data)}")

    def formatConversations(self, example):
        conversation = example["conversations"]
        result = ""
        for turn in conversation:
            result = result + "<|" + turn["role"] + "|>" + turn["content"]
        return result

    def formatText(self, example):
        text = example["text"]
        text = text.replace("<HUMAN>:", "<|user|>").replace("<ASSISTANT>:", "<|assistant|>")
        return text

    def formatQA(self, example):
        question = example.get("questionTitle", "") + " " + example.get("questionText", "")
        answer = example.get("answerText", "")
        return "<|user|>" + question.strip() + "<|assistant|>" + answer

    def setupModel(self):
        self.aither = model().model
        self.aither.to(self.device)
        self.aither.train()
        self.optimizer = torch.optim.AdamW(self.aither.parameters(), lr=config.learningRate, weight_decay=config.weightDecay)

    def train(self):
        for epoch in range(config.epochs):
            for i, batch in enumerate(self.training_data):
                batch = batch.to(self.device)

                attention_mask = (batch != self.tokenizer.tokenizer.pad_token_id).long().to(self.device)

                outputs = self.aither(input_ids=batch, attention_mask=attention_mask, labels=batch)
                loss = outputs.loss / config.gradientAccSteps
                loss.backward()

                if (i + 1) % config.gradientAccSteps == 0:
                    self.optimizer.step()
                    self.optimizer.zero_grad()

                if i % 100 == 0:
                    print(f"Epoch {epoch}, Batch {i}, Loss: {loss.item() * config.gradientAccSteps}")
