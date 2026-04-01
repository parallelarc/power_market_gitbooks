#!/usr/bin/env python3
"""
Split 电力市场化交易必读 raw markdown into GitBook structure.

Usage: python split_book.py
"""

import os
import re
import sys

RAW_FILE = "MinerU_markdown_电力市场化交易必读_2039235198297829376.md"
BOOK_DIR = "../电力市场化交易必读"


def parse_raw_file(filepath):
    """Parse the raw markdown file and return structured data."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find where body content starts (after TOC, skip to "# 1 电力市场概述" in body)
    # The body starts after the image line following the TOC
    body_start = None
    for i, line in enumerate(lines):
        # Look for the first occurrence of "# 1 电力市场概述" that is body content
        # The TOC has it at ~line 89, body at ~line 224
        if i > 200 and re.match(r"^# 1 电力市场概述\s*$", line.strip()):
            body_start = i
            break

    if body_start is None:
        print("ERROR: Could not find body start")
        sys.exit(1)

    print(f"Body starts at line {body_start + 1}")

    # Parse body into chapters and sections
    # Pattern: all lines start with "# "
    # NOTE: Some headings have NO space between number and title (OCR artifact):
    #   "# 6电力交易结算", "# 9电力交易平台", "# 2.2市场注册", "# 6.4售电公司结算"
    # Chapter: "# N 章名" or "# N章名" (N is 1-10)
    # Section: "# N.N 节名" or "# N.N节名"
    # Subsection: "# N.N.N 子节名"
    # Deep subsection: "# N.N.N.N ..."
    # Special: "# 第X阶段：..." or "# 1. ..." (numbered items within sections)

    chapters = []
    current_chapter = None
    current_section = None
    current_content = []

    def flush_content():
        nonlocal current_content
        if current_section is not None and current_content:
            current_section["content"].extend(current_content)
        elif current_chapter is not None and current_content:
            current_chapter["intro_content"].extend(current_content)
        current_content = []

    for i in range(body_start, len(lines)):
        line = lines[i]
        stripped = line.strip()

        # Check if this is a heading
        heading_match = re.match(r"^# (.+)$", stripped)

        if heading_match:
            title = heading_match.group(1).strip()

            # IMPORTANT: Check deeper patterns FIRST to avoid partial matches

            # Check for deep subsection: "# N.N.N.N ..." (4 levels)
            deep_match = re.match(r"^(\d+\.\d+\.\d+\.\d+)\s*(.*)$", title)
            if deep_match:
                current_content.append(line)
                continue

            # Check for subsection heading: "# N.N.N 子节名" (3 levels)
            subsection_match = re.match(r"^(\d+\.\d+\.\d+)\s*(.+)$", title)
            if subsection_match:
                flush_content()
                subsec = {
                    "full_num": subsection_match.group(1),
                    "title": subsection_match.group(2).strip(),
                    "content": [],
                }
                if current_section:
                    current_section["subsections"].append(subsec)
                current_content = []
                current_content.append(line)
                continue

            # Check for section heading: "# N.N 节名" or "# N.N节名" (2 levels)
            section_match = re.match(r"^(\d+\.\d+)\s*(.+)$", title)
            if section_match:
                flush_content()
                current_section = {
                    "full_num": section_match.group(1),
                    "title": section_match.group(2).strip(),
                    "content": [],
                    "subsections": [],
                }
                if current_chapter:
                    current_chapter["sections"].append(current_section)
                continue

            # Check for special patterns like "# 第X阶段：", "# 1. ", "# 2. "
            # IMPORTANT: must check BEFORE chapter regex, as "1. ..." would match chapter "1"
            if re.match(r"^第[一二三]阶段", title) or re.match(r"^\d+\.\s", title):
                current_content.append(line)
                continue

            # Check for chapter heading: "# N 章名" or "# N章名" (N is 1-10)
            # Must also ensure title looks like a real chapter name (not ". something")
            chapter_match = re.match(r"^(\d{1,2})\s*(.+)$", title)
            if chapter_match:
                ch_num = int(chapter_match.group(1))
                ch_title = chapter_match.group(2).strip()
                # Valid chapter: number 1-10, title exists, title doesn't start with digit+dot
                if (1 <= ch_num <= 10 and ch_title
                        and not re.match(r"^\d+\.", ch_title)
                        and not ch_title.startswith(".")):
                    flush_content()
                    current_chapter = {
                        "num": ch_num,
                        "title": ch_title,
                        "sections": [],
                        "intro_content": [],
                    }
                    chapters.append(current_chapter)
                    current_section = None
                    continue

            # Other headings - just add as content
            current_content.append(line)
        else:
            current_content.append(line)

    flush_content()

    return chapters


def fix_heading_level(line, section_depth=0):
    """Fix heading levels in content lines.

    In the source file, ALL headings use single # regardless of depth.
    We convert based on numbering pattern:
    - N.N -> ## (one level below the section title which is #)
    - N.N.N.N -> ###
    - 第X阶段 / "1. " -> ###
    """
    heading_match = re.match(r"^(#+)\s+(.+)$", line)
    if not heading_match:
        return line

    title = heading_match.group(2)

    # Determine the actual depth of this heading by its numbering
    # In a section file (N.N), the hierarchy is:
    #   # = N.N section title
    #   ## = N.N.N subsection
    #   ### = N.N.N.N deep subsection
    #   ### = special items
    if re.match(r"^\d+\.\d+\.\d+\.\d+", title):
        return f"### {title}\n"
    elif re.match(r"^\d+\.\d+\.\d+", title):
        return f"## {title}\n"
    elif re.match(r"^第[一二三]阶段", title):
        return f"### {title}\n"
    elif re.match(r"^\d+\.\s", title):
        return f"### {title}\n"
    else:
        return line


def clean_content(lines):
    """Clean up content lines."""
    result = []
    for line in lines:
        # Fix heading levels
        line = fix_heading_level(line)
        result.append(line)

    # Remove trailing empty lines
    while result and result[-1].strip() == "":
        result.pop()

    return result


def generate_chapter_readme(chapter):
    """Generate README.md content for a chapter."""
    num = chapter["num"]
    title = chapter["title"]
    return f"# 第{num}章 {title}\n\n"


def generate_section_file(section, chapter_num):
    """Generate content for a section file."""
    full_num = section["full_num"]
    title = section["title"]
    content_lines = section.get("content", [])

    lines = [f"# {full_num} {title}\n\n"]

    # Process content - skip leading empty lines
    cleaned = clean_content(content_lines)
    while cleaned and cleaned[0].strip() == "":
        cleaned.pop(0)

    if cleaned:
        lines.extend(cleaned)
        lines.append("\n")

    return "".join(lines)


def generate_summary(chapters):
    """Generate SUMMARY.md content."""
    lines = ["# Summary\n\n"]
    lines.append("* [简介](README.md)\n\n")

    cn_nums = {
        1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
        6: "六", 7: "七", 8: "八", 9: "九", 10: "十",
    }

    for ch in chapters:
        ch_num = ch["num"]
        ch_title = ch["title"]
        cn = cn_nums.get(ch_num, str(ch_num))
        ch_dir = f"chapters/chapter-{ch_num:02d}"

        lines.append(f"* [第{cn}章 {ch_title}]({ch_dir}/README.md)\n")

        for sec in ch["sections"]:
            sec_num = sec["full_num"]
            sec_title = sec["title"]
            # Generate filename: sNNNN
            parts = sec_num.split(".")
            fname = f"s{int(parts[0]):02d}{int(parts[1]):02d}.md"
            lines.append(f"  * [{sec_num} {sec_title}]({ch_dir}/{fname})\n")

            # Add subsections as deeper entries
            for subsec in sec.get("subsections", []):
                sub_num = subsec["full_num"]
                sub_title = subsec["title"]
                lines.append(
                    f"    * [{sub_num} {sub_title}]({ch_dir}/{fname}#{sub_num}-{sub_title.lower().replace(' ', '-')})\n"
                )

        lines.append("\n")

    return "".join(lines)


def generate_readme():
    """Generate root README.md."""
    return """# 电力市场化交易必读

