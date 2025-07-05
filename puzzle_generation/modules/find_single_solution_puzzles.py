import itertools
from tqdm.auto import tqdm

from .utils import standardize_tile_tuple
from .solve_sudodle_semi_optimized import complete_latin_square_backtrack_all_solutions


def find_single_solution_puzzles(grid, n_well_placed):
    """
    Find all puzzles with a single solution for a given grid and number of well placed tiles.

    Parameters:
        grid (list): The grid to find puzzles for.
        n_well_placed (int): The number of well placed tiles.

    Returns:
        list: A list of tuples, each containing the selected tiles and the solution.
    """
    standard_tile_tuples = set()
    N = len(grid)
    tile_coordinates = [(i, j) for i in range(N) for j in range(N)]
    selected_solutions = []
    for selected_tiles in tqdm(itertools.combinations(tile_coordinates, n_well_placed)):
        standardized_tiles = standardize_tile_tuple(N, selected_tiles)
        if standardized_tiles in standard_tile_tuples:
            continue
        standard_tile_tuples.add(standardized_tiles)
        known_values = {}
        known_wrong_values = {}
        for i, j in tile_coordinates:
            if (i, j) in selected_tiles:
                known_values[(i, j)] = grid[i][j]
            else:
                known_wrong_values[(i, j)] = [grid[i][j]]
        result = complete_latin_square_backtrack_all_solutions(
            N, known_values, known_wrong_values, max_solutions=2
        )
        solutions, branches = result
        if len(solutions) == 1:
            selected_solutions.append((selected_tiles, solutions[0]))
    return selected_solutions
