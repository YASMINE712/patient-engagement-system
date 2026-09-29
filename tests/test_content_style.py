"""Repository style guard for the explicit no-emojis requirement."""
from pathlib import Path
import re
import unittest


class ContentStyleTests(unittest.TestCase):
    def test_project_text_contains_no_emojis(self):
        root = Path(__file__).resolve().parents[1]
        pattern = re.compile(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D\u20E3]')
        folders = ('health_friend', 'docs', 'scripts', 'tests', '.github')
        paths = [p for folder in folders for p in (root / folder).rglob('*')]
        paths += list(root.glob('*.md')) + [root / 'data/README.md']
        suffixes = {'.py', '.md', '.html', '.css', '.js', '.yml', '.yaml', '.txt'}
        for path in paths:
            if path.is_file() and path.suffix in suffixes:
                with self.subTest(file=str(path.relative_to(root))):
                    self.assertIsNone(pattern.search(path.read_text(encoding='utf-8')))
