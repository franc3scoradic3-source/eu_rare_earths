"""
Draw the charts of the analysis with matplotlib.
"""

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

# Red for China and blue for Europe, in every chart.
CHINA_COLOR = "#D62828"
CHINA_LIGHT = "#E6A39B"
EU_COLOR = "#3A6BB5"
EU_LIGHT = "#9DB5DB"
# Grey for the reference lines, so that they don't hide the data.
REFERENCE_COLOR = "gray"
# Dark grey for titles and light grey for the other texts.
TITLE_COLOR = "#222222"
TEXT_COLOR = "#555555"
# Critical Raw Materials Act: at most 65% from a single third country.
CRMA_LIMIT = 65


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
        color=TITLE_COLOR,
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
        colors=[CHINA_COLOR, EU_COLOR],
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
        color="white",
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
