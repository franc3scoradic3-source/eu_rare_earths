"""
Turn the answers of the Comext API into pandas tables.
"""

import os

import numpy as np
import pandas as pd

# Folder where the clean tables are saved as CSV files.
CLEAN_DATA_DIR = os.path.join("data", "clean")


def to_dataframe(data):
    """
    Convert a Comext answer into a table with one row per value.

    Parameters
    ----------
    data : dict
        Answer returned by fetch_imports or download_imports.

    Returns
    -------
    pandas.DataFrame
        One column per dimension (reporter, partner, ...) and a column "value".
    """
    dimensions = data["id"]

    # Turn every key into its position along each dimension, all at once.
    keys = np.array(list(data["value"].keys()), dtype=int)
    positions = np.unravel_index(keys, data["size"])

    table = pd.DataFrame({"value": list(data["value"].values())})
    for dimension, dimension_positions in zip(dimensions, positions):
        # The API maps code -> position, so we invert it to get the codes.
        index = data["dimension"][dimension]["category"]["index"]
        codes = {}
        for code, position in index.items():
            codes[position] = code
        table[dimension] = pd.Series(dimension_positions).map(codes)

    return table[dimensions + ["value"]]


def tidy_imports(table):
    """
    Put quantity and value side by side and add tonnes and unit price.

    Parameters
    ----------
    table : pandas.DataFrame
        Table returned by to_dataframe.

    Returns
    -------
    pandas.DataFrame
        One row per reporter, partner, product and period.

    Raises
    ------
    ValueError
        If the table has duplicated rows or negative values.
    """
    # Unlike pivot_table, pivot raises an error on duplicated rows.
    wide = table.pivot(
        index=["reporter", "partner", "product", "time"],
        columns="indicators",
        values="value",
    ).reset_index()
    wide.columns.name = None  # drop the "indicators" label left by pivot

    wide = wide.rename(
        columns={
            "time": "period",
            "QUANTITY_IN_100KG": "quantity_100kg",
            "VALUE_IN_EUROS": "value_eur",
        }
    )

    if (wide[["quantity_100kg", "value_eur"]] < 0).any().any():
        raise ValueError("Quantities and values cannot be negative")

    # Quantities are in units of 100 kg: 10 units make a tonne.
    return wide.assign(
        tonnes=wide["quantity_100kg"] / 10,
        price_eur_kg=wide["value_eur"] / (wide["quantity_100kg"] * 100),
    )