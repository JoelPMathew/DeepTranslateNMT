from src.transliterate_utils import transliterate_tanglish

tests = [
    "vanakkam",
    "enna da soldra",
    "ena da soldra",
    "eppadi irukkiraai",
    "nandri",
    "nandry",
    "tamil",
    "amma",
    "appa"
]

for t in tests:
    print(f"'{t}' -> '{transliterate_tanglish(t)}'")
