import sys
from pathlib import Path
import argparse

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.generator import SyntheticDataGenerator

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic SME relational dataset")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--target", type=int, default=100000, help="Target record count (default: 100,000)")
    parser.add_argument("--reset", action="store_true", help="Purge previous synthetic records before generating")
    args = parser.parse_args()

    gen = SyntheticDataGenerator(seed=args.seed, target_records=args.target)
    if args.reset:
        gen.reset_synthetic_data()

    res = gen.generate_full_dataset()
    print(f"Generated {res['total_records']:,} relational records across {len(res['table_counts'])} tables.")
