import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import threading
from .nllb_inference import NLLBTranslator
from .transliterate_utils import transliterate_tanglish
import os

class DeepTranslateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepTranslate - Bidirectional NMT (NLLB-200)")
        self.root.geometry("600x600")
        
        # Configure colors (Premium Look)
        self.bg_color = "#f0f2f5"
        self.primary_color = "#1a73e8"
        self.text_color = "#3c4043"
        
        self.root.configure(bg=self.bg_color)
        
        # Translation Direction State
        self.src_lang = "tam_Taml"
        self.tgt_lang = "eng_Latn"
        self.src_label_text = "Tamil Input:"
        self.tgt_label_text = "English Translation:"
        
        # Style Options
        self.styles = ["standard", "formal", "casual", "literary", "spoken", "chennai", "madurai"]
        self.selected_style = tk.StringVar(value="standard")
        
        # Enhanced Model (LoRA)
        self.use_enhanced = tk.BooleanVar(value=False)
        # Check for refined adapter first, then legacy
        refined_path = os.path.join(os.getcwd(), "nllb_lora_refined", "best_model")
        legacy_path = os.path.join(os.getcwd(), "nllb_lora_results", "best_model")
        
        if os.path.exists(refined_path):
            self.adapter_path = refined_path
        else:
            self.adapter_path = legacy_path
        
        # Load Translator
        self.translator = None
        self.status_label = None # Will be defined in setup_ui
        self.setup_ui()
        
        self.loading_thread = threading.Thread(target=self.load_model, daemon=True)
        self.loading_thread.start()
        
    def load_model(self):
        try:
            # Check if adapter exists
            adapter = self.adapter_path if self.use_enhanced.get() and os.path.exists(self.adapter_path) else None
            
            self.status_label.config(text=f"Loading {'Enhanced ' if adapter else ''}Model...", fg="orange")
            self.translator = NLLBTranslator(adapter_path=adapter)
            self.root.after(0, self.on_model_loaded)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Load Error", f"Failed to load NLLB model: {str(e)}"))

    def on_model_loaded(self):
        self.status_label.config(text="Model Ready (NLLB-200)", fg="green")
        self.translate_btn.config(state=tk.NORMAL)

    def setup_ui(self):
        # Header
        header = tk.Label(self.root, text="DeepTranslate NMT", font=("Helvetica", 18, "bold"), 
                          bg=self.bg_color, fg=self.primary_color, pady=20)
        header.pack()
        
        # Swap Direction Button
        self.swap_btn = tk.Button(self.root, text="⇄ Swap Direction", command=self.swap_direction,
                                  bg="white", fg=self.primary_color, font=("Helvetica", 10, "bold"),
                                  padx=10, pady=5, relief=tk.FLAT, borderwidth=1)
        self.swap_btn.pack(pady=5)
        
        # Style Selection
        style_frame = tk.Frame(self.root, bg=self.bg_color)
        style_frame.pack(pady=5)
        
        tk.Label(style_frame, text="Translation Style:", font=("Helvetica", 10), 
                 bg=self.bg_color, fg=self.text_color).pack(side=tk.LEFT, padx=5)
        
        self.style_dropdown = ttk.Combobox(style_frame, textvariable=self.selected_style, 
                                           values=self.styles, state="readonly", width=15)
        self.style_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Enhanced Toggle
        if os.path.exists(self.adapter_path):
            self.enhanced_check = tk.Checkbutton(style_frame, text="Use Enhanced Model (LoRA)", 
                                                 variable=self.use_enhanced, command=self.reload_model,
                                                 bg=self.bg_color, fg=self.primary_color, font=("Helvetica", 9, "bold"))
            self.enhanced_check.pack(side=tk.LEFT, padx=10)
        
        # Input Frame
        input_frame = tk.Frame(self.root, bg=self.bg_color)
        input_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        self.src_title_label = tk.Label(input_frame, text=self.src_label_text, font=("Helvetica", 10, "bold"), 
                                        bg=self.bg_color, fg=self.text_color)
        self.src_title_label.pack(anchor=tk.W)
        
        self.input_text = scrolledtext.ScrolledText(input_frame, height=5, font=("Helvetica", 11))
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(5, 5))
        
        # Transliterate Button
        self.translit_btn = tk.Button(input_frame, text="✨ Magic Transliterate (Tanglish -> Tamil)", 
                                      command=self.handle_transliterate,
                                      bg="#e8f0fe", fg=self.primary_color, font=("Helvetica", 9, "bold"),
                                      padx=10, pady=2, relief=tk.GROOVE)
        self.translit_btn.pack(anchor=tk.E)
        
        # Translate Button
        self.translate_btn = tk.Button(self.root, text="Translate", command=self.start_translation,
                                       bg=self.primary_color, fg="white", font=("Helvetica", 12, "bold"),
                                       padx=20, pady=10, state=tk.DISABLED)
        self.translate_btn.pack(pady=10)
        
        # Output Frame
        output_frame = tk.Frame(self.root, bg=self.bg_color)
        output_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        self.tgt_title_label = tk.Label(output_frame, text=self.tgt_label_text, font=("Helvetica", 10, "bold"), 
                                        bg=self.bg_color, fg=self.text_color)
        self.tgt_title_label.pack(anchor=tk.W)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=5, font=("Helvetica", 11), state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(5, 5))
        
        # Cultural Insights Panel
        self.insight_frame = tk.Frame(self.root, bg="#fff3e0", bd=1, relief=tk.SOLID)
        self.insight_label = tk.Label(self.insight_frame, text="💡 Cultural Insight:", font=("Helvetica", 9, "bold"), 
                                      bg="#fff3e0", fg="#e65100")
        self.insight_label.pack(anchor=tk.W, padx=5, pady=2)
        self.insight_text = tk.Label(self.insight_frame, text="", font=("Helvetica", 9), 
                                     bg="#fff3e0", fg="#3c4043", wraplength=550, justify=tk.LEFT)
        self.insight_text.pack(fill=tk.X, padx=5, pady=(0, 5))
        # Keep hidden initially
        # self.insight_frame.pack(...) will be called when insight is found
        
        # Status Bar
        self.status_label = tk.Label(self.root, text="Loading NLLB-200 Model...", font=("Helvetica", 9), 
                                     bg=self.bg_color, fg="orange", pady=5)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def swap_direction(self):
        # Swap language codes
        self.src_lang, self.tgt_lang = self.tgt_lang, self.src_lang
        
        # Swap labels
        if self.src_lang == "tam_Taml":
            self.src_label_text = "Tamil Input:"
            self.tgt_label_text = "English Translation:"
        else:
            self.src_label_text = "English Input:"
            self.tgt_label_text = "Tamil Translation:"
            
        self.src_title_label.config(text=self.src_label_text)
        self.tgt_title_label.config(text=self.tgt_label_text)
        
        # Clear fields
        self.input_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.insight_frame.pack_forget()

    def handle_transliterate(self):
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            return
        transliterated = transliterate_tanglish(text)
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, transliterated)

    def start_translation(self):
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            return
            
        self.translate_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Translating...", fg="blue")
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        threading.Thread(target=self.perform_translation, args=(text,), daemon=True).start()

    def perform_translation(self, text):
        try:
            translation = self.translator.translate(
                text, 
                src_lang=self.src_lang, 
                tgt_lang=self.tgt_lang,
                style=self.selected_style.get()
            )
            self.root.after(0, lambda: self.show_translation(translation))
        except Exception as e:
            self.root.after(0, lambda: self.on_translation_error(str(e)))

    def show_translation(self, translation):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, translation)
        self.output_text.config(state=tk.DISABLED)
        
        # Check for Cultural Insights
        text_to_analyze = self.input_text.get("1.0", tk.END) if self.src_lang == "tam_Taml" else translation
        insights = self.translator.analyze_culture(text_to_analyze)
        
        if insights:
            insight = insights[0] # Show the first one for simplicity
            self.insight_text.config(text=f"'{insight['term']}' is a metaphor for: {insight['metaphor']}\nContext: {insight['context']}")
            self.insight_frame.pack(padx=20, pady=10, fill=tk.X, before=self.status_label)
        else:
            self.insight_frame.pack_forget()

        self.translate_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Model Ready", fg="green")

    def reload_model(self):
        self.translate_btn.config(state=tk.DISABLED)
        self.loading_thread = threading.Thread(target=self.load_model, daemon=True)
        self.loading_thread.start()

    def on_translation_error(self, error):
        messagebox.showerror("Translation Error", f"An error occurred: {error}")
        self.translate_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Model Ready", fg="green")

if __name__ == "__main__":
    root = tk.Tk()
    app = DeepTranslateGUI(root)
    root.mainloop()
