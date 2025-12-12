import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from ingest.cleaner import INVALID_BYTES, clean_file  # noqa: E402


class CleanFileTests(unittest.TestCase):
    def test_clean_file_strips_invalid_bytes(self):
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "input.csv"
            target = Path(tmpdir) / "output.csv"

            content = b"hello" + INVALID_BYTES + b"world\n"
            source.write_bytes(content)

            clean_file(source, target)

            self.assertEqual(target.read_bytes(), b"helloworld\n")


if __name__ == "__main__":
    unittest.main()
