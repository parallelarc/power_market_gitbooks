#!/usr/bin/env python3
"""
修复数学公式格式 - 简化版
将裸露的LaTeX公式用 $$ 包裹
"""
import re
from pathlib import Path

def fix_math_formulas(content):
    """修复数学公式"""
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        stripped = line.strip()

        # 检测包含LaTeX命令的行
        latex_indicators = [
            r'\\text\s*\{',
            r'\\frac\{',
            r'\\frac\s',
            r'\\begin\{',
            r'\\end\{',
        ]

        has_latex = any(re.search(pattern, stripped) for pattern in latex_indicators)

        # 如果包含LaTeX命令且未被$$包裹
        if has_latex:
            if not (stripped.startswith('$$') and stripped.endswith('$$')):
                # 保留原始缩进
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
            print(f"✓ {file_path.relative_to(file_path.parent.parent)}")
            return True
        return False
    except Exception as e:
        print(f"✗ 错误处理 {file_path}: {e}")
        return False

def main():
    """主函数"""
    book_dir = Path('/Users/rjv/Projects/power_market_gitbooks/book2')

    # 查找所有 markdown 文件
    md_files = list(book_dir.rglob('*.md'))

    print("开始修复数学公式格式...\n")
    print("修复规则：将包含LaTeX命令的行用$$包裹\n")

    fixed_count = 0
    for md_file in md_files:
        if process_file(md_file):
            fixed_count += 1

    print(f"\n修复完成！共修复 {fixed_count} 个文件")

if __name__ == '__main__':
    main()
