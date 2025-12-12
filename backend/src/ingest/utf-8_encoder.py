"""Re-encode CSV files to UTF-8."""
from argparse import ArgumentParser, Namespace
from pathlib import Path

import pandas as pd


def encode_to_utf8(input_path: Path, output_path: Path) -> None:
    """Load a Latin-1 encoded CSV and write a UTF-8 version."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(input_path, encoding="latin-1", dtype=str)
    df.to_csv(output_path, encoding="utf-8", index=False)


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Re-encode a Latin-1 CSV file to UTF-8.")
    parser.add_argument("input_path", type=Path, help="Path to the source CSV file")
    parser.add_argument("output_path", type=Path, help="Where to save the UTF-8 CSV file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    encode_to_utf8(args.input_path, args.output_path)
    print(f"File re-encoded to UTF-8 and saved as '{args.output_path}'")
