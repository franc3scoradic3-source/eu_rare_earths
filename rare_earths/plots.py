"""
Draw the charts of the analysis: matplotlib for the charts, Plotly for
the interactive map.
"""

import matplotlib.pyplot as plt
import plotly.express as px
from matplotlib.colors import to_rgba
from matplotlib.ticker import PercentFormatter

from rare_earths.metrics import CHINA, trend

# Red for China, in every chart.
CHINA_COLOR = "#D62828"
CHINA_LIGHT = "#E6A39B"
# Grey for the reference lines, so that they don't hide the data.
REFERENCE_COLOR = "gray"
# A mid grey for the secondary texts, readable on light and dark pages.
TEXT_COLOR = "#8A8A8A"
# Critical Raw Materials Act: at most 65% from a single third country.
CRMA_LIMIT = 65
# Above 2,500 the market is highly concentrated.
HHI_CONCENTRATED = 2500
# ISO codes with three letters, the ones that Plotly uses for maps.
ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CY": "CYP", "CZ": "CZE",
    "DE": "DEU", "DK": "DNK", "EE": "EST", "ES": "ESP", "FI": "FIN",
    "FR": "FRA", "GR": "GRC", "HR": "HRV", "HU": "HUN", "IE": "IRL",
    "IT": "ITA", "LT": "LTU", "LU": "LUX", "LV": "LVA", "MT": "MLT",
    "NL": "NLD", "PL": "POL", "PT": "PRT", "RO": "ROU", "SE": "SWE",
    "SI": "SVN", "SK": "SVK",
}
# English names of the countries, shown on the map.
COUNTRY_NAMES = {
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "CY": "Cyprus",
    "CZ": "Czechia", "DE": "Germany", "DK": "Denmark", "EE": "Estonia",
    "ES": "Spain", "FI": "Finland", "FR": "France", "GR": "Greece",
    "HR": "Croatia", "HU": "Hungary", "IE": "Ireland", "IT": "Italy",
    "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia", "MT": "Malta",
    "NL": "Netherlands", "PL": "Poland", "PT": "Portugal", "RO": "Romania",
    "SE": "Sweden", "SI": "Slovenia", "SK": "Slovakia",
}



def style_axes(ax, title, subtitle):
    """
    Give a chart the common style of the project.

    The frame is removed, the tick labels are grey and away from the
    chart, and the title is on the left, with a subtitle below it.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The chart to style.
    title : str
        The message of the chart.
    subtitle : str
        What the chart measures.
    """
    ax.spines[:].set_visible(False)
    ax.tick_params(colors=TEXT_COLOR, length=0, pad=10)
    ax.set_title(
        title,
        loc="left",
        fontsize=13,
        fontweight="bold",
        # The colour of the text set by the notebook or the app.
        color=plt.rcParams["text.color"],
        pad=24,
    )
    # In axes coordinates, (0, 1.03) is just above the top-left corner.
    ax.text(0, 1.03, subtitle, transform=ax.transAxes, color=TEXT_COLOR)


