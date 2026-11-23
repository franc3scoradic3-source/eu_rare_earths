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


def save_table(table, path):
    """
    Save a tidy table to a CSV file.

    The folder is created if it does not exist yet.

    Parameters
    ----------
    table : pandas.DataFrame
        Table returned by tidy_imports.
    path : str
        Destination file, e.g. "data/clean/magnets.csv".
    """
    folder = os.path.dirname(path)
    if folder != "":
        os.makedirs(folder, exist_ok=True)

    table.to_csv(path, index=False)


def load_table(path):
    """
    Read a tidy table saved with save_table.

    Parameters
    ----------
    path : str
        Path of the CSV file.

    Returns
    -------
    pandas.DataFrame
        The saved table.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found: save_table() first")

    # Codes and periods are labels, not numbers: read them as text.
    return pd.read_csv(path, dtype={"product": str, "period": str})


def tidy_value_added(table):
    """
    Turn the value added by sector into one value per country and year.

    Parameters
    ----------
    table : pandas.DataFrame
        Table returned by to_dataframe for the national accounts.

    Returns
    -------
    pandas.DataFrame
        Table with columns "reporter", "period", "value_added_meur", for
        the countries with data for all the sectors.
    """
    # Eurostat uses EL for Greece here, and GR in Comext.
    table = table.assign(geo=table["geo"].replace("EL", "GR"))

    by_country = table.groupby(["geo", "time"])["value"].agg(["sum", "count"])
    # A country without all the sectors would look smaller than it is.
    complete = by_country[by_country["count"] == by_country["count"].max()]

    return (
        complete["sum"]
        .reset_index()
        .rename(
            columns={
                "geo": "reporter",
                "time": "period",
                "sum": "value_added_meur",
            }
        )
    )
