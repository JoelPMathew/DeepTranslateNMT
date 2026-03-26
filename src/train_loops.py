import torch
import torch.nn as nn
import time
from .model import generate_square_subsequent_mask

def train_epoch(model, dataloader, optimizer, criterion, device, pad_id):
    model.train()
    losses = 0
    
    for src, tgt in dataloader:
        src = src.to(device)
        tgt = tgt.to(device)
        
        # tgt_input is all but last token, tgt_out is all but first token
        tgt_input = tgt[:-1, :]
        tgt_out = tgt[1:, :]
        
        src_mask = None
        tgt_mask = generate_square_subsequent_mask(tgt_input.size(0)).to(device)
        
        # Masks for padding tokens
        src_padding_mask = (src == pad_id).transpose(0, 1)
        tgt_padding_mask = (tgt_input == pad_id).transpose(0, 1)
        
        logits = model(src, tgt_input, src_mask, tgt_mask, src_padding_mask, tgt_padding_mask, src_padding_mask)
        
        optimizer.optimizer.zero_grad()
        loss = criterion(logits.reshape(-1, logits.shape[-1]), tgt_out.reshape(-1))
        loss.backward()
        optimizer.step()
        losses += loss.item()
        
    return losses / len(dataloader)

def validate(model, dataloader, criterion, device, pad_id):
    model.eval()
    losses = 0
    with torch.no_grad():
        for src, tgt in dataloader:
            src = src.to(device)
            tgt = tgt.to(device)
            
            tgt_input = tgt[:-1, :]
            tgt_out = tgt[1:, :]
            
            src_mask = None
            tgt_mask = generate_square_subsequent_mask(tgt_input.size(0)).to(device)
            
            src_padding_mask = (src == pad_id).transpose(0, 1)
            tgt_padding_mask = (tgt_input == pad_id).transpose(0, 1)
            
            logits = model(src, tgt_input, src_mask, tgt_mask, src_padding_mask, tgt_padding_mask, src_padding_mask)
            
            loss = criterion(logits.reshape(-1, logits.shape[-1]), tgt_out.reshape(-1))
            losses += loss.item()
            
    return losses / len(dataloader)
