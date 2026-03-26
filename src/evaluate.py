import sacrebleu

def compute_metrics(hypotheses, references):
    """
    Computes BLEU and chrF scores.
    hypotheses: List of strings
    references: List of list of strings (sacrebleu format)
    """
    bleu = sacrebleu.corpus_bleu(hypotheses, references)
    chrf = sacrebleu.corpus_chrf(hypotheses, references)
    
    return {
        'bleu': bleu.score,
        'chrf': chrf.score
    }
