from transformers import AutoModelForCausalLM  
from peft import LoraConfig, get_peft_model
from aither.setup.config import AitherTrainingConfig as model_name


class AitherModel():
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained(model_name.model)

        if model_name.useLora: #configured from config.py
            self.loraConfig = LoraConfig(
                r = model_name.lora_rank,
                lora_alpha = model_name.lora_scale,
                lora_dropout = model_name.lora_drop,
                target_modules = model_name.target_modules
            )
            self.model = get_peft_model(self.model, self.loraConfig)









