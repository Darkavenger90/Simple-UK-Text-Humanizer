#!/usr/bin/env python3
"""
uk_academic_humaniser.py

Humanises text into a UK-academic style:
- Avoids slang and contractions
- Uses formal but natural phrasing
- Introduces mild logical connectors
- Smooths over rigid transitions
- Keeps arguments clear and structured

Usage:
    python uk_academic_humaniser.py
"""

import re
from textwrap import fill
import random

# Formal connectors suitable for UK academic writing
ACADEMIC_CONNECTORS = [
    "Moreover, ",
    "Furthermore, ",
    "In addition, ",
    "It is also important to note that ",
    "However, ",
    "Consequently, ",
    "Therefore, ",
]

# Light rephrasings to sound academically natural
LIGHT_REPHRASINGS = [
    (r"\bin conclusion\b", "overall"),
    (r"\btherefore\b", "therefore"),
    (r"\bmoreover\b", "moreover"),
    (r"\bfurthermore\b", "furthermore"),
    (r"\bin addition\b", "in addition"),
    (r"\bto summarise\b", "to summarise"),
]


def split_sentences(text: str):
    """Crude sentence splitter."""
    text = re.sub(r"([.!?])([A-Za-z])", r"\1 \2", text)
    parts = re.split(r"([.!?])", text)
    sentences = []
    for i in range(0, len(parts) - 1, 2):
        s = (parts[i] + parts[i + 1]).strip()
        if s:
            sentences.append(s)
    if len(parts) % 2 != 0 and parts[-1].strip():
        sentences.append(parts[-1].strip())
    return sentences


def apply_light_rephrasings(text: str) -> str:
    for pattern, replacement in LIGHT_REPHRASINGS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def academic_tone(sentence: str, idx: int, total: int) -> str:
    original = sentence

    # Very mild rephrasing
    s = apply_light_rephrasings(sentence)

    # Add connectors between sentences (sparingly)
    if 0 < idx < total and random.random() < 0.35:
        connector = random.choice(ACADEMIC_CONNECTORS)
        s = connector + s[0].lower() + s[1:]

    # Do not introduce contractions in UK academic writing
    return s or original


def humanise_uk_academic(text: str, wrap: int = 90):
    """Humanises text to a natural UK-academic tone."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    sentences = split_sentences(text)
    new = []

    for idx, s in enumerate(sentences):
        new.append(academic_tone(s, idx, len(sentences)))

    result = " ".join(new)

    return fill(result, width=wrap)


# CLI
def main():
    import sys

    print("Paste text to humanise (Ctrl+D to finish):\n")
    text = sys.stdin.read()
    out = humanise_uk_academic(text)
    print("\n--- Humanised (UK Academic Tone) ---\n")
    print(out)


if __name__ == "__main__":
    main()
