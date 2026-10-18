"""
Reproducible Dataset Splitting and Leakage Prevention Module.
Provides stratified partitioning for classification and chronological
rolling-origin backtesting splits for time-series forecasting.
"""

from __future__ import annotations

import random
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit


class DataSplitter:
    """Manages leakage-free dataset partitions for competitive evaluation."""

    @classmethod
    def stratified_train_val_test_split(
        cls,
        samples: List[Dict[str, Any]],
        target_field: str = "document_class",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Splits samples into Train, Validation, and Test sets with exact class stratification.
        Guarantees zero overlap in sample identities.
        """
        if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-5:
            raise ValueError("Ratios must sum to exactly 1.0")

        n = len(samples)
        if n < 10:
            raise ValueError(f"Sample count ({n}) is too small for 3-way stratified splitting.")

        y = [s[target_field] for s in samples]

        # First split: Train vs Temp (Val + Test)
        temp_ratio = val_ratio + test_ratio
        sss1 = StratifiedShuffleSplit(n_splits=1, test_size=temp_ratio, random_state=seed)
        train_idx, temp_idx = next(sss1.split(samples, y))

        train_set = [samples[i] for i in train_idx]
        temp_samples = [samples[i] for i in temp_idx]
        temp_y = [y[i] for i in temp_idx]

        # Second split: Val vs Test from Temp
        val_share_of_temp = val_ratio / temp_ratio
        sss2 = StratifiedShuffleSplit(n_splits=1, test_size=(1.0 - val_share_of_temp), random_state=seed)
        val_sub_idx, test_sub_idx = next(sss2.split(temp_samples, temp_y))

        val_set = [temp_samples[i] for i in val_sub_idx]
        test_set = [temp_samples[i] for i in test_sub_idx]

        # Audit for leakage
        cls._verify_leakage(train_set, val_set, test_set)

        return train_set, val_set, test_set

    @classmethod
    def chronological_rolling_origin_split(
        cls,
        time_series: List[Dict[str, Any]],
        horizon_days: int = 30,
        min_train_days: int = 60,
        step_days: int = 14,
    ) -> List[Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]]:
        """
        Generates chronological rolling-origin backtesting folds.
        For each fold i:
        Train window: [0, t]
        Test window: [t + 1, t + horizon_days]
        Zero lookahead into the future.
        """
        n = len(time_series)
        if n < min_train_days + horizon_days:
            raise ValueError(
                f"Time-series length ({n}) is shorter than min_train_days ({min_train_days}) + horizon ({horizon_days})"
            )

        folds = []
        origin = min_train_days

        while origin + horizon_days <= n:
            train_fold = time_series[:origin]
            test_fold = time_series[origin : origin + horizon_days]
            folds.append((train_fold, test_fold))
            origin += step_days

        return folds

    @classmethod
    def _verify_leakage(
        cls,
        train_set: List[Dict[str, Any]],
        val_set: List[Dict[str, Any]],
        test_set: List[Dict[str, Any]],
        id_field: str = "image_id",
    ) -> None:
        """Asserts that no sample ID appears in more than one partition."""
        train_ids = {s.get(id_field, id(s)) for s in train_set}
        val_ids = {s.get(id_field, id(s)) for s in val_set}
        test_ids = {s.get(id_field, id(s)) for s in test_set}

        tv_leak = train_ids & val_ids
        tt_leak = train_ids & test_ids
        vt_leak = val_ids & test_ids

        if tv_leak or tt_leak or vt_leak:
            raise RuntimeError(
                f"Data Leakage Detected! Intersections: Train-Val: {len(tv_leak)}, Train-Test: {len(tt_leak)}, Val-Test: {len(vt_leak)}"
            )
