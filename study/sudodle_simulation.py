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
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm.auto import tqdm
import itertools


def backtracked_random_latin_square(N, seed=None, timeout=None):
    """
    Generate a single N×N Latin square in a reproducible (pseudo-random) way.

    This function uses backtracking with randomized value selection to generate
    a valid Latin square. The randomization ensures different squares are generated
    with different seeds, while the same seed produces the same square.

    Parameters:
        N (int): Order of the Latin square (number of rows/columns).
        seed (int or None): Seed for the random number generator. If provided,
            results will be deterministic for the same (N, seed) pair.

    Returns:
        List[List[int]]: An N×N Latin square (each row and each column is a
        permutation of 1..N). If no square is found (extremely unlikely
        for reasonable N), returns None.

    Example:
        >>> square = backtracked_random_latin_square(3, seed=42)
        >>> len(square)
        3
        >>> len(square[0])
        3
        >>> set(square[0]) == {1, 2, 3}
        True

    Note:
        Values in the returned square are 1-indexed (1 to N), not 0-indexed.
    """
    rng = random.Random(seed)

    # Prepare the empty square and bitmasks for row/column usage
    square = [[-1] * N for _ in range(N)]
    row_used = [0] * N  # row_used[i] has bit v set iff v+1 is already in row i
    col_used = [0] * N  # col_used[j] has bit v set iff v+1 is already in column j
    full_mask = (1 << N) - 1  # bits 0..N-1 all set
    initial_time = time.time()

    def backtrack(cell=0):
        if timeout is not None:
            if time.time() - initial_time > timeout:
                raise TimeoutError("Backtracking timed out")
        # cell runs from 0..N*N-1 in row-major order
        if cell == N * N:
            return True  # filled every cell successfully

        i, j = divmod(cell, N)

        # Compute which values are still available at (i,j)
        used = row_used[i] | col_used[j]
        avail_mask = full_mask & ~used

        # If no available symbol, backtrack
        if avail_mask == 0:
            return False

        # Build a list of all available values and shuffle it
        candidates = []
        m = avail_mask
        while m:
            bit = m & -m
            m -= bit
            v = bit.bit_length() - 1
            candidates.append(v + 1)  # Add 1 to get numbers 1..N
        rng.shuffle(candidates)

        # Try each candidate in randomized order
        for v in candidates:
            bit = 1 << (v - 1)  # Subtract 1 for bitmask operations
            square[i][j] = v
            row_used[i] |= bit
            col_used[j] |= bit

            if backtrack(cell + 1):
                return True  # once one full square is found, stop

            # undo placement
            row_used[i] ^= bit
            col_used[j] ^= bit
            square[i][j] = -1

        return False

    success = backtrack(0)
    return square if success else None


def backtracked_random_latin_square_with_timeout_retries(N, seed=None, timeout=1):
    while True:
        try:
            return backtracked_random_latin_square(N, seed, timeout=timeout)
        except TimeoutError:
            pass


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


def _random_intercalate_step(L, rng):
    """
    Attempt one random intercalate swap on a Latin square in place.

    This function implements one step of the Jacobson-Matthews algorithm for
    generating uniformly random Latin squares. It looks for a 2×2 submatrix
    of the form [[a,b],[b,a]] and swaps it to [[b,a],[a,b]].

    Parameters:
        L (List[List[int]]): The Latin square to modify in place.
        rng (random.Random): Random number generator to use for selection.

    Returns:
        bool: True if a swap was performed, False if no valid swap was found.

    Algorithm:
        1. Pick two distinct rows r1, r2 and two distinct columns c1, c2 at random
        2. Check if the 2×2 submatrix at these positions has the intercalate pattern
        3. If so, swap the values to maintain the intercalate property
        4. Return whether a swap was performed

    Note:
        This is a helper function for uniform_random_latin_square and should
        not typically be called directly.
    """
    N = len(L)
    r1, r2 = rng.sample(range(N), 2)
    c1, c2 = rng.sample(range(N), 2)

    a = L[r1][c1]
    b = L[r1][c2]
    if a == b:
        return False
    if L[r2][c1] == b and L[r2][c2] == a:
        # We have an intercalate [[a,b],[b,a]], so flip:
        L[r1][c1], L[r1][c2] = b, a
        L[r2][c1], L[r2][c2] = a, b
        return True

    return False


