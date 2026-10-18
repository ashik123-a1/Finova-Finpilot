import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.validator import DatasetValidator

if __name__ == "__main__":
    print("Running comprehensive dataset audit...")
    report = DatasetValidator.run_full_validation()
    print("\n================ AUDIT SUMMARY ================")
    print(f"Overall Status:            {report['status']}")
    print(f"Total Database Records:    {report['total_records']:,}")
    print(f"Referential Integrity:     {report['referential_integrity']['status']}")
    print(f"Financial Consistency:     {report['financial_consistency']['status']}")
    print(f"Sectors Covered:           {len(report['scenario_coverage']['sectors_covered'])}")
    print("===============================================")
