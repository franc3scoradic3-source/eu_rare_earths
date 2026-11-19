"""
Measure how much EU imports depend on China.
"""

# Comext code of China as a partner: the numerator of the share.
CHINA = "CN"
# Comext code of all countries outside the EU, China included: the denominator.
EXTRA_EU = "EXT_EU"


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
        Table with columns "product", "period", "china_share".
    """
    by_partner = table.pivot(
        index=["product", "period"],
        columns="partner",
        values=measure,
    ).reset_index()
    by_partner.columns.name = None  # drop the "partner" label left by pivot

    share = by_partner[CHINA] / by_partner[EXTRA_EU]
    by_partner = by_partner.assign(china_share=share)

    return by_partner[["product", "period", "china_share"]]
