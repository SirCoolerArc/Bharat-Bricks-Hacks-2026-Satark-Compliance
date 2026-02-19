"""
src/__init__.py — InsightX
==========================
Exposes top-level imports so other modules and the app layer can use:
    from src import get_dataframe, CONSTANTS, VALID_VALUES
instead of reaching into submodules directly.
"""

from src.data_loader import (
    get_dataframe,
    get_subset,
    get_constants,
    get_valid_values,
    get_high_value_df,
    sample_size_warning,
    CONSTANTS,
    VALID_VALUES,
)

__all__ = [
    "get_dataframe",
    "get_subset",
    "get_constants",
    "get_valid_values",
    "get_high_value_df",
    "sample_size_warning",
    "CONSTANTS",
    "VALID_VALUES",
]