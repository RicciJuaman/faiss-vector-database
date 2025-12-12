"""Utility for removing Windows-1252 invalid bytes from CSV files."""
from argparse import ArgumentParser, Namespace
from pathlib import Path

INVALID_BYTES = bytes([0x81, 0x8D, 0x8F, 0x90, 0x9D])


def clean_file(input_path: Path, output_path: Path) -> None:
    """Remove Windows-1252 invalid bytes and save the cleaned file.

    Args:
        input_path: Location of the source CSV file.
        output_path: Destination path for the cleaned CSV output.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("rb") as src, output_path.open("wb") as dst:
        for line in src:
            clean_line = line.translate(None, INVALID_BYTES)
            dst.write(clean_line)



def parse_args() -> Namespace:
    parser = ArgumentParser(description="Clean a CSV by removing invalid Windows-1252 bytes.")
    parser.add_argument("input_path", type=Path, help="Path to the input CSV file")
    parser.add_argument("output_path", type=Path, help="Path to write the cleaned CSV file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    clean_file(args.input_path, args.output_path)
    print(f"Cleaning complete! Saved as {args.output_path}")
