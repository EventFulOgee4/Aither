from dataclasses import dataclass

@dataclass
class AitherTrainingConfig:
    model : str = "microsoft/phi-2"
    contextWindow : int = 2048
    batches : int = 4
    learningRate : float = 1e-4
    epochs : int = 3
    gradientAccSteps : int = 2
    weightDecay : float = 0.05
    useLora : bool = True #if gpu memory is sufficent set to false
    lora_rank : int = 16
    lora_scale : float = lora_rank * 2
    lora_drop : float = 0.06
    target_modules : list[str] = ["q_proj", "k_proj", "v_proj", "dense"]
    paddingSide : str = "right"
    padToken : str = "<|endoftext|>"










    