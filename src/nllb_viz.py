import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def visualize_attention(text, model_name="facebook/nllb-200-distilled-600M", output_path="attention_map.png"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, output_attentions=True)
    
    inputs = tokenizer(text, return_tensors="pt")
    outputs = model.generate(
        **inputs, 
        forced_bos_token_id=tokenizer.lang_code_to_id["eng_Latn"], 
        max_length=128,
        return_dict_in_generate=True,
        output_attentions=True
    )
    
    # Decoding generated tokens
    generated_tokens = tokenizer.batch_decode(outputs.sequences, skip_special_tokens=True)[0]
    src_tokens = tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
    tgt_tokens = tokenizer.convert_ids_to_tokens(outputs.sequences[0])

    # For simplicity, we'll plot the cross-attention of the last layer
    # Cross-attentions shape: (num_generated_tokens, num_decoder_layers, batch, num_heads, tgt_len, src_len)
    cross_attentions = outputs.cross_attentions # tuple of length num_generated_tokens
    
    # This is complex to visualize across all steps, so we take a snapshot of the last layer of the last step
    # or reconstruct. For NLLB/T5-style, attention maps are often averaged.
    
    last_step_attn = cross_attentions[-1] # tuple of layers
    last_layer_attn = last_step_attn[-1] # Tensor: (batch, num_heads, tgt_len, src_len)
    
    avg_attention = last_layer_attn[0].mean(dim=0).detach().cpu().numpy()

    plt.figure(figsize=(10, 8))
    sns.heatmap(avg_attention, xticklabels=src_tokens, yticklabels=tgt_tokens[-avg_attention.shape[0]:], cmap="viridis")
    plt.title(f"Cross-Attention Heatmap (Last Layer)")
    plt.xlabel("Source Tokens (Tamil)")
    plt.ylabel("Target Tokens (English)")
    plt.savefig(output_path)
    print(f"Attention visualization saved to {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?", help="Tamil text")
    parser.add_argument("--output", default="attention_map.png")
    args = parser.parse_args()
    visualize_attention(args.text, output_path=args.output)
