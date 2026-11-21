"""
Measure how much EU imports depend on China.
"""

from scipy import stats

# Comext code of China as a partner: the numerator of the share.
CHINA = "CN"
# Comext code of all countries outside the EU, China included: the denominator.
EXTRA_EU = "EXT_EU"
# Comext code of trade between EU countries, which is not a dependence.
INTRA_EU = "INT_EU"
# Comext codes of the 27 EU member states (Eurostat uses GR for Greece).
EU_MEMBERS = [
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK",
]


def china_share(table, measure="tonnes"):
    """
    Compute the share of extra-EU imports that comes from China.

    Parameters
    ----------
    table : pandas.DataFrame
        Tidy table returned by tidy_imports, with rows for CHINA and EXTRA_EU.
    measure : str, default "tonnes"
        Column used for the share: "tonnes" or "value_eur".

    Returns
    -------
    pandas.DataFrame
        Table with columns "reporter", "product", "period", "china_share".
    """
    by_partner = table.pivot(
        index=["reporter", "product", "period"],
        columns="partner",
        values=measure,
    ).reset_index()
    by_partner.columns.name = None  # drop the "partner" label left by pivot

    share = by_partner[CHINA] / by_partner[EXTRA_EU]
    by_partner = by_partner.assign(china_share=share)

    return by_partner[["reporter", "product", "period", "china_share"]]


def hhi(table, measure="tonnes"):
    """
    Compute the Herfindahl-Hirschman index of the extra-EU suppliers.

    The index is the sum of the squared shares of all suppliers, in percent.
    It goes from close to 0 (many small suppliers) to 10,000 (one supplier).

    Parameters
    ----------
    table : pandas.DataFrame
        Tidy table returned by tidy_imports, with one row per partner.
    measure : str, default "tonnes"
        Column used for the shares: "tonnes" or "value_eur".

    Returns
    -------
    pandas.DataFrame
        Table with columns "reporter", "product", "period", "hhi".
    """
    groups = ["reporter", "product", "period"]

    # Keep only single countries outside the EU: no EU members, no totals.
    excluded = EU_MEMBERS + [EXTRA_EU, INTRA_EU]
    suppliers = table[~table["partner"].isin(excluded)]

    # transform repeats each group total on every row, so we can divide.
    total = suppliers.groupby(groups)[measure].transform("sum")
    share = suppliers[measure] / total
    suppliers = suppliers.assign(squared=(share * 100) ** 2)

    index = suppliers.groupby(groups)["squared"].sum()
    return index.reset_index(name="hhi")

def trend(table, column):
    """
    Fit a least-squares line to a column over the years.

    Parameters
    ----------
    table : pandas.DataFrame
        Table with a "period" column of years, with one row per year: a single
        series, i.e. one reporter and one product.
    column : str
        Column to study, e.g. "china_share" or "hhi".

    Returns
    -------
    scipy.stats LinregressResult
        Result of linregress: slope (change per year, in the unit of column),
        intercept, rvalue and pvalue.

    Raises
    ------
    ValueError
        If a year appears more than once.
    """
    # A repeated year means that several series are mixed in the table.
    if table["period"].duplicated().any():
        raise ValueError(
            "Each year must appear once: filter one reporter and one product."
        )

    # Periods are labels in the tables, but the line needs numbers.
    year = table["period"].astype(int)
    return stats.linregress(year, table[column])

def year_over_year(table, measure="tonnes"):
    """
    Compute the change of monthly imports from the same month a year before.

    Parameters
    ----------
    table : pandas.DataFrame
        Tidy table of monthly data returned by tidy_imports, with rows for
        CHINA and EXTRA_EU, one reporter and one product. The months must be
        consecutive, without gaps.
    measure : str, default "tonnes"
        Column used for the change: "tonnes" or "value_eur".

    Returns
    -------
    pandas.DataFrame
        Changes in percent, with "period" as index and the columns CHINA,
        EXTRA_EU and "other" (all extra-EU suppliers but China). The first
        12 months are NaN, since they have no year before.

    Raises
    ------
    ValueError
        If a month appears more than once for the same partner.
    """
    # A repeated month means that several series are mixed in the table.
    if table[["partner", "period"]].duplicated().any():
        raise ValueError(
            "Each month must appear once: filter one reporter and one product."
        )

    by_partner = table.pivot(index="period", columns="partner", values=measure)
    by_partner = by_partner.assign(
        other=by_partner[EXTRA_EU] - by_partner[CHINA]
    )

    # pct_change counts rows: with one row per month, 12 rows back is the
    # same month of the year before, which also removes seasonality.
    return by_partner.pct_change(12) * 100