def plot_china_share(shares, title):
    """
    Plot China's share of extra-EU imports against the rest of the world.

    China and the rest of the world are stacked areas, which always add
    up to 100%, with the limit of the Critical Raw Materials Act.

    Parameters
    ----------
    shares : pandas.DataFrame
        Table returned by china_share, with one reporter and one product.
    title : str
        The message of the chart.

    Returns
    -------
    matplotlib.figure.Figure
        The chart.
    """
    year = shares["period"].astype(int)
    china = shares["china_share"] * 100
    first, last = year.min(), year.max()

    fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
    ax.stackplot(
        year,
        china,
        100 - china,
        # The rest of the world in the light grey of the shaded areas.
        colors=[CHINA_COLOR, to_rgba(REFERENCE_COLOR, 0.1)],
        edgecolor="white",
        linewidth=1.5,
    )

    # The limit of the Critical Raw Materials Act.
    ax.axhline(CRMA_LIMIT, color="white", linestyle="--", linewidth=1.2)
    ax.text(
        last - 0.3,
        CRMA_LIMIT - 5,
        "EU target: max 65% from one country",
        color="white",
        fontsize=12,
        ha="right",
    )

    # At half of the lowest share, CHINA stays inside the red area.
    ax.text(
        (first + last) / 2,
        china.min() / 2,
        "CHINA",
        color="white",
        fontsize=20,
        fontweight="bold",
        ha="center",
        va="center",
    )
    ax.text(
        first + 0.5,
        (china.iloc[0] + 100) / 2,
        "REST OF THE WORLD",
        color=REFERENCE_COLOR,
        fontsize=13,
        fontweight="bold",
        va="center",
    )

    # China's share in the first and last year, on the border.
    ax.plot(
        [first, last],
        [china.iloc[0], china.iloc[-1]],
        "o",
        color="white",
        clip_on=False,
    )
    ax.text(
        first + 0.2,
        china.iloc[0] - 5,
        f"{china.iloc[0]:.0f}% in {first}",
        color="white",
        fontweight="bold",
    )
    ax.text(
        last - 0.2,
        china.iloc[-1] - 5,
        f"{china.iloc[-1]:.0f}% in {last}",
        color="white",
        fontweight="bold",
        ha="right",
    )

    ax.set_xticks(year)
    ax.set_xlim(first, last)
    ax.set_ylim(0, 100)
    # No 0%: the areas clearly start from the bottom.
    ax.set_yticks([25, 50, 75, 100])
    ax.yaxis.set_major_formatter(PercentFormatter())
    style_axes(
        ax,
        title,
        "Where the EU buys its permanent magnets: "
        f"China vs the rest of the world, {first}–{last}",
    )

    return fig


def plot_hhi(index, title):
    """
    Plot the Herfindahl-Hirschman index of the suppliers over the years.

    The index is drawn with its linear trend, over the zone of highly
    concentrated markets.

    Parameters
    ----------
    index : pandas.DataFrame
        Table returned by hhi, with one reporter and one product.
    title : str
        The message of the chart.

    Returns
    -------
    matplotlib.figure.Figure
        The chart.
    """
    year = index["period"].astype(int)
    fit = trend(index, "hhi")
    first, last = year.min(), year.max()

    fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")

    # The zone of highly concentrated markets.
    ax.axhspan(
        HHI_CONCENTRATED,
        10000,
        color=CHINA_LIGHT,
        alpha=0.25,
        linewidth=0,
    )
    ax.text(
        first,
        HHI_CONCENTRATED + 150,
        "Highly concentrated: above 2,500",
        color=REFERENCE_COLOR,
        fontsize=12,
    )

    # The trend line, dashed, below the index.
    ax.plot(
        year,
        fit.intercept + fit.slope * year,
        color=CHINA_COLOR,
        linestyle="--",
        linewidth=1.2,
    )
    ax.plot(year, index["hhi"], color=CHINA_COLOR, linewidth=3)

    # How much the index grows every year, above the last value.
    ax.text(
        last,
        index["hhi"].iloc[-1] + 400,
        f"+{fit.slope:.0f} per year",
        color=CHINA_COLOR,
        fontweight="bold",
        ha="right",
    )

    # A light baseline at 0, since the frame is removed.
    ax.axhline(0, color="darkgray", linewidth=1, clip_on=False)
    ax.set_xticks(year)
    ax.set_xlim(first, last)
    ax.set_ylim(0, 10000)
    ax.set_yticks([x * 1250 for x in range(1, 9)])
    style_axes(
        ax,
        title,
        "Herfindahl-Hirschman index of extra-EU suppliers "
        f"(10,000 = a single supplier), {first}–{last}",
    )

    return fig


