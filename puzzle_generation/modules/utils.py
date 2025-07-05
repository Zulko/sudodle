"""
Sudodle Simulation - Latin Square Generation and Game Simulation

This module provides functions for generating Latin squares using various methods,
completing partial Latin squares with constraints, and simulating a Sudoku-like
game where players try to guess a Latin square.

A Latin square is an n×n array filled with n different symbols, each occurring
exactly once in each row and exactly once in each column.

Functions:
    - backtracked_random_latin_square: Generate random Latin squares using backtracking
    - cyclic_latin_square: Generate the basic cyclic Latin square
    - uniform_random_latin_square: Generate uniformly random Latin squares using Markov chains
    - complete_latin_square_backtrack: Complete partial Latin squares with constraints
    - compare_squares: Compare two squares to find matches and differences
    - display_square: Pretty-print a Latin square
    - simulate_game: Run a complete game simulation

"""

import random
from tqdm.auto import tqdm
import itertools


def cyclic_latin_square(N):
    """
    Generate the basic cyclic Latin square of order N.

    A cyclic Latin square is constructed using the formula: L[i][j] = (i + j) mod N + 1
    This is guaranteed to be a valid Latin square for any positive integer N.

    Parameters:
        N (int): Order of the Latin square (number of rows/columns).

    Returns:
        List[List[int]]: An N×N cyclic Latin square with values 1..N.

    Example:
        >>> square = cyclic_latin_square(3)
        >>> square
        [[1, 2, 3], [2, 3, 1], [3, 1, 2]]

    Note:
        This is often used as a starting point for generating more random
        Latin squares through transformations.
    """
    return [[(i + j) % N + 1 for j in range(N)] for i in range(N)]


def compare_squares(square, expected_square):
    """
    Compare two Latin squares and identify correct and incorrect values.

    This function compares each cell of two squares and categorizes the values
    as either correct (matching) or incorrect (different).

    Parameters:
        square (List[List[int]]): The first square to compare (typically a guess).
        expected_square (List[List[int]]): The second square to compare against
            (typically the solution).

    Returns:
        tuple: A tuple containing two lists:
            - right_values: List of tuples (row, col, value) for matching cells
            - wrong_values: List of tuples (row, col, value) for non-matching cells

    Example:
        >>> guess = [[1, 2], [2, 1]]
        >>> solution = [[1, 2], [2, 3]]
        >>> right, wrong = compare_squares(guess, solution)
        >>> right
        [(0, 0, 1), (0, 1, 2), (1, 0, 2)]
        >>> wrong
        [(1, 1, 1)]

    Note:
        This function assumes both squares have the same dimensions.
        It's primarily used in game simulation to provide feedback on guesses.
    """
    right_values = []
    wrong_values = []

    for i in range(len(square)):
        for j in range(len(square[i])):
            if square[i][j] == expected_square[i][j]:
                right_values.append((i, j, square[i][j]))
            else:
                wrong_values.append((i, j, square[i][j]))

    return (right_values, wrong_values)


def random_square(n):
    """Return a random nxn square with n ones, n twos, etc."""
    numbers = [(i + 1) for i in range(n) for _ in range(n)]
    random.shuffle(numbers)
    return [numbers[i * n : (i + 1) * n] for i in range(n)]


def standardize_tile_tuple(correct_tiles):
    return min(
        [
            tuple(sorted(correct_tiles)),
            tuple(sorted((j, i) for i, j in correct_tiles)),
        ]
    )
