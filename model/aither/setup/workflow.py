import os
import torch
from datasets import load_dataset
from aither.setup.config import AitherTrainingConfig as config
from aither.setup.tokenization import AitherTokenizer as tokenizer
from aither.setup.model import AitherModel as model, getDevice


class AitherWorkflow():
    # ── Dataset Registry ──────────────────────────────────────────────
    # Each entry: HuggingFace ID → { type: format handler, domain: category }
    #
    # Domains:  mental_health | psychology | medicine
    # Types:    conversations | text | qa | medical | instruction

    DATASETS = {
        # ── Mental Health ─────────────────────────────────────────────
        "Amod/mental_health_counseling_conversations": {
            "type": "conversations",
            "domain": "mental_health"
        },
        "heliosbrahma/mental_health_chatbot_dataset": {
            "type": "text",
            "domain": "mental_health"
        },
        "mpingale/mental-health-chat-dataset": {
            "type": "qa",
            "domain": "mental_health"
        },
        "nbertagnolli/counsel-chat": {
            "type": "qa",
            "domain": "mental_health"
        },

        # ── Medicine ──────────────────────────────────────────────────
        "ruslanmv/ai-medical-chatbot": {
            "type": "medical",
            "domain": "medicine"
        },
        "lavita/ChatDoctor-HealthCareMagic-100k": {
            "type": "instruction",
            "domain": "medicine"
        },

        # ── Psychology ────────────────────────────────────────────────
        "alexandreteles/mental-health-conversational-data": {
            "type": "conversations",
            "domain": "psychology"
        },
    }

    def __init__(self):
        self.device = getDevice()
        self.tokenizer = tokenizer()
        self.training_data = []
        self.aither = None
        self.optimizer = None
        self.savePath = os.path.join(os.path.dirname(__file__), "../../aither_trained")

        print(f"Device: {self.device}")
        if self.device.type == "mps":
            print("Apple Silicon detected — using fp16 + LoRA + gradient checkpointing for 8GB memory")

    # ── Data Preparation ──────────────────────────────────────────────

    def prepareData(self):
        total = 0
        for datasetName, info in self.DATASETS.items():
            datasetType = info["type"]
            domain = info["domain"]

            print(f"\nLoading [{domain}] {datasetName}...")
            try:
                data = load_dataset(datasetName, split="train")
            except Exception as e:
                print(f"  Skipping {datasetName}: {e}")
                continue

            count = 0
            for example in data:
                if total >= config.maxSamples:
                    print(f"  Reached max samples limit ({config.maxSamples})")
                    break

                formatted = self._formatExample(example, datasetType)
                if formatted:
                    token = self.tokenizer.encode(formatted)
                    self.training_data.append(token)
                    count += 1
                    total += 1

            print(f"  Added {count} samples from {datasetName} (total: {total})")

            if total >= config.maxSamples:
                break

        print(f"\nTotal training samples: {len(self.training_data)}")

    def _formatExample(self, example, datasetType):
        try:
            if datasetType == "conversations":
                return self.formatConversations(example)
            elif datasetType == "text":
                return self.formatText(example)
            elif datasetType == "qa":
                return self.formatQA(example)
            elif datasetType == "medical":
                return self.formatMedical(example)
            elif datasetType == "instruction":
                return self.formatInstruction(example)
        except (KeyError, TypeError):
            return None
        return None

    # ── Format Handlers ───────────────────────────────────────────────

    def formatConversations(self, example):
        """Format: [{"role": "...", "content": "..."}]"""
        conversation = example["conversations"]
        result = ""
        for turn in conversation:
            result = result + "<|" + turn["role"] + "|>" + turn["content"]
        return result

    def formatText(self, example):
        """Format: single text with <HUMAN>:/<ASSISTANT>: tags"""
        text = example["text"]
        text = text.replace("<HUMAN>:", "<|user|>").replace("<ASSISTANT>:", "<|assistant|>")
        return text

    def formatQA(self, example):
        """Format: questionTitle + questionText → answerText"""
        question = example.get("questionTitle", "") + " " + example.get("questionText", "")
        answer = example.get("answerText", "")
        if not answer.strip():
            return None
        return "<|user|>" + question.strip() + "<|assistant|>" + answer

    def formatMedical(self, example):
        """Format: Description + Patient → Doctor response"""
        context = example.get("Description", "")
        patient = example.get("Patient", "")
        doctor = example.get("Doctor", "")
        if not doctor.strip():
            return None
        prompt = f"{context} {patient}".strip() if context else patient
        return f"<|user|>{prompt}<|assistant|>{doctor}"

    def formatInstruction(self, example):
        """Format: instruction + input → output"""
        instruction = example.get("instruction", "")
        inp = example.get("input", "")
        output = example.get("output", "")
        if not output.strip():
            return None
        prompt = f"{instruction} {inp}".strip() if inp else instruction
        return f"<|user|>{prompt}<|assistant|>{output}"

    # ── Model Setup ───────────────────────────────────────────────────

    def setupModel(self):
        self.aither = model().model
        self.aither.to(self.device)
        self.aither.train()
        self.optimizer = torch.optim.AdamW(
            self.aither.parameters(),
            lr=config.learningRate,
            weight_decay=config.weightDecay
        )

    # ── Training Loop ─────────────────────────────────────────────────

    def train(self):
        totalSteps = len(self.training_data) * config.epochs
        step = 0

        for epoch in range(config.epochs):
            epochLoss = 0.0
            batchCount = 0

            for i, batch in enumerate(self.training_data):
                batch = batch.to(self.device)
                attention_mask = (batch != self.tokenizer.tokenizer.pad_token_id).long().to(self.device)

                outputs = self.aither(input_ids=batch, attention_mask=attention_mask, labels=batch)
                loss = outputs.loss / config.gradientAccSteps
                loss.backward()

                if (i + 1) % config.gradientAccSteps == 0:
                    self.optimizer.step()
                    self.optimizer.zero_grad()

                realLoss = loss.item() * config.gradientAccSteps
                epochLoss += realLoss
                batchCount += 1
                step += 1

                if i % config.logEvery == 0:
                    avgLoss = epochLoss / batchCount if batchCount > 0 else realLoss
                    progress = (step / totalSteps) * 100
                    print(f"  Epoch {epoch+1}/{config.epochs} | Batch {i}/{len(self.training_data)} | Loss: {realLoss:.4f} | Avg: {avgLoss:.4f} | Progress: {progress:.1f}%")

                # Clear MPS cache periodically to prevent OOM
                if self.device.type == "mps" and i % 500 == 0:
                    torch.mps.empty_cache()

            avgEpochLoss = epochLoss / batchCount if batchCount > 0 else 0
            print(f"\n  Epoch {epoch+1} complete — Avg Loss: {avgEpochLoss:.4f}\n")

    # ── Save ──────────────────────────────────────────────────────────

    def save(self):
        os.makedirs(self.savePath, exist_ok=True)
        self.aither.save_pretrained(self.savePath)
        self.tokenizer.tokenizer.save_pretrained(self.savePath)
        print(f"Model saved to {self.savePath}")

    # ── Run Full Pipeline ─────────────────────────────────────────────

    def run(self):
        print("=" * 60)
        print("  Aither Training Pipeline")
        print(f"  Model: {config.model}")
        print(f"  Compression: fp16={config.useFp16}, LoRA={config.useLora}, GradCheckpoint={config.gradientCheckpointing}")
        print(f"  LoRA rank={config.lora_rank}, alpha={config.lora_scale}")
        print(f"  Batch={config.batches}, GradAcc={config.gradientAccSteps}, LR={config.learningRate}")
        print(f"  Max samples: {config.maxSamples}")
        print("=" * 60)

        print("\n[1/4] Preparing data...")
        self.prepareData()

        print("\n[2/4] Setting up model...")
        self.setupModel()

        print("\n[3/4] Training...")
        self.train()

        print("\n[4/4] Saving...")
        self.save()

        print("\nTraining complete.")
        print(f"To compress for inference, run: python -m aither.setup.compress")


if __name__ == "__main__":
    pipeline = AitherWorkflow()
    pipeline.run()
