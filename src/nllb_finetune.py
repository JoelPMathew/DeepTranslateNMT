import os
import torch
import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForSeq2SeqLM, 
    DataCollatorForSeq2Seq, 
    Seq2SeqTrainingArguments, 
    Seq2SeqTrainer,
    EarlyStoppingCallback
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def finetune(csv_path, output_dir, model_name="facebook/nllb-200-distilled-600M", epochs=3, batch_size=16, use_8bit=False, max_steps=-1, use_lora=True):
    # 1. Load Dataset
    df = pd.read_csv(csv_path)
    dataset = Dataset.from_pandas(df)
    
    # Split dataset
    dataset = dataset.train_test_split(test_size=0.1)
    
    # 2. Tokenizer & Model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    model_kwargs = {}
    if use_8bit:
        # Requires bitsandbytes and accelerate
        model_kwargs["load_in_8bit"] = True
        model_kwargs["device_map"] = "auto"
    
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, **model_kwargs)
    
    src_lang = "tam_Taml"
    tgt_lang = "eng_Latn"
    tokenizer.src_lang = src_lang
    tokenizer.tgt_lang = tgt_lang

    # Style Tokens
    style_tokens = ["<style=formal>", "<style=casual>", "<style=literary>", "<style=spoken>", "<style=chennai>", "<style=madurai>"]
    tokenizer.add_special_tokens({"additional_special_tokens": style_tokens})
    model.resize_token_embeddings(len(tokenizer))

    if use_lora:
        logger.info("Configuring LoRA...")
        if use_8bit:
            model = prepare_model_for_kbit_training(model)
        
        peft_config = LoraConfig(
            task_type=TaskType.SEQ_2_SEQ_LM,
            inference_mode=False,
            r=8,
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_proj", "k_proj", "v_proj", "out_proj"] 
        )
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()
        
    # Disable cache for training (required for gradient checkpointing/PEFT)
    model.config.use_cache = False

    def preprocess_function(examples):
        # We are fine-tuning for English -> Styled Tamil
        inputs = examples["english"]
        targets = examples["tamil"]
        styles = examples.get("style", ["formal"] * len(inputs))
        
        processed_inputs = []
        for text, style in zip(inputs, styles):
            # Prepend style token to English source
            style_token = f"<style={style}>" if f"<style={style}>" in style_tokens else "<style=formal>"
            processed_inputs.append(f"{style_token} {text}")

        model_inputs = tokenizer(processed_inputs, max_length=128, truncation=True, padding="max_length")

        with tokenizer.as_target_tokenizer():
            labels = tokenizer(targets, max_length=128, truncation=True, padding="max_length")

        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    tokenized_datasets = dataset.map(preprocess_function, batched=True)
    
    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    # 3. Training Arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        eval_strategy="no", # Disable for demo to avoid Seq2Seq/PEFT generation conflicts
        save_strategy="no",
        learning_rate=2e-5,
        per_device_train_batch_size=1, # Reduce to save RAM
        gradient_accumulation_steps=batch_size, # Accumulate to match original effective batch size
        weight_decay=0.01,
        num_train_epochs=epochs if max_steps <= 0 else 1,
        max_steps=max_steps,
        report_to="none"
    )

    # 4. Trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    trainer.train()
    
    # Save the adapter if using LoRA, or the full model if not
    if use_lora:
        model.save_pretrained(os.path.join(output_dir, "best_model"), safe_serialization=False)
    else:
        trainer.save_model(os.path.join(output_dir, "best_model"))
    
    tokenizer.save_pretrained(os.path.join(output_dir, "best_model"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to CSV with 'tamil' and 'english' columns")
    parser.add_argument("--output", default="./nllb_finetuned", help="Output directory")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--eight_bit", action="store_true", help="Use 8-bit quantization")
    parser.add_argument("--lora", action="store_true", default=True, help="Use LoRA (default True)")
    parser.add_argument("--no_lora", action="store_false", dest="lora", help="Disable LoRA")
    parser.add_argument("--max_steps", type=int, default=-1, help="Force a specific number of steps (for demo)")
    args = parser.parse_args()
    
    finetune(args.csv, args.output, epochs=args.epochs, batch_size=args.batch_size, use_8bit=args.eight_bit, max_steps=args.max_steps, use_lora=args.lora)
