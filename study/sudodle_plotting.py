import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from sudodle_simulation import (
    standardize_tile_tuple,
    cyclic_latin_square,
    parse_puzzles_from_txt,
)


def plot_puzzle(N, well_placed_tiles):
    """Plot the cyclic latin square with Matplotlib and highlight
    the well placed tiles in green."""
    grid = cyclic_latin_square(N)
    fig, ax = plt.subplots(figsize=(N, N))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, N)
    ax.set_ylim(0, N)
    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", linewidth=0.5, color="gray")
    tile_coordinates = [(i, j) for i in range(N) for j in range(N)]
    # Draw grid lines
    for i in range(N + 1):
        ax.axhline(y=i, color="black", linewidth=1)
        ax.axvline(x=i, color="black", linewidth=1)
    for i, j in tile_coordinates:
        if (i, j) in well_placed_tiles:
            color = "white"
            ax.add_patch(plt.Rectangle((j, N - i - 1), 1, 1, facecolor="darkgreen"))
        else:
            color = "lightgrey"
        ax.text(
            x=j + 0.5,
            y=N - i - 0.55,
            s=grid[i][j],
            ha="center",
            va="center",
            fontsize=36,
            fontfamily="EB Garamond",
            color=color,
        )

    return ax


def plot_puzzles_pdf_from_txt(puzzles, grid_size, target_file=None):
    with PdfPages(target_file) as pdf:
        for tiles in puzzles:
            ax = plot_puzzle(grid_size, tiles)  # Use the correct N parameter
            pdf.savefig(ax.figure, bbox_inches="tight")
            plt.close(ax.figure)


def plot_simulation_histogram(tries_list, ax, title):
    """Run simulations in parallel with timeout handling"""

    # Only plot if we have valid results
    if tries_list:
        ax.hist(
            tries_list, bins=range(1, max(tries_list) + 1), align="left", density=True
        )
        ax.set_title(f"{title}")
        ax.set_xlabel("Guesses needed")
        ax.set_ylabel("Frequency")
        ax.set_xlim(0.5, 5.5)
        ax.set_xticks(range(1, max(tries_list) + 1))
        ax.set_yticks(range(0, 1 + 1))
        ax.set_ylim(0, 1.05)
    else:
        ax.text(
            0.5,
            0.5,
            "No successful simulations",
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
        )
        ax.set_title(f"{title}")
        ax.set_xlabel("Tries to victory")
        ax.set_ylabel("Frequency")
