import torch
from .model import generate_square_subsequent_mask

def greedy_decode(model, src, src_mask, max_len, start_symbol, device):
    src = src.to(device)
    src_mask = src_mask.to(device)
    
    memory = model.encode(src, src_mask)
    ys = torch.ones(1, 1).fill_(start_symbol).type(torch.long).to(device)
    
    for i in range(max_len - 1):
        memory = memory.to(device)
        tgt_mask = generate_square_subsequent_mask(ys.size(0)).type(torch.bool).to(device)
        out = model.decode(ys, memory, tgt_mask)
        out = out.transpose(0, 1)
        prob = model.generator(out[:, -1])
        _, next_word = torch.max(prob, dim=1)
        next_word = next_word.item()
        
        ys = torch.cat([ys, torch.ones(1, 1).type_as(src.data).fill_(next_word)], dim=0)
        if next_word == 3: # EOS token ID is 3 as defined in tokenizer.py
            break
    return ys

def translate_sentence(model, sentence, src_tokenizer, tgt_tokenizer, device, max_len=50):
    model.eval()
    src_ids = [src_tokenizer.bos_id] + src_tokenizer.encode(sentence) + [src_tokenizer.eos_id]
    src = torch.tensor(src_ids).unsqueeze(1)
    num_tokens = src.shape[0]
    src_mask = (torch.zeros(num_tokens, num_tokens)).type(torch.bool)
    
    tgt_tokens = greedy_decode(model, src, src_mask, max_len=max_len, start_symbol=tgt_tokenizer.bos_id, device=device).flatten()
    return tgt_tokenizer.decode(tgt_tokens.tolist())
