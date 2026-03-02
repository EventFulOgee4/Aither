from datasets import load_dataset
from aither.setup.tokenization import AitherTokenizer as tok

class AitherDataset():
    def __init__(self, dataset_name : str, tokenizer = tok()):
        self.tokenizer = tokenizer
        self.dataset_name = dataset_name
    
    def get_dataset(self):
        self.data = load_dataset(self.dataset_name)

        context_tokens = []

        for example in self.data:
            conversation = example["conversations"]
            result = ""
            for turn in conversation:
                result = result + "<|" + turn["role"] + "|>" + turn["content"]
            token = self.tokenizer.encode(result)
            context_tokens.append(token)

        return context_tokens
