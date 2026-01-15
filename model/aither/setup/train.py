import torch
from aither.setup.config import AitherTrainingConfig as config
from aither.setup.tokenization import AitherTokenizer as tokenizer
from aither.setup.dataset import AitherDataset as dataset
from aither.setup.model import AitherModel as model

tok = tokenizer()
data = dataset("Amod/mental_health_counseling_conversations", tok)
training_data = data.get_dataset()
aither = model().model

optimizer = torch.optim.AdamW(aither.parameters(), lr = config.learningRate)

for epoch in range(config.epochs):
    for i,batch in enumerate(training_data):
        #Forward Pass
        outputs = aither(input_ids = batch, labels = batch)
        #Loss
        loss = outputs.loss
        #Backwards Pass
        optimizer.zero_grad() # clear the old gradient
        loss.backward() # calculate new gradients
        #Optimizer
        optimizer.step() # update the weights

        #Print every 100 batches
        if i % 100 == 0:
            print(f"Epoch {epoch}, Batch {i}, Loss: {loss.item()}")

# save the model
aither.save_pretrained("./aither_trained")


