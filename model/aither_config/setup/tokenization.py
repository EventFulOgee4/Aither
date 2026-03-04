from transformers import AutoTokenizer
from aither_config.setup.config import AitherTrainingConfig as aither_model

class AitherTokenizer():
    def __init__(self, model_name: str = aither_model.model, max_length: int = aither_model.contextWindow, add_special_tokens: bool = True, return_tensors: str = "pt", return_token_type_ids: bool = False, return_attention_mask: bool = True, return_overflowing_tokens: bool = False, return_length: bool = False, padding_side: str = aither_model.paddingSide, pad_token: str = aither_model.padToken):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.max_length = max_length
        self.add_special_tokens = add_special_tokens
        self.return_tensors = return_tensors
        self.return_token_type_ids = return_token_type_ids
        self.return_attention_mask = return_attention_mask
        self.return_overflowing_tokens = return_overflowing_tokens
        self.return_length = return_length
        self.tokenizer.padding_side = aither_model.paddingSide
        self.tokenizer.pad_token = aither_model.padToken

    def encode(self, text: str, max_length: int = aither_model.contextWindow):
        return self.tokenizer.encode(text, add_special_tokens=self.add_special_tokens, padding=True, 
        truncation=True, max_length=max_length, return_tensors=self.return_tensors, 
        return_token_type_ids=self.return_token_type_ids, return_attention_mask=self.return_attention_mask, 
        return_overflowing_tokens=self.return_overflowing_tokens, return_length=self.return_length)

    def decode(self, ids: list[int]):
        return self.tokenizer.decode(ids, skip_special_tokens=True)

if __name__ == "__main__":
    tok = AitherTokenizer()
    result = tok.encode("Hello, how are you?")
    print(result)