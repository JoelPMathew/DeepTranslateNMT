import sentencepiece as spm
import os

class NMTTokenizer:
    def __init__(self, model_prefix=None):
        self.sp = spm.SentencePieceProcessor()
        if model_prefix and os.path.exists(f"{model_prefix}.model"):
            self.sp.load(f"{model_prefix}.model")

    @staticmethod
    def train(input_file, model_prefix, vocab_size=8000, model_type='bpe', character_coverage=1.0):
        """
        Trains a SentencePiece model.
        """
        spm.SentencePieceTrainer.train(
            input=input_file,
            model_prefix=model_prefix,
            vocab_size=vocab_size,
            model_type=model_type,
            character_coverage=character_coverage,
            pad_id=0,
            unk_id=1,
            bos_id=2,
            eos_id=3,
            pad_piece='[PAD]',
            unk_piece='[UNK]',
            bos_piece='[BOS]',
            eos_piece='[EOS]'
        )

    def encode(self, text, enable_sampling=False, alpha=0.1, nbest_size=-1):
        """
        Encodes text to subword IDs. 
        Subword regularization (sampling) can be enabled during training.
        """
        if enable_sampling:
            return self.sp.encode_with_sampling(text, nbest_size=nbest_size, alpha=alpha)
        return self.sp.encode_as_ids(text)

    def decode(self, ids):
        """
        Decodes subword IDs back to text.
        """
        return self.sp.decode_ids(ids)

    def get_vocab_size(self):
        return self.sp.get_piece_size()

    @property
    def pad_id(self): return self.sp.pad_id()
    @property
    def bos_id(self): return self.sp.bos_id()
    @property
    def eos_id(self): return self.sp.eos_id()
    @property
    def unk_id(self): return self.sp.unk_id()
