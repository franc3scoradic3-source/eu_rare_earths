"""
Measure how much EU imports depend on China.
"""

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
