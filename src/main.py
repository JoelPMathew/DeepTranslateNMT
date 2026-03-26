import click
import os
import torch
import torch.nn as nn
from .data_utils import clean_parallel_data
from .tokenizer import NMTTokenizer
from .model import TransformerModel
from .train_utils import NMTDataset, collate_fn, NoamOpt, LabelSmoothing
from .train_loops import train_epoch, validate
from .translate import translate_sentence
from .evaluate import compute_metrics
from functools import partial

@click.group()
def cli():
    pass

@cli.command()
@click.option('--src-train', required=True)
@click.option('--tgt-train', required=True)
@click.option('--src-val', required=True)
@click.option('--tgt-val', required=True)
@click.option('--output-dir', default='models/')
@click.option('--vocab-size', default=8000)
@click.option('--epochs', default=20)
@click.option('--batch-size', default=32)
@click.option('--d-model', default=512)
@click.option('--nhead', default=8)
@click.option('--num-layers', default=6)
def train(src_train, tgt_train, src_val, tgt_val, output_dir, vocab_size, epochs, batch_size, d_model, nhead, num_layers):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Clean/Normalize is assumed to be done or part of pipeline
    # For simplicity here we assume files are cleaned or we clean them to a temp path
    
    # Train tokenizers
    print("Training tokenizers...")
    NMTTokenizer.train(src_train, os.path.join(output_dir, 'src_spm'), vocab_size=vocab_size)
    NMTTokenizer.train(tgt_train, os.path.join(output_dir, 'tgt_spm'), vocab_size=vocab_size)
    
    src_tokenizer = NMTTokenizer(os.path.join(output_dir, 'src_spm'))
    tgt_tokenizer = NMTTokenizer(os.path.join(output_dir, 'tgt_spm'))
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    model = TransformerModel(
        src_vocab_size=src_tokenizer.get_vocab_size(),
        tgt_vocab_size=tgt_tokenizer.get_vocab_size(),
        d_model=d_model,
        nhead=nhead,
        num_encoder_layers=num_layers,
        num_decoder_layers=num_layers
    ).to(device)
    
    criterion = LabelSmoothing(size=tgt_tokenizer.get_vocab_size(), padding_idx=tgt_tokenizer.pad_id, smoothing=0.1)
    optimizer = NoamOpt(model_size=d_model, factor=1, warmup=4000, 
                        optimizer=torch.optim.Adam(model.parameters(), lr=0, betas=(0.9, 0.98), eps=1e-9))
    
    train_dataset = NMTDataset(src_train, tgt_train, src_tokenizer, tgt_tokenizer)
    val_dataset = NMTDataset(src_val, tgt_val, src_tokenizer, tgt_tokenizer)
    
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, 
                                               shuffle=True, collate_fn=partial(collate_fn, pad_id=src_tokenizer.pad_id))
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=batch_size, 
                                             shuffle=False, collate_fn=partial(collate_fn, pad_id=src_tokenizer.pad_id))
    
    best_val_loss = float('inf')
    for epoch in range(epochs):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device, src_tokenizer.pad_id)
        val_loss = validate(model, val_loader, criterion, device, src_tokenizer.pad_id)
        print(f"Epoch {epoch+1}: Train Loss {train_loss:.4f}, Val Loss {val_loss:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), os.path.join(output_dir, 'best_model.pt'))
            print("Saved best model.")

@cli.command()
@click.option('--model-path', required=True)
@click.option('--src-spm', required=True)
@click.option('--tgt-spm', required=True)
@click.option('--d-model', default=512)
@click.option('--nhead', default=8)
@click.option('--num-layers', default=6)
@click.argument('text')
def translate(model_path, src_spm, tgt_spm, d_model, nhead, num_layers, text):
    src_tokenizer = NMTTokenizer(src_spm)
    tgt_tokenizer = NMTTokenizer(tgt_spm)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = TransformerModel(
        src_vocab_size=src_tokenizer.get_vocab_size(),
        tgt_vocab_size=tgt_tokenizer.get_vocab_size(),
        d_model=d_model,
        nhead=nhead,
        num_encoder_layers=num_layers,
        num_decoder_layers=num_layers
    ).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    
    translation = translate_sentence(model, text, src_tokenizer, tgt_tokenizer, device)
    print(f"Translation: {translation}")

if __name__ == "__main__":
    cli()
