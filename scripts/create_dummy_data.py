en_sentences = [
    "Hello", "How are you?", "What is your name?", "I am fine.", "Good morning.",
    "Tamil is a beautiful language.", "Where are you going?", "I love to learn new things.",
    "This is a test sentence.", "Neural machine translation is powerful."
]

ta_sentences = [
    "வணக்கம்", "நீங்கள் எப்படி இருக்கிறீர்கள்?", "உங்கள் பெயர் என்ன?", "நான் நலமாக இருக்கிறேன்.", "காலை வணக்கம்.",
    "தமிழ் ஒரு அழகான மொழி.", "நீங்கள் எங்கே போகிறீர்கள்?", "புதிய விஷயங்களைக் கற்றுக்கொள்வது எனக்குப் பிடிக்கும்.",
    "இது ஒரு சோதனை வாக்கியம்.", "நரம்பியல் இயந்திர மொழிபெயர்ப்பு சக்தி வாய்ந்தது."
]

# Duplicate to make a small corpus
with open('data/train.en', 'w', encoding='utf-8') as f_en, \
     open('data/train.ta', 'w', encoding='utf-8') as f_ta:
    for _ in range(200):  # Repeat to make it enough for a quick train
        for en, ta in zip(en_sentences, ta_sentences):
            f_en.write(en + '\n')
            f_ta.write(ta + '\n')

with open('data/val.en', 'w', encoding='utf-8') as f_en, \
     open('data/val.ta', 'w', encoding='utf-8') as f_ta:
    for en, ta in zip(en_sentences, ta_sentences):
        f_en.write(en + '\n')
        f_ta.write(ta + '\n')

print("Dummy dataset created in data/ directory.")
