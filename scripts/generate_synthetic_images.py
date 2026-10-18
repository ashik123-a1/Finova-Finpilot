import sys
from pathlib import Path
import argparse

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.image_tooling import DocumentImageDatasetTooling

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic document images and manifest")
    parser.add_argument("--count", type=int, default=20, help="Number of sample images (default: 20)")
    args = parser.parse_args()

    manifest_path = DocumentImageDatasetTooling.generate_sample_collection(count=args.count)
    print(f"Generated {args.count} sample images and annotation manifest at:\n{manifest_path}")
