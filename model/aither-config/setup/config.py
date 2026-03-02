from dataclasses import dataclass, field

@dataclass
class AitherTrainingConfig:
    # Base Model
    model : str = "microsoft/phi-2"
    contextWindow : int = 2048

    # Training Hyperparameters
    batches : int = 1               # Keep at 1 for 8GB memory
    learningRate : float = 2e-5
    epochs : int = 3
    gradientAccSteps : int = 8      # Effective batch size = batches * gradientAccSteps = 8
    weightDecay : float = 0.05
    warmupSteps : int = 100
    maxSamples : int = 15000        # Cap total training samples to fit in memory

    # LoRA — Low-Rank Adaptation (parameter-efficient fine-tuning)
    useLora : bool = True
    lora_rank : int = 16
    lora_scale : float = 32.0      # alpha = 2 * rank
    lora_drop : float = 0.06
    target_modules : list[str] = field(default_factory=lambda: ["q_proj", "k_proj", "v_proj", "dense"])

    # Compression — critical for M2 8GB
    useFp16 : bool = True           # Half precision: 2.7B params → ~5.4GB instead of ~10.8GB
    gradientCheckpointing : bool = True  # Saves ~60% activation memory by recomputing during backward pass

    # Tokenizer
    paddingSide : str = "right"
    padToken : str = "<|endoftext|>"

    # Logging
    logEvery : int = 50






    