"""
Download EU import data from the Eurostat Comext API.

The API is public and needs no key. Data come from dataset DS-045409.
"""

import json
import os

import requests

BASE_URL = (
    "https://ec.europa.eu/eurostat/api/comext/dissemination/"
    "statistics/1.0/data/DS-045409"
)
TIMEOUT_SECONDS = 60


class ComextError(Exception):
    """Raised when the Comext data cannot be obtained."""


def build_params(products, partners, periods, reporter="EU", freq="A"):
    """
    Build the parameters for a Comext import request.

    Parameters
    ----------
    products : str or list
        CN product codes.
    partners : str or list
        Partner countries, e.g. "CN" or "EXT_EU".
    periods : str or list
        Years ("2024") or months ("2024-04").
    reporter : str
        Importing country, "EU" by default.
    freq : str
        "A" for annual or "M" for monthly data.

    Returns
    -------
    dict
        Parameters for requests.get.
    """
    return {
        "format": "JSON",
        "reporter": reporter,
        "partner": partners,
        "product": products,
        "flow": "1",
        "indicators": ["QUANTITY_IN_100KG", "VALUE_IN_EUROS"],
        "freq": freq,
        "time": periods,
    }


def fetch_imports(products, partners, periods, reporter="EU", freq="A"):
    """
    Download import quantities and values from the Comext API.

    Parameters
    ----------
    products, partners, periods, reporter, freq
        Same as in build_params.

    Returns
    -------
    dict
        The JSON answer of the API.

    Raises
    ------
    ComextError
        If the request fails or the answer contains no data.
    """
    params = build_params(products, partners, periods, reporter, freq)

    try:
        response = requests.get(BASE_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()  # HTTP errors (400, 404, 500) become exceptions
    except requests.exceptions.Timeout:
        raise ComextError("The Comext API did not answer in time, please retry")
    except requests.exceptions.RequestException as error:
        raise ComextError(f"Could not reach the Comext API: {error}")

    try:
        data = response.json()
    except ValueError:
        raise ComextError("The Comext API did not return valid JSON")

    if not data.get("value"):
        raise ComextError(
            "No data found for these parameters. "
            "Check the product code and that periods match freq "
            "('2024' for 'A', '2024-04' for 'M')."
        )

    return data


def save_json(data, path):
    """
    Save an API answer to a JSON file.

    The folder is created if it does not exist yet.

    Parameters
    ----------
    data : dict
        Answer returned by fetch_imports.
    path : str
        Destination file, e.g. "data/raw/magnets.json".
    """
    folder = os.path.dirname(path)
    if folder != "":
        os.makedirs(folder, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(path):
    """
    Read an API answer saved with save_json.

    Parameters
    ----------
    path : str
        Path of the JSON file.

    Returns
    -------
    dict
        The saved answer.

    Raises
    ------
    ComextError
        If the file does not exist.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ComextError(f"File not found: {path}. Download the data first.")
    
def download_imports(path, products, partners, periods, reporter="EU", freq="A"):
    """
    Download imports and save them to a JSON file, unless it already exists.

    Parameters
    ----------
    path : str
        Where to save the file, e.g. "data/raw/magnets.json".
    products, partners, periods, reporter, freq
        Same as in build_params.

    Returns
    -------
    dict
        The answer of the API, read from the file.
    """
    if not os.path.exists(path):
        data = fetch_imports(products, partners, periods, reporter, freq)
        save_json(data, path)
    return load_json(path)