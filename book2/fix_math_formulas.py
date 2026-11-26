#!/usr/bin/env python3
"""
修复数学公式格式 - 简化版
将裸露的LaTeX公式用 $$ 包裹

注意：仅处理纯公式行（不含中文或其他散文文本的行）。
包含内联数学（$...$）的散文段落不应被包裹在 $$ 中。
"""
import re
from pathlib import Path


def is_escaped(text, index):
    """字符前有奇数个连续反斜杠时，该字符被转义。"""
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == '\\':
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def remove_text_blocks(text):
    """移除完整的 LaTeX text 块，支持嵌套括号和转义括号。"""
    parts = []
    cursor = 0
    for match in re.finditer(r'\\text\s*\{', text):
        if match.start() < cursor or is_escaped(text, match.start()):
            continue
        depth = 1
        end = match.end()
        while end < len(text) and depth:
            if not is_escaped(text, end):
                if text[end] == '{':
                    depth += 1
                elif text[end] == '}':
                    depth -= 1
            end += 1
        if depth:
            # 不完整的块保留原文，避免把无法确认的内容当作纯公式。
            break
        parts.append(text[cursor:match.start()])
        cursor = end
    parts.append(text[cursor:])
    return ''.join(parts)


def fix_math_formulas(content):
    """修复数学公式"""
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        stripped = line.strip()

        # 跳过空行
        if not stripped:
            fixed_lines.append(line)
            continue

        # 已经被$$包裹的行不需要处理
        if stripped.startswith('$$') and stripped.endswith('$$'):
            fixed_lines.append(line)
            continue

        # 检测包含LaTeX命令的行
        latex_indicators = [
            r'\\text\s*\{',
            r'\\frac\{',
            r'\\frac\s',
            r'\\begin\{',
            r'\\end\{',
        ]

        has_latex = any(re.search(pattern, stripped) for pattern in latex_indicators)

        if has_latex:
            # 跳过包含内联数学的散文行。这些行混合了普通文本和
            # $...$ 内联公式，不应被包裹在 $$ 块公式中。
            # 检测方式：检查是否有内联数学标记（单个$），或者
            # 在 \text{} 块之外是否有CJK字符（中文散文）。
            has_inline_math = any(
                not is_escaped(stripped, match.start())
                for match in re.finditer(r'(?<!\$)\$(?!\$)', stripped)
            )
            # 去掉 \text{...} 块后，检查剩余部分是否含有CJK字符
            text_removed = remove_text_blocks(stripped)
            has_cjk_outside_text = re.search(r'[\u4e00-\u9fff]', text_removed)

            if has_cjk_outside_text or has_inline_math:
                # 这是包含内联数学的散文行，不要用$$包裹
                fixed_lines.append(line)
                continue

            # 纯公式行：用$$包裹
            indent = len(line) - len(line.lstrip())
            line = ' ' * indent + '$$' + stripped + '$$'

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)

def process_file(file_path):
    """处理单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 修复数学公式
        fixed_content = fix_math_formulas(content)

        # 如果内容有变化，写回文件
        if fixed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"  fixed: {file_path.relative_to(file_path.parent.parent)}")
            return True
        return False
    except Exception as e:
        print(f"  error: {file_path}: {e}")
        return False

def main():
    """主函数"""
    book_dir = Path(__file__).resolve().parent

    # 查找所有 markdown 文件
    md_files = list(book_dir.rglob('*.md'))

    print("开始修复数学公式格式...\n")
    print("修复规则：将纯LaTeX公式行用$$包裹（跳过含内联数学的散文行）\n")

    fixed_count = 0
    for md_file in md_files:
        if process_file(md_file):
            fixed_count += 1

    print(f"\n修复完成！共修复 {fixed_count} 个文件")

if __name__ == '__main__':
    main()
