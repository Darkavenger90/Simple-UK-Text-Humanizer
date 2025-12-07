#!/usr/bin/env python3
"""
style_assistant_uk_academic.py

A simple UK-academic style assistant.

Features:
- Analyses text for:
    • Contractions (don't, can't, it's, etc.)
    • Informal / vague words (really, a lot, stuff, etc.)
    • Very long or very short sentences
    • Repeated sentence openings
    • First-person pronouns (I, we, our) – flagged, not banned

- Optionally produces a "cleaned" version:
    • Expands common contractions
    • Softly swaps some informal phrases for more academic ones

Usage examples:
    python style_assistant_uk_academic.py < input.txt
    python style_assistant_uk_academic.py --clean < input.txt
"""

import re
import sys
import collections
from textwrap import fill

# -----------------------------
# Config / dictionaries
# -----------------------------

# Common English contractions to expand in academic writing
CONTRACTION_MAP = {
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "can't": "cannot",
    "cannot": "cannot",
    "won't": "will not",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "hasn't": "has not",
    "haven't": "have not",
    "hadn't": "had not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "couldn't": "could not",
    "I'm": "I am",
    "I'm": "I am",
    "you're": "you are",
    "we're": "we are",
    "they're": "they are",
    "it's": "it is",
    "that's": "that is",
    "there's": "there is",
    "I've": "I have",
    "you've": "you have",
    "we've": "we have",
    "they've": "they have",
    "I'll": "I will",
    "you'll": "you will",
    "we'll": "we will",
    "they'll": "they will",
}

# Informal / vague words to flag (not all must be removed)
INFORMAL_MAP = {
    "really": "highly / very (consider more precise wording)",
    "very": "intensely / extremely (or remove if unnecessary)",
    "a lot": "a substantial amount",
    "lots of": "many / numerous",
    "stuff": "material / content / items (be specific)",
    "things": "aspects / factors / elements (be specific)",
    "kids": "children",
    "big": "significant / substantial",
    "huge": "major / considerable",
    "basically": "fundamentally / essentially (or remove)",
    "pretty": "fairly / relatively (or remove)",
    "kind of": "somewhat / to some extent",
    "sort of": "somewhat / to some extent",
    "gonna": "going to",
    "wanna": "want to",
}

INFORMAL_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in INFORMAL_MAP.keys()) + r")\b",
    flags=re.IGNORECASE,
)

CONTRACTION_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in CONTRACTION_MAP.keys()) + r")\b"
)

FIRST_PERSON_PATTERN = re.compile(r"\b(I|we|We|our|Our|us)\b")

# -----------------------------
# Helpers
# -----------------------------


def split_sentences(text: str):
    """Crude sentence splitter: good enough for this assistant."""
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


def analyse_text(text: str):
    """
    Analyse text and return:
      - sentences
      - list of issues (each issue is a dict)
    """
    sentences = split_sentences(text)
    issues = []

    # Track repeated sentence starts (first 2 words)
    starts = []

    for idx, s in enumerate(sentences, start=1):
        words = re.findall(r"\w+('\w+)?", s)
        word_count = len(words)

        # Sentence length flags
        if word_count > 35:
            issues.append(
                {
                    "type": "long_sentence",
                    "sentence_index": idx,
                    "message": f"Sentence {idx} is quite long ({word_count} words). "
                               f"Consider splitting it for clarity.",
                    "extract": s,
                }
            )
        elif word_count < 7:
            issues.append(
                {
                    "type": "short_sentence",
                    "sentence_index": idx,
                    "message": f"Sentence {idx} is very short ({word_count} words). "
                               f"In academic writing, you may wish to combine it with a neighbouring sentence.",
                    "extract": s,
                }
            )

        # Contractions
        for m in CONTRACTION_PATTERN.finditer(s):
            issues.append(
                {
                    "type": "contraction",
                    "sentence_index": idx,
                    "message": f"Contraction '{m.group(0)}' found in sentence {idx}. "
                               f"Consider using the full form in academic writing.",
                    "extract": s,
                }
            )

        # Informal words
        for m in INFORMAL_PATTERN.finditer(s):
            w = m.group(0)
            suggestion = INFORMAL_MAP.get(w.lower(), "Consider a more precise alternative.")
            issues.append(
                {
                    "type": "informal",
                    "sentence_index": idx,
                    "message": f"Informal or vague word '{w}' in sentence {idx}. {suggestion}",
                    "extract": s,
                }
            )

        # First person (flag only)
        for m in FIRST_PERSON_PATTERN.finditer(s):
            issues.append(
                {
                    "type": "first_person",
                    "sentence_index": idx,
                    "message": f"First-person pronoun '{m.group(0)}' in sentence {idx}. "
                               f"Check if this is appropriate for your assignment guidelines.",
                    "extract": s,
                }
            )

        # Collect sentence start (first 2 words)
        if len(words) >= 2:
            start = " ".join(words[0:2]).lower()
        elif words:
            start = words[0].lower()
        else:
            start = ""
        starts.append(start)

    # Repeated starts
    counter = collections.Counter(starts)
    for idx, start in enumerate(starts, start=1):
        if start and counter[start] > 2:  # appears 3+ times
            issues.append(
                {
                    "type": "repeated_start",
                    "sentence_index": idx,
                    "message": f"Several sentences start with '{start}'. "
                               f"Varying openings can improve academic style and flow.",
                    "extract": sentences[idx - 1],
                }
            )

    return sentences, issues


def clean_text(text: str, wrap: int = 90) -> str:
    """
    Produce a gently 'cleaned' version:
    - Expand contractions
    - Softly replace some informal terms
    """
    def repl_contraction(match):
        word = match.group(0)
        return CONTRACTION_MAP.get(word, CONTRACTION_MAP.get(word.lower(), word))

    cleaned = CONTRACTION_PATTERN.sub(repl_contraction, text)

    # Replace informal terms with suggestions in brackets
    def repl_informal(match):
        word = match.group(0)
        key = word.lower()
        suggestion = INFORMAL_MAP.get(key)
        if suggestion:
            return f"{word} ({suggestion})"
        return word

    cleaned = INFORMAL_PATTERN.sub(repl_informal, cleaned)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return fill(cleaned, width=wrap)


def print_report(sentences, issues):
    print("=== Style Analysis (UK Academic) ===\n")
    print(f"Total sentences: {len(sentences)}")
    print(f"Total issues found: {len(issues)}\n")

    if not issues:
        print("No major style issues detected based on the current checks.")
        return

    for i, issue in enumerate(issues, start=1):
        print(f"Issue {i}: [{issue['type']}]")
        print(issue["message"])
        print("Sentence:", issue["extract"])
        print("-" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="UK-academic style assistant: analyses text and optionally cleans it."
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Output a cleaned version of the text after the analysis.",
    )
    parser.add_argument(
        "--nowrap",
        action="store_true",
        help="Do not wrap cleaned text to a fixed width.",
    )

    args = parser.parse_args()

    if sys.stdin.isatty():
        print("Paste your text below. End input with Ctrl+D (Linux/macOS) or Ctrl+Z then Enter (Windows):\n")

    text = sys.stdin.read()

    if not text.strip():
        print("No input text received.")
        return

    sentences, issues = analyse_text(text)
    print_report(sentences, issues)

    if args.clean:
        print("\n=== Cleaned Version (suggested) ===\n")
        wrap_width = None if args.nowrap else 90
        cleaned = clean_text(text, wrap=wrap_width or 90)
        print(cleaned)


if __name__ == "__main__":
    main()
