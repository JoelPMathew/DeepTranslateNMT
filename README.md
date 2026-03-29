#  DeepTranslateNMT (NLLB-200)

A production-ready Neural Machine Translation system that prioritizes local execution, absolute control, and cultural intelligence.

## 🌟 Novelty of DeepTranslate
DeepTranslate is not just another translation tool reliant on cloud-based APIs like Google. It is a **fully self-contained Neural Machine Translation system** where every component—from vocabulary construction to semantic modeling—is integrated into a single, cohesive architecture.

Unlike "shortcut" services that piggyback on existing platforms, DeepTranslate provides complete control over the entire pipeline:
- **Architecture**: A fundamentally sequence-to-sequence encoder-decoder system enhanced with **Multi-Head Attention**, allowing the model to focus on appropriate context and "recollect" content across complex sentences.
- **Semantic Understanding**: The system doesn't simply replace words. It studies sentence pairs to capture underlying meaning (semantics), even when source and target grammars differ significantly.
- **Local & Private**: All training (via cross-entropy loss) and inference happen locally, making the tool a playground for research, learning, and privacy-first translation.
- **Democratizing NMT**: It demonstrates that high-quality translation doesn't require expensive APIs—only open datasets and a sound neural architecture.

## 🛠️ Methodology
The development of DeepTranslate followed a rigorous, modular approach to ensure accuracy and cultural relevance.

### 1. Data Engineering & Preprocessing
- **Source Selection**: Utilized high-quality parallel corpora cleaned of noise and mismatches.
- **Style Tagging**: Implemented a labeling system (e.g., `<style=casual>`) to allow the model to learn context-specific registers (Formal, Spoken, Chennai slang).
- **Phonetic Encoding**: Built a custom rule-based engine to map Roman characters (Tanglish) to their exact Tamil phonetic equivalents before translation begins.

### 2. Architecture: Sequence-to-Sequence with Attention
DeepTranslate leverages the **Transformer architecture**, specifically a distilled version of **NLLB-200 (No Language Left Behind)**. 
- **Encoder**: Receives the source text and converts it into high-dimensional semantic vectors.
- **Attention Mechanism**: Allows the model to weigh the importance of different words in a sentence, solving the "long-distance dependency" problem in complex Tamil syntax.
- **Decoder**: Reconstructs the English output token by token, guided by the semantic vectors from the encoder.

### 3. Training Strategy: Low-Rank Adaptation (LoRA)
To achieve high accuracy on standard hardware (8GB RAM), we implemented **LoRa**:
- Instead of updating all 600M parameters, we train a small set of "rank decomposition matrices" ($r=8$).
- This reduces the trainable parameter count by >99%, preserving the core linguistic knowledge of the base model while rapidly adapting it to Tamil colloquialisms.
- **Loss Function**: Used label-smoothed cross-entropy loss to improve generalization and reduce overconfidence.

### 4. Cultural Insight Logic (Semantic Analysis)
- **Heuristic Detection**: The system cross-references translations against a curated database of 200+ Tamil idioms.
- **Metaphorical Expansion**: When a match is found, the system interrupts the standard flow to provide an "Insight" explaining the cultural context, ensuring the metaphor is not lost in literal translation.

## 🚀 Key Features
- **✨ Magic Transliterate**: Integrated phonetic engine to convert "Tanglish" (Tamil in Latin script) into accurate Tamil script instantly.
- **🧠 Cultural Intelligence**: Real-time detection of Tamil idioms and proverbs with a dedicated "Insight Engine" to explain metaphorical context.
- **🎭 Multi-Style Control**: Domain-specific adaptation for **Formal, Casual, Spoken, and Regional dialects (Chennai/Madurai)** via LoRA.
- **💾 8GB RAM Optimized**: Advanced memory management using **LoRA (Low-Rank Adaptation)** and sequential model loading for stable execution on standard laptops.
- **⚡ Production API**: FastAPI-powered server with support for batching and real-time inference.
- **🔍 Attention Visualization**: Tool to generate attention heatmaps to analyze how the model "sees" the relationship between words.
- **📦 ONNX Export**: Optimized for ultra-low latency deployment.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 🚀 Inference
Run a quick translation:
```bash
python -m src.nllb_inference --text "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?"
```

### 📈 Batch Translation
```bash
python -m src.nllb_inference --batch "வாழ்க தமிழ்" "உங்களை சந்தித்ததில் மகிழ்ச்சி"
```

### ⚡ FastAPI Server
Start the server:
```bash
python -m src.nllb_server
```
Endpoint: `POST http://localhost:8000/translate`  
Body: `{"text": "யாருக்காவது உதவி தேவையா?"}`

### 🛠️ Fine-tuning
Prepare a CSV with `tamil` and `english` columns:
```bash
python -m src.nllb_finetune --csv data/custom.csv --epochs 3 --batch-size 16 --eight_bit
```

### 🔍 Attention Visualization
Generate an attention map:
```bash
python -m src.nllb_viz --text "யாருக்காவது உதவி தேவையா?" --output attention.png
```

## Example Sentences for Testing
1. **வணக்கம்!** (Hello!)
2. **உங்கள் பெயர் என்ன?** (What is your name?)
3. **நான் இந்தியாவிலிருந்து வருகிறேன்.** (I am from India.)
4. **இன்று வானிலை மிகவும் நன்றாக இருக்கிறது.** (The weather is very good today.)
5. **உதவிக்கு மிக்க நன்றி.** (Thank you very much for the help.)

## Evaluation
Run BLEU evaluation on a parallel corpus:
```bash
python -m src.nllb_evaluate --csv data/test.csv
```
