import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import os

def export_to_onnx(model_name="facebook/nllb-200-distilled-600M", output_path="models/nllb_onnx"):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    dummy_input_text = "வணக்கம்"
    inputs = tokenizer(dummy_input_text, return_tensors="pt")
    
    onnx_path = os.path.join(output_path, "model.onnx")
    
    # Using torch.onnx.export for Seq2Seq is non-trivial due to the decoder loop.
    # Usually Optimum is preferred. Here's a basic export of the encoder-decoder pair.
    
    logger = print
    logger(f"Exporting {model_name} to ONNX...")
    
    # We export the whole model as a single block for simplicity in this template
    # although production often splits encoder and decoder.
    torch.onnx.export(
        model,
        (inputs["input_ids"], inputs["attention_mask"], inputs["input_ids"]), # Dummy inputs
        onnx_path,
        input_names=["input_ids", "attention_mask", "decoder_input_ids"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "sequence"},
            "attention_mask": {0: "batch", 1: "sequence"},
            "decoder_input_ids": {0: "batch", 1: "sequence"},
            "logits": {0: "batch", 1: "sequence"},
        },
        opset_version=14
    )
    
    logger(f"Model exported to {onnx_path}")

if __name__ == "__main__":
    export_to_onnx()
