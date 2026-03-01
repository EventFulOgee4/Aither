import os
import subprocess
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from aither.setup.config import AitherTrainingConfig as config


class AitherCompress():
    """
    Post-training compression for deploying Aither on Apple Silicon (M2 8GB).

    Pipeline:
        1. Merge LoRA adapters back into the base model
        2. Quantize to 4-bit using MLX (Apple Silicon native)
        3. Result: ~1.5GB model that runs fast on M2

    Usage:
        python -m aither.setup.compress
    """

    def __init__(self, loraPath=None, outputPath=None):
        self.loraPath = loraPath or os.path.join(os.path.dirname(__file__), "../../aither_trained")
        self.mergedPath = os.path.join(os.path.dirname(__file__), "../../aither_merged")
        self.quantizedPath = outputPath or os.path.join(os.path.dirname(__file__), "../../aither_quantized")

    # ── Step 1: Merge LoRA ────────────────────────────────────────────

    def mergeLoRA(self):
        """Merge LoRA adapter weights back into the base model."""
        print(f"Loading base model: {config.model}")
        base = AutoModelForCausalLM.from_pretrained(
            config.model,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )
        tokenizer = AutoTokenizer.from_pretrained(config.model, trust_remote_code=True)

        print(f"Loading LoRA adapters from: {self.loraPath}")
        model = PeftModel.from_pretrained(base, self.loraPath)

        print("Merging LoRA weights into base model...")
        merged = model.merge_and_unload()

        os.makedirs(self.mergedPath, exist_ok=True)
        merged.save_pretrained(self.mergedPath)
        tokenizer.save_pretrained(self.mergedPath)
        print(f"Merged model saved to: {self.mergedPath}")

        # Free memory
        del merged, model, base
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()

    # ── Step 2: Quantize with MLX ─────────────────────────────────────

    def quantizeMLX(self, bits=4):
        """
        Quantize the merged model to 4-bit using MLX.
        Requires: pip install mlx-lm

        Phi-2 (2.7B) at 4-bit ≈ 1.5GB — fits easily in 8GB memory.
        """
        print(f"Quantizing to {bits}-bit with MLX...")
        print(f"  Input:  {self.mergedPath}")
        print(f"  Output: {self.quantizedPath}")

        try:
            result = subprocess.run(
                [
                    "python", "-m", "mlx_lm.convert",
                    "--hf-path", self.mergedPath,
                    "--mlx-path", self.quantizedPath,
                    "-q",
                    "--q-bits", str(bits)
                ],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"Quantized model saved to: {self.quantizedPath}")
                self.estimateSize()
            else:
                print(f"MLX quantization failed: {result.stderr}")
                print("Make sure mlx-lm is installed: pip install mlx-lm")
        except FileNotFoundError:
            print("mlx-lm not found. Install it with: pip install mlx-lm")

    # ── Size Estimation ───────────────────────────────────────────────

    def estimateSize(self):
        """Print model size estimates."""
        paramCount = 2.7  # Phi-2 billions

        print("\n  Model Size Estimates:")
        print(f"  {'Format':<20} {'Size':>10}")
        print(f"  {'-'*30}")
        print(f"  {'fp32 (original)':<20} {paramCount * 4:>8.1f} GB")
        print(f"  {'fp16 (training)':<20} {paramCount * 2:>8.1f} GB")
        print(f"  {'8-bit quantized':<20} {paramCount * 1:>8.1f} GB")
        print(f"  {'4-bit quantized':<20} {paramCount * 0.5:>8.1f} GB")

        # Check actual size on disk
        for path, label in [(self.mergedPath, "Merged"), (self.quantizedPath, "Quantized")]:
            if os.path.exists(path):
                size = sum(
                    os.path.getsize(os.path.join(dp, f))
                    for dp, _, fns in os.walk(path) for f in fns
                )
                print(f"\n  {label} model on disk: {size / (1024**3):.2f} GB")

    # ── Full Pipeline ─────────────────────────────────────────────────

    def run(self):
        print("=" * 60)
        print("  Aither Post-Training Compression")
        print("=" * 60)

        print("\n[1/2] Merging LoRA adapters...")
        self.mergeLoRA()

        print("\n[2/2] Quantizing to 4-bit (MLX)...")
        self.quantizeMLX(bits=4)

        print("\n" + "=" * 60)
        print("  Compression complete!")
        print(f"  Quantized model: {self.quantizedPath}")
        print()
        print("  To use for inference with MLX:")
        print("    from mlx_lm import load, generate")
        print(f'    model, tokenizer = load("{self.quantizedPath}")')
        print('    response = generate(model, tokenizer, prompt="Hello", max_tokens=200)')
        print("=" * 60)


if __name__ == "__main__":
    compressor = AitherCompress()
    compressor.run()