def uniform_random_latin_square(N, seed=None, burn_in_steps=None):
    """
    Generate a (nearly) uniformly random Latin square of order N.

    Uses the Jacobson–Matthews "intercalate‐flip" Markov chain to generate
    Latin squares that are approximately uniformly distributed over all
    possible Latin squares of the given order.

    Parameters:
        N (int): Order of the Latin square (number of rows/columns).
        seed (int or None): Seed for the random number generator. If provided,
            results will be deterministic for the same (N, seed) pair.
        burn_in_steps (int or None): Number of random intercalate flips to perform
            before returning the square. If None, defaults to 50 * N².

    Returns:
        List[List[int]]: An N×N Latin square with values 1..N that is approximately
        uniformly distributed over all possible Latin squares.

    Example:
        >>> square = uniform_random_latin_square(4, seed=123)
        >>> len(square)
        4
        >>> all(len(row) == 4 for row in square)
        True

    Algorithm:
        1. Start with a cyclic Latin square
        2. Perform many random intercalate flips
        3. Return the resulting square

    Note:
        The "burn-in" period ensures the Markov chain has converged to its
        stationary distribution, giving approximately uniform sampling.
    """
    rng = random.Random(seed)
    L = backtracked_random_latin_square_with_timeout_retries(N, seed=seed, timeout=1)

    if burn_in_steps is None:
        burn_in_steps = 50 * (N**2)

    for _ in range(burn_in_steps):
        # Try an intercalate‐flip; if it's not valid, we simply continue.
        _random_intercalate_step(L, rng)

    # At this point, L is (approximately) a uniform sample.
    return L


def complete_latin_square_backtrack_all_solutions(
    size=5,
    known_values={},
    known_wrong_values={},
    timeout=2,
    max_solutions=None,
):
    """
    Find all completions of a partial Latin square using optimized backtracking with constraints.

    This function takes a partially filled Latin square with known correct values
    and known incorrect values, then uses backtracking with the Most Constrained
    Variable (MCV) heuristic to find all valid completions.

    Parameters:
        size (int): Size of the Latin square (N×N). Default is 5.
        known_values (dict): Dictionary mapping (row, col) tuples to known correct
            values. Example: {(0, 1): 3, (2, 0): 1} means cell (0,1) must be 3
            and cell (2,0) must be 1.
        known_wrong_values (dict): Dictionary mapping (row, col) tuples to lists
            of values that are known to be wrong for that cell.
            Example: {(0, 0): [1, 2]} means cell (0,0) cannot be 1 or 2.
        timeout (float): Maximum time to spend searching (in seconds). Default is 2.
        max_solutions (int or None): Maximum number of solutions to find. If None,
            finds all solutions. If set, stops when this many solutions are found.

    Returns:
        List[List[List[int]]]: A list of completed N×N Latin squares with values 1 to N.
        Returns empty list if no valid completion exists.

    Example:
        >>> # Find all completions of a 3×3 square with some known values
        >>> known = {(0, 0): 1, (1, 1): 2}
        >>> wrong = {(0, 1): [1, 3]}
        >>> solutions = complete_latin_square_backtrack_all_solutions(3, known, wrong, max_solutions=5)
        >>> len(solutions)  # Number of solutions found (up to 5)
        3

    Algorithm:
        1. Initialize square with known values
        2. Use MCV heuristic to select the most constrained empty cell
        3. Try all valid values for that cell
        4. Recursively solve the remaining cells
        5. When a complete solution is found, save it and continue searching
        6. Stop when max_solutions is reached or all possibilities are exhausted

    Note:
        The MCV heuristic significantly improves performance by tackling
        the most constrained cells first, reducing the search space.
    """
    # Initialize the square with -1 for unknown cells
    square = [[-1] * size for _ in range(size)]
    initial_time = time.time()
    solutions = []

    # Fill in known values
    for (i, j), value in known_values.items():
        if 0 <= i < size and 0 <= j < size and 1 <= value <= size:
            square[i][j] = value

    # Create bitmasks for tracking used values in rows and columns
    row_used = [0] * size  # row_used[i] has bit v-1 set iff value v is in row i
    col_used = [0] * size  # col_used[j] has bit v-1 set iff value v is in column j
    full_mask = (1 << size) - 1  # bits 0..size-1 all set

    # Initialize bitmasks based on known values
    for i in range(size):
        for j in range(size):
            if square[i][j] != -1:
                value = square[i][j]
                bit = 1 << (value - 1)  # Convert to 0-based for bitmask
                row_used[i] |= bit
                col_used[j] |= bit

    def get_available_values(i, j):
        """Get list of available values for cell (i, j)"""
        if square[i][j] != -1:
            return []  # Cell already filled

        # Values already used in this row or column
        used = row_used[i] | col_used[j]
        avail_mask = full_mask & ~used

        # Build list of available values
        candidates = []
        m = avail_mask
        while m:
            bit = m & -m
            m -= bit
            v = bit.bit_length()  # Convert back to 1-based
            candidates.append(v)

        # Remove values that are known to be wrong for this cell
        if (i, j) in known_wrong_values:
            wrong_values_set = set(known_wrong_values[(i, j)])
            candidates = [v for v in candidates if v not in wrong_values_set]

        return candidates

    def find_most_constrained_cell():
        """Find empty cell with fewest possible values (MCV heuristic)"""
        best_cell = None
        min_choices = size + 1

        for i in range(size):
            for j in range(size):
                if square[i][j] == -1:  # Empty cell
                    choices = len(get_available_values(i, j))
                    if choices == 0:
                        return (i, j), 0  # Dead end - return immediately
                    if choices < min_choices:
                        min_choices = choices
                        best_cell = (i, j)
                        if choices == 1:
                            return best_cell, 1  # Can't get better than 1 choice

        return best_cell, min_choices

    def is_valid_partial():
        """Quick validity check - ensure no empty cell has zero possibilities"""
        for i in range(size):
            for j in range(size):
                if square[i][j] == -1 and len(get_available_values(i, j)) == 0:
                    return False
        return True

    def backtrack():
        if timeout is not None:
            if time.time() - initial_time > timeout:
                raise TimeoutError("Backtracking timed out")

        # Check if we've found enough solutions
        if max_solutions is not None and len(solutions) >= max_solutions:
            return

        # Find the most constrained empty cell
        cell, num_choices = find_most_constrained_cell()

        if cell is None:
            # All cells filled successfully - save this solution
            solution = [row[:] for row in square]  # Deep copy
            solutions.append(solution)
            return

        if num_choices == 0:
            return  # Dead end

        i, j = cell
        candidates = get_available_values(i, j)

        # Try each candidate value
        for value in candidates:
            # Early termination check
            if max_solutions is not None and len(solutions) >= max_solutions:
                return

            bit = 1 << (value - 1)

            # Place the value
            square[i][j] = value
            row_used[i] |= bit
            col_used[j] |= bit

            # Quick validity check before deeper recursion
            if is_valid_partial():
                backtrack()

            # Backtrack: remove the value
            square[i][j] = -1
            row_used[i] ^= bit
            col_used[j] ^= bit

    # Validate that known values don't violate Latin square constraints
    for i in range(size):
        row_values = [square[i][j] for j in range(size) if square[i][j] != -1]
        if len(row_values) != len(set(row_values)):
            return []  # Duplicate values in row

    for j in range(size):
        col_values = [square[i][j] for i in range(size) if square[i][j] != -1]
        if len(col_values) != len(set(col_values)):
            return []  # Duplicate values in column

    # Initial validity check
    if not is_valid_partial():
        return []

    # Try to find all completions
    try:
        backtrack()
        return solutions
    except TimeoutError:
        return solutions  # Return whatever solutions we found before timing out


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