def plot_monthly(monthly, title, highlight="2025"):
    """
    Plot the monthly imports from China, one line per year.

    The highlighted year is red, the others grey, with the months of the
    April 2025 licences shaded and two events marked.

    Parameters
    ----------
    monthly : pandas.DataFrame
        Tidy table of monthly data returned by tidy_imports, with one
        reporter and one product.
    title : str
        The message of the chart.
    highlight : str, default "2025"
        Year drawn in red.

    Returns
    -------
    matplotlib.figure.Figure
        The chart.
    """
    china = monthly[monthly["partner"] == CHINA]
    year = china["period"].str[:4]
    month = china["period"].str[5:].astype(int)
    tonnes = china.set_index("period")["tonnes"]

    fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")

    # The first months of the licences, when few were granted.
    ax.axvspan(4, 8, color=REFERENCE_COLOR, alpha=0.1, linewidth=0)
    ax.text(
        6,
        2550,
        f"{highlight}: licence bottleneck",
        color=REFERENCE_COLOR,
        ha="center",
    )

    for one_year in sorted(year.unique()):
        rows = year == one_year
        if one_year == highlight:
            color, width = CHINA_COLOR, 3.5
        else:
            color, width = "#BBBBBB", 1.5
        ax.plot(
            month[rows],
            china.loc[rows, "tonnes"],
            color=color,
            linewidth=width,
        )
        # The year on the left of its line: in January the lines are apart.
        ax.text(
            0.85,
            china.loc[rows, "tonnes"].iloc[0],
            one_year,
            color=color,
            fontweight="bold" if one_year == highlight else "normal",
            ha="right",
            va="center",
        )

    # Two events of 2025: the talks in London and the new controls.
    ax.plot(
        [6, 10],
        [tonnes["2025-06"], tonnes["2025-10"]],
        "o",
        color=CHINA_COLOR,
    )
    ax.text(
        6,
        tonnes["2025-06"] - 230,
        "London talks",
        color=CHINA_COLOR,
        ha="center",
    )
    ax.text(
        10,
        tonnes["2025-10"] + 120,
        "New controls",
        color=CHINA_COLOR,
        ha="center",
    )

    ax.axhline(0, color="darkgray", linewidth=1, clip_on=False)
    ax.set_xticks(
        range(1, 13),
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    )
    ax.set_xlim(0.3, 12.2)
    ax.set_ylim(0, 2700)
    style_axes(
        ax,
        title,
        "Rare-earth magnets imported each month from China, tonnes",
    )

    return fig

def plot_country_map(table, column, title):
    """
    Draw an interactive map of the EU countries, coloured by one column.

    Parameters
    ----------
    table : pandas.DataFrame
        One row per country, with a "reporter" column (Eurostat codes).
    column : str
        Column that gives the colour, e.g. "china_share_pct", "imports_meur"
        or "exposure".
    title : str
        The message of the map.

    Returns
    -------
    plotly.graph_objects.Figure
        The map: the values appear with the mouse over a country.
    """
    table = table.assign(
        iso3=table["reporter"].map(ISO3),
        country=table["reporter"].map(COUNTRY_NAMES),
    )

    fig = px.choropleth(
        table,
        locations="iso3",
        color=column,
        hover_name="country",
        # From light to dark red: no white, so that low values are not
        # confused with the grey countries outside the analysis.
        color_continuous_scale=[CHINA_LIGHT, CHINA_COLOR, "#7A1414"],
        scope="europe",
    )
    # All of Europe, with the countries outside the analysis in grey.
    fig.update_geos(
        projection_type="mercator",
        lonaxis_range=[-25, 45],
        lataxis_range=[34, 68],
        showland=True,
        landcolor="#B5B5B5",
        showocean=False,
        bgcolor="rgba(0, 0, 0, 0)",
        showcountries=True,
        countrycolor="white",
        showcoastlines=False,
        showframe=False,
    )
    fig.update_traces(marker_line_color="white", marker_line_width=0.8)
    fig.update_layout(
        title={"text": title, "x": 0},
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
        height=600,
        # Transparent, so that the map takes the colour of the page.
        paper_bgcolor="rgba(0, 0, 0, 0)",
        coloraxis_colorbar={"thickness": 12, "len": 0.6, "title": ""},
    )

    return fig