**陈向群 罗朝春 等 编著**

本书主要聚焦电力市场的基本概念和运行实操，全面介绍电力市场发展背景和最新政策要求，着力阐述市场准入与退出、中长期交易分类与基本流程、各类市场主体结算流程与清算算法、交易平台开发与应用、合同管理与信用评价等电力交易核心业务，深度介绍电力现货交易与辅助服务市场、可再生能源消纳等最新发展方向，并探讨了交易机构公司化规范运行的路径。

> 中国电力出版社，2023年6月
>
> ISBN 978-7-5198-7681-4
"""


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_path = os.path.join(script_dir, RAW_FILE)
    book_path = os.path.join(script_dir, BOOK_DIR)

    print(f"Reading: {raw_path}")
    print(f"Output:  {book_path}")

    chapters = parse_raw_file(raw_path)

    print(f"\nParsed {len(chapters)} chapters:")
    for ch in chapters:
        print(f"  Chapter {ch['num']}: {ch['title']} ({len(ch['sections'])} sections)")
        for sec in ch["sections"]:
            print(f"    {sec['full_num']} {sec['title']}")

    # Create directory structure
    os.makedirs(book_path, exist_ok=True)

    # Write root README
    readme_path = os.path.join(book_path, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(generate_readme())
    print(f"\nWrote {readme_path}")

    # Write SUMMARY
    summary_path = os.path.join(book_path, "SUMMARY.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(generate_summary(chapters))
    print(f"Wrote {summary_path}")

    # Write chapters
    for ch in chapters:
        ch_num = ch["num"]
        ch_dir = os.path.join(book_path, "chapters", f"chapter-{ch_num:02d}")
        os.makedirs(ch_dir, exist_ok=True)

        # Chapter README
        readme = generate_chapter_readme(ch)
        readme_path = os.path.join(ch_dir, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme)

        # Section files
        for sec in ch["sections"]:
            parts = sec["full_num"].split(".")
            fname = f"s{int(parts[0]):02d}{int(parts[1]):02d}.md"
            content = generate_section_file(sec, ch_num)
            sec_path = os.path.join(ch_dir, fname)
            with open(sec_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  Wrote {fname}")

    print("\nDone!")


if __name__ == "__main__":
    main()
