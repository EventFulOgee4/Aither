import os
import torch
from aither.setup.config import AitherTrainingConfig as config
from aither.setup.tokenization import AitherTokenizer as tokenizer
from aither.setup.dataset import AitherDataset as dataset
from aither.setup.model import AitherModel as model

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

tok = tokenizer()
data = dataset("Amod/mental_health_counseling_conversations", tok)
training_data = data.get_dataset()
aither = model().model
aither.to(device)
aither.train()

optimizer = torch.optim.AdamW(aither.parameters(), lr=config.learningRate, weight_decay=config.weightDecay)

for epoch in range(config.epochs):
    for i, batch in enumerate(training_data):
        batch = batch.to(device)

        attention_mask = (batch != tok.tokenizer.pad_token_id).long().to(device)

        #Forward Pass
        outputs = aither(input_ids=batch, attention_mask=attention_mask, labels=batch)
        #Loss
        loss = outputs.loss / config.gradientAccSteps
        #Backwards Pass
        loss.backward()

        #Optimizer
        if (i + 1) % config.gradientAccSteps == 0:
            optimizer.step()
            optimizer.zero_grad()

        #Print every 100 batches
        if i % 100 == 0:
            print(f"Epoch {epoch}, Batch {i}, Loss: {loss.item() * config.gradientAccSteps}")

savePath = os.path.join(os.path.dirname(__file__), "../../aither_trained")

#Save the model
aither.save_pretrained(savePath)
tok.tokenizer.save_pretrained(savePath)
