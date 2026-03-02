import torch
from transformers import AutoModelForCausalLM
from peft import LoraConfig, get_peft_model
from aither.setup.config import AitherTrainingConfig as config


def getDevice():
    """Auto-detect best available device: MPS (Apple Silicon) > CUDA > CPU"""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


class AitherModel():
    def __init__(self):
        dtype = torch.float16 if config.useFp16 else torch.float32

        self.model = AutoModelForCausalLM.from_pretrained(
            config.model,
            torch_dtype=dtype,
            low_cpu_mem_usage=True,     # Loads weights sequentially to reduce peak memory
            trust_remote_code=True
        )

        if config.gradientCheckpointing:
            self.model.gradient_checkpointing_enable()
            self.model.enable_input_require_grads()  # Required for gradient checkpointing + LoRA

        if config.useLora:
            self.loraConfig = LoraConfig(
                r = config.lora_rank,
                lora_alpha = config.lora_scale,
                lora_dropout = config.lora_drop,
                target_modules = config.target_modules,
                task_type = "CAUSAL_LM"
            )
            self.model = get_peft_model(self.model, self.loraConfig)
            self.model.print_trainable_parameters()

    def generate(self, input_ids, max_new_tokens=100):
        return self.model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            pad_token_id=self.model.config.eos_token_id
        )
