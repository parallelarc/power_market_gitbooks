import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name('fix_math_formulas.py')
spec = importlib.util.spec_from_file_location('fix_math_formulas', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fix_math_formulas = module.fix_math_formulas


class FixMathFormulasTests(unittest.TestCase):
    def test_prose_is_preserved(self):
        for content in (
            r'匹配电量 $Q_{\text{匹配}}$ 等于购方申报电量。',
            r'匹配电量 Q_{\text{匹配}} 等于购方申报电量。',
            r'The price is $\frac{R}{Q}$.',
            r'$\frac{a}{b}$',
            '',
        ):
            with self.subTest(content=content):
                self.assertEqual(fix_math_formulas(content), content)

    def test_bare_formulas_are_wrapped(self):
        for formula in (
            r'Q=\frac{a}{b}',
            r'Q_{\text{匹配}}=\frac{a}{b}',
            r'P=\frac{100\text{\$}}{Q}',
            r'Q_{\text{\textbf{购方}申报}}=\frac{a}{b}',
            r'Q_{\text{\{购方\}申报}}=\frac{a}{b}',
            r'Q_{\text {购方{申报}电量}}=\frac{a}{b}',
        ):
            with self.subTest(formula=formula):
                self.assertEqual(fix_math_formulas(formula), '$$' + formula + '$$')

    def test_even_number_of_backslashes_does_not_escape_dollar(self):
        content = r'Price $\text{USD}\\$ ends here.'
        self.assertEqual(fix_math_formulas(content), content)

    def test_prose_after_nested_text_is_preserved(self):
        content = r'Q_{\text{\textbf{购方}申报}} 表示购方申报电量。'
        self.assertEqual(fix_math_formulas(content), content)

    def test_unbalanced_text_is_left_unchanged(self):
        content = r'Q_{\text{购方申报 = \frac{a}{b}'
        self.assertEqual(fix_math_formulas(content), content)

    def test_indentation_and_idempotence(self):
        content = '  ' + r'Q=\frac{a}{b}' + '\n'
        expected = '  $$' + r'Q=\frac{a}{b}' + '$$\n'
        self.assertEqual(fix_math_formulas(content), expected)
        self.assertEqual(fix_math_formulas(expected), expected)

    def test_current_book_is_unchanged(self):
        for path in SCRIPT.parent.rglob('*.md'):
            with self.subTest(path=path):
                content = path.read_text(encoding='utf-8')
                self.assertEqual(fix_math_formulas(content), content)

    def test_cli_uses_script_directory_from_another_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / 'book2'
            book.mkdir()
            shutil.copyfile(SCRIPT, book / SCRIPT.name)
            chapter = book / 'chapter.md'
            chapter.write_text(r'Q=\frac{a}{b}', encoding='utf-8')
            unrelated = root / 'unrelated.md'
            unrelated.write_text(r'Q=\frac{a}{b}', encoding='utf-8')
            for _ in range(2):
                subprocess.run([sys.executable, str(book / SCRIPT.name)],
                               cwd=root, check=True, capture_output=True, text=True)
            self.assertEqual(chapter.read_text(encoding='utf-8'), r'$$Q=\frac{a}{b}$$')
            self.assertEqual(unrelated.read_text(encoding='utf-8'), r'Q=\frac{a}{b}')


if __name__ == '__main__':
    unittest.main()