def square_to_string(square):
    """
    Display a Latin square in a readable format.

    Prints the square to stdout with proper formatting, making it easy to
    visualize the structure and values.

    Parameters:
        square (List[List[int]]): The Latin square to display.

    Returns:
        None: This function prints directly to stdout.

    Example:
        >>> square = [[1, 2, 3], [2, 3, 1], [3, 1, 2]]
        >>> print(square_to_string(square))
        | 1 2 3
        | 2 3 1
        | 3 1 2

    Note:
        Each row is prefixed with "| " for better visual separation.
        Values are separated by single spaces.
    """
    return "\n".join("| " + " ".join(str(cell) for cell in row) for row in square)


def simulate_game(first_guess, verbose=False, solve_timeout=2):
    """
    Simulate a complete Sudodle game with up to 5 attempts.

    This function runs a complete game simulation where the player tries to guess
    a randomly generated Latin square. It starts with a cyclic square as the
    initial guess and uses feedback to improve subsequent guesses.

    Parameters:
        N (int): Order of the Latin square (N×N grid).

    Returns:
        None: This function prints the game progress to stdout.

    Game Flow:
        1. Generate a random solution Latin square
        2. Start with a cyclic Latin square as the first guess
        3. For each guess:
           - Display the current guess
           - Compare with the solution
           - If correct, announce victory
           - If incorrect, record correct and incorrect values
           - Generate a new guess incorporating the feedback
        4. Continue for up to 5 attempts

    Example:
        >>> simulate_game(3)
        solution:
        | 2 3 1
        | 3 1 2
        | 1 2 3

        guess:
        | 1 2 3
        | 2 3 1
        | 3 1 2
        Found 3 known values so far

        guess:
        | 2 3 1
        | 3 1 2
        | 1 2 3
        Found solution in 2 tries!

    Note:
        The game uses intelligent guessing by incorporating feedback from
        previous attempts, making it more likely to find the solution quickly.
    """

    def verbose_print(s):
        if verbose:
            print(s)

    N = len(first_guess)
    solution = uniform_random_latin_square(N)
    verbose_print("solution:\n" + square_to_string(solution))
    known_values = {}
    known_wrong_values = {}
    history_of_known_values = []

    guess = first_guess

    for _ in range(1, 6):
        verbose_print("\nguess:\n" + square_to_string(guess))
        right_values, wrong_values = compare_squares(guess, solution)
        history_of_known_values.append(len(known_values))
        if wrong_values == []:
            return history_of_known_values[1:]
        for i, j, value in right_values:
            known_values[(i, j)] = value
        for i, j, value in wrong_values:
            if (i, j) not in known_wrong_values:
                known_wrong_values[(i, j)] = []
            known_wrong_values[(i, j)].append(value)
        verbose_print(f"Found {len(known_values)} known values so far")
        guess = complete_latin_square_backtrack(
            N, known_values, known_wrong_values, timeout=solve_timeout
        )
        if guess is None:
            return None


