import torch
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence

class NMTDataset(Dataset):
    def __init__(self, src_file, tgt_file, src_tokenizer, tgt_tokenizer):
        with open(src_file, 'r', encoding='utf-8') as f:
            self.src_lines = f.readlines()
        with open(tgt_file, 'r', encoding='utf-8') as f:
            self.tgt_lines = f.readlines()
        
        self.src_tokenizer = src_tokenizer
        self.tgt_tokenizer = tgt_tokenizer

    def __len__(self):
        return len(self.src_lines)

    def __getitem__(self, idx):
        src_text = self.src_lines[idx].strip()
        tgt_text = self.tgt_lines[idx].strip()
        
        # Subword regularization can be done here by passing enable_sampling=True if needed
        src_ids = [self.src_tokenizer.bos_id] + self.src_tokenizer.encode(src_text) + [self.src_tokenizer.eos_id]
        tgt_ids = [self.tgt_tokenizer.bos_id] + self.tgt_tokenizer.encode(tgt_text) + [self.tgt_tokenizer.eos_id]
        
        return torch.tensor(src_ids), torch.tensor(tgt_ids)

def collate_fn(batch, pad_id):
    src_batch, tgt_batch = zip(*batch)
    src_batch = pad_sequence(src_batch, padding_value=pad_id)
    tgt_batch = pad_sequence(tgt_batch, padding_value=pad_id)
    return src_batch, tgt_batch

class NoamOpt:
    "Optim wrapper that implements rate."
    def __init__(self, model_size, factor, warmup, optimizer):
        self.optimizer = optimizer
        self._step = 0
        self.warmup = warmup
        self.factor = factor
        self.model_size = model_size
        self._rate = 0
        
    def step(self):
        "Update parameters and rate"
        self._step += 1
        rate = self.rate()
        for p in self.optimizer.param_groups:
            p['lr'] = rate
        self._rate = rate
        self.optimizer.step()
        
    def rate(self, step = None):
        "Implement `lrate` above"
        if step is None:
            step = self._step
        return self.factor * \
            (self.model_size ** (-0.5) *
            min(step ** (-0.5), step * self.warmup ** (-1.5)))

class LabelSmoothing(torch.nn.Module):
    "Implement label smoothing."
    def __init__(self, size, padding_idx, smoothing=0.0):
        super(LabelSmoothing, self).__init__()
        self.criterion = torch.nn.KLDivLoss(reduction='sum')
        self.padding_idx = padding_idx
        self.confidence = 1.0 - smoothing
        self.smoothing = smoothing
        self.size = size
        self.true_dist = None
        
    def forward(self, x, target):
        assert x.size(1) == self.size
        true_dist = x.data.clone()
        true_dist.fill_(self.smoothing / (self.size - 2))
        true_dist.scatter_(1, target.data.unsqueeze(1), self.confidence)
        true_dist[:, self.padding_idx] = 0
        mask = torch.nonzero(target.data == self.padding_idx)
        if mask.dim() > 0:
            true_dist.index_fill_(0, mask.squeeze(), 0.0)
        self.true_dist = true_dist
        return self.criterion(x, true_dist.clone().detach())
