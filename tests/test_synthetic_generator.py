"""
Tests for Synthetic Dataset Generator and Reset Mechanisms.
"""

from src.data.generator import SyntheticDataGenerator
from src.data.validator import DatasetValidator
from src.database.connection import SessionLocal


def test_synthetic_data_generator_and_reset(db_session):
    """
    Tests that generator produces connected records and reset clears synthetic records.
    """
    gen = SyntheticDataGenerator(seed=123, target_records=1000)

    # 1. Reset
    gen.reset_synthetic_data(db_session)

    # 2. Generate
    res = gen.generate_full_dataset(session=db_session)
    assert res["total_records"] > 500
    assert "sales" in res["table_counts"]
    assert "products" in res["table_counts"]

    # 3. Validate
    report = DatasetValidator.run_full_validation(session=db_session)
    assert report["status"] == "PASS"
    assert report["referential_integrity"]["status"] == "PASS"
    assert report["financial_consistency"]["status"] == "PASS"

    # 4. Reset again
    del_counts = gen.reset_synthetic_data(db_session)
    assert sum(del_counts.values()) > 0
