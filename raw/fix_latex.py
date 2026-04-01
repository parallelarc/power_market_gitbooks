#!/usr/bin/env python3
"""
Convert LaTeX inline math ($...$) to plain text for GitBook compatibility.

Handles:
- \mathrm{X} → X          (units: kV, min, h, km)
- \% → %
- \sim → ~
- \times → ×
- \rightarrow → →
- \text{X} → X            (Chinese text in subscripts)
- \frac{A}{B} → A/B
- _{X} → ₍X₎             (subscripts)
- \Sigma → Σ
- \pm → ±
- simple symbols like $+$, $=$, $-$

Usage: python fix_latex.py [directory]
       Default directory: ../电力市场化交易必读/
"""

import os
import re
import sys
import glob


def convert_latex(expr):
    """Convert a single LaTeX expression (without $ delimiters) to plain text."""
    s = expr.strip()

    # \frac{A}{B} → A/B (handle before \text removal)
    def frac_replace(m):
        num = m.group(1)
        den = m.group(2)
        return f"{convert_latex(num)}/{convert_latex(den)}"

    s = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", frac_replace, s)

    # \mathrm{X} → X
    s = re.sub(r"\\mathrm\{([^}]*)\}", r"\1", s)

    # \text{X} → X
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)

    # LaTeX symbols
    s = s.replace("\\times", "×")
    s = s.replace("\\Sigma", "Σ")
    s = s.replace("\\rightarrow", "→")
    s = s.replace("\\pm", "±")
    s = s.replace("\\sim", "~")

    # \% → %
    s = s.replace("\\%", "%")

    # Subscript: _{text} → ₍text₎
    # First handle complex subscripts with remaining commands
    def subscript_replace(m):
        inner = convert_latex(m.group(1))
        # Convert to Unicode subscript if simple, else keep as _X
        return subscript_text(inner)

    s = re.sub(r"_\{([^}]*)\}", subscript_replace, s)

    # Simple subscript: _X → ₍X₎
    s = re.sub(r"_([A-Za-z0-9])", lambda m: subscript_text(m.group(1)), s)

    # Clean up remaining backslash commands
    s = s.replace("\\", "")

    # Clean up extra spaces
    s = re.sub(r"\s+", " ", s).strip()

    return s


def subscript_text(text):
    """Convert text to Unicode subscript where possible."""
    sub_map = {
        "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
        "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
        "+": "₊", "-": "₋", "=": "₌",
        "a": "ₐ", "e": "ₑ", "h": "ₕ", "i": "ᵢ", "j": "ⱼ",
        "k": "ₖ", "l": "ₗ", "m": "ₘ", "n": "ₙ", "o": "ₒ",
        "p": "ₚ", "r": "ᵣ", "s": "ₛ", "t": "ₜ", "u": "ᵤ",
    }
    result = ""
    all_convertible = True
    for ch in text:
        if ch in sub_map:
            result += sub_map[ch]
        else:
            all_convertible = False
            break

    if all_convertible:
        return result
    else:
        # For non-convertible (Chinese etc.), use ₍...₎
        return f"₍{text}₎"


def process_line(line):
    """Process a single line, converting all $...$ expressions."""
    # Find all $...$ patterns (non-greedy, but handle adjacent pairs)
    result = []
    i = 0
    while i < len(line):
        if line[i] == "$":
            # Find closing $
            j = line.index("$", i + 1) if "$" in line[i + 1:] else -1
            if j == -1:
                j = i + 1
                # Find actual closing
                try:
                    j = line.index("$", i + 1)
                except ValueError:
                    result.append(line[i])
                    i += 1
                    continue

            expr = line[i + 1 : j]
            converted = convert_latex(expr)
            result.append(converted)
            i = j + 1
        else:
            result.append(line[i])
            i += 1

    return "".join(result)


def process_file(filepath):
    """Process a single markdown file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if "$" not in content:
        return 0

    lines = content.split("\n")
    new_lines = []
    count = 0
    for line in lines:
        new_line = process_line(line)
        if new_line != line:
            count += 1
        new_lines.append(new_line)

    if count > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))

    return count


def main():
    if len(sys.argv) > 1:
        book_dir = sys.argv[1]
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        book_dir = os.path.join(script_dir, "..", "电力市场化交易必读")

    book_dir = os.path.abspath(book_dir)
    print(f"Processing: {book_dir}")

    md_files = glob.glob(os.path.join(book_dir, "**", "*.md"), recursive=True)
    total_changes = 0
    total_files = 0

    for filepath in sorted(md_files):
        changes = process_file(filepath)
        if changes > 0:
            relpath = os.path.relpath(filepath, book_dir)
            print(f"  {relpath}: {changes} lines changed")
            total_changes += changes
            total_files += 1

    print(f"\nDone: {total_files} files, {total_changes} lines modified")


if __name__ == "__main__":
    main()