def random_square(n):
    numbers = [(i + 1) for i in range(n) for _ in range(n)]
    random.shuffle(numbers)
    return [numbers[i * n : (i + 1) * n] for i in range(n)]


def run_multiple_simulations_in_parallel(first_guesses, n_processes=10):
    with ProcessPoolExecutor(n_processes) as executor:
        futures = [
            executor.submit(simulate_game, first_guess) for first_guess in first_guesses
        ]
        results = []
        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result(timeout=2)
            results.append(result)
        return results


def complete_latin_square_backtrack(
    size=5,
    known_values={},
    known_wrong_values={},
    timeout=2,
):
    """
    Complete a partial Latin square using optimized backtracking with constraints.

    This is a convenience wrapper around complete_latin_square_backtrack_all_solutions
    that returns only the first solution found.

    Parameters:
        size (int): Size of the Latin square (N×N). Default is 5.
        known_values (dict): Dictionary mapping (row, col) tuples to known correct
            values. Example: {(0, 1): 3, (2, 0): 1} means cell (0,1) must be 3
            and cell (2,0) must be 1.
        known_wrong_values (dict): Dictionary mapping (row, col) tuples to lists
            of values that are known to be wrong for that cell.
            Example: {(0, 0): [1, 2]} means cell (0,0) cannot be 1 or 2.
        timeout (float): Maximum time to spend searching (in seconds). Default is 2.

    Returns:
        List[List[int]]: A completed N×N Latin square with values 1 to N,
        or None if no valid completion exists.
    """
    solutions = complete_latin_square_backtrack_all_solutions(
        size, known_values, known_wrong_values, timeout, max_solutions=1
    )
    return solutions[0] if solutions else None


def standardize_tile_tuple(N, correct_tiles):
    return min(
        [
            tuple(sorted(correct_tiles)),
            tuple(sorted((j, i) for i, j in correct_tiles)),
        ]
    )


def find_single_solution_puzzles(grid, n_well_placed):
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
        solutions = complete_latin_square_backtrack_all_solutions(
            N, known_values, known_wrong_values, max_solutions=2
        )
        if len(solutions) == 1:
            selected_solutions.append((selected_tiles, solutions[0]))
    return selected_solutions


if __name__ == "__main__":
    first_guess = cyclic_latin_square(5)
    tries = simulate_game(first_guess, verbose=True)
    print(f"Found solution in {len(tries) + 1} tries!")


def parse_puzzles_from_txt(txt_file, grid_size, standardize_tiles=True):
    with open(txt_file, "r") as f:
        lines = f.readlines()

    def parse_line(line):
        """Parse a line into coordinate tuples, handling potential format issues."""
        line = line.strip()
        if not line:  # Skip empty lines
            return None
        try:
            # Split by commas and clean up each coordinate pair
            coords = line.split(", ")
            # Convert each "(x,y)" string into a tuple of ints
            tiles = [tuple(map(int, coord.strip("()").split(","))) for coord in coords]
            return tiles
        except (ValueError, IndexError) as e:
            print(f"Warning: Could not parse line '{line}': {e}")
            return None

    puzzles = []
    seen_standardized_puzzles = set()
    for line in lines:
        tiles = parse_line(line)
        if tiles is not None:
            if standardize_tiles:
                standardized_tiles = standardize_tile_tuple(grid_size, tiles)
                if standardized_tiles not in seen_standardized_puzzles:
                    puzzles.append(tiles)
                    seen_standardized_puzzles.add(standardized_tiles)
            else:
                puzzles.append(tiles)
    return puzzles
