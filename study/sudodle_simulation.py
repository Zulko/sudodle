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
    Variable (MCV) heuristic and constraint propagation to find all valid completions.

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
        2. Use constraint propagation with bitmasks to track possible value placements
        3. Use MCV heuristic and naked singles detection to select the most constrained cell
        4. Try all valid values for that cell
        5. Recursively solve the remaining cells
        6. When a complete solution is found, save it and continue searching
        7. Stop when max_solutions is reached or all possibilities are exhausted

    Note:
        The enhanced algorithm uses bitmask tracking for efficient constraint propagation,
        significantly improving performance by quickly identifying naked singles and
        hidden singles.
    """
    # Initialize the square with -1 for unknown cells
    square = [[-1] * size for _ in range(size)]
    initial_time = time.time()
    solutions = []
    branches = []  # counts the times the most constrained cell has more than 1 choice

    # Fill in known values
    for (i, j), value in known_values.items():
        if 0 <= i < size and 0 <= j < size and 1 <= value <= size:
            square[i][j] = value

    # Create bitmasks for tracking used values in rows and columns
    row_used = [0] * size  # row_used[i] has bit v-1 set iff value v is in row i
    col_used = [0] * size  # col_used[j] has bit v-1 set iff value v is in column j
    full_mask = (1 << size) - 1  # bits 0..size-1 all set

    # NEW: Create bitmasks for tracking where each value can be placed
    # row_possible[i][v-1] has bit j set iff value v can be placed at (i,j)
    # col_possible[j][v-1] has bit i set iff value v can be placed at (i,j)
    row_possible = [[full_mask] * size for _ in range(size)]
    col_possible = [[full_mask] * size for _ in range(size)]

    # Initialize bitmasks based on known values and constraints
    for i in range(size):
        for j in range(size):
            if square[i][j] != -1:
                value = square[i][j]
                bit = 1 << (value - 1)  # Convert to 0-based for bitmask
                row_used[i] |= bit
                col_used[j] |= bit

                # This value can no longer be placed anywhere else in this row/column
                for k in range(size):
                    if k != j:
                        row_possible[i][value - 1] &= ~(1 << k)
                    if k != i:
                        col_possible[j][value - 1] &= ~(1 << k)

                # No other values can be placed at this position
                for v in range(size):
                    if v != value - 1:
                        row_possible[i][v] &= ~(1 << j)
                        col_possible[j][v] &= ~(1 << i)

    # Handle known wrong values
    for (i, j), wrong_values in known_wrong_values.items():
        for value in wrong_values:
            if 1 <= value <= size:
                # This value cannot be placed at (i,j)
                row_possible[i][value - 1] &= ~(1 << j)
                col_possible[j][value - 1] &= ~(1 << i)

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

    def popcount(x):
        """Count the number of set bits in x using Brian Kernighan's algorithm"""
        count = 0
        while x:
            x &= x - 1  # Clear the lowest set bit
            count += 1
        return count

    def find_single_bit_position(mask):
        """Find the position of the single set bit in mask (0-indexed)"""
        return (mask & -mask).bit_length() - 1

    def get_available_values_fast(i, j):
        """Fast version of get_available_values using only bitmasks"""
        if square[i][j] != -1:
            return []

        # Values already used in this row or column
        used = row_used[i] | col_used[j]

        # Get intersection of what's possible for this cell from row and column constraints
        available_mask = full_mask & ~used  # Exclude already used values
        for v in range(size):
            if not (row_possible[i][v] & (1 << j)) or not (
                col_possible[j][v] & (1 << i)
            ):
                available_mask &= ~(1 << v)

        # Convert mask to list
        candidates = []
        m = available_mask
        while m:
            bit = m & -m
            m -= bit
            v = bit.bit_length()  # Convert back to 1-based
            candidates.append(v)

        return candidates

    def propagate_constraints():
        """Propagate all forced moves (naked singles) until no more changes occur"""
        changed = True
        total_placements = 0

        while changed:
            changed = False

            # Find all naked singles (hidden singles in rows)
            for i in range(size):
                for v in range(size):
                    # Skip if this value is already used in this row
                    if row_used[i] & (1 << v):
                        continue
                    possible_mask = row_possible[i][v]
                    if possible_mask != 0 and popcount(possible_mask) == 1:
                        j = find_single_bit_position(possible_mask)
                        if square[i][j] == -1:
                            square[i][j] = v + 1
                            update_constraints_fast(i, j, v + 1)
                            changed = True
                            total_placements += 1

            # Find all naked singles (hidden singles in columns)
            for j in range(size):
                for v in range(size):
                    # Skip if this value is already used in this column
                    if col_used[j] & (1 << v):
                        continue
                    possible_mask = col_possible[j][v]
                    if possible_mask != 0 and popcount(possible_mask) == 1:
                        i = find_single_bit_position(possible_mask)
                        if square[i][j] == -1:  # Ensure cell is still empty
                            square[i][j] = v + 1
                            update_constraints_fast(i, j, v + 1)
                            changed = True
                            total_placements += 1

            # Find naked singles (cells with only one possibility)
            for i in range(size):
                for j in range(size):
                    if square[i][j] == -1:
                        candidates = get_available_values_fast(i, j)
                        if len(candidates) == 1:
                            value = candidates[0]
                            square[i][j] = value
                            update_constraints_fast(i, j, value)
                            changed = True
                            total_placements += 1
                        elif len(candidates) == 0:
                            return False  # Invalid state

        return total_placements

    def update_constraints_fast(i, j, value):
        """Fast constraint update without saving state"""
        bit = 1 << (value - 1)
        row_used[i] |= bit
        col_used[j] |= bit

        # This value can no longer be placed anywhere else in this row/column
        for k in range(size):
            if k != j:
                row_possible[i][value - 1] &= ~(1 << k)
            if k != i:
                col_possible[j][value - 1] &= ~(1 << k)

        # No other values can be placed at this position
        for v in range(size):
            if v != value - 1:
                row_possible[i][v] &= ~(1 << j)
                col_possible[j][v] &= ~(1 << i)

    def is_valid_state():
        """Fast validity check using bitmasks only"""
        # Check for impossible states
        for i in range(size):
            for j in range(size):
                if square[i][j] == -1:
                    if not get_available_values_fast(i, j):
                        return False

        # Check for values with no possible placements
        for i in range(size):
            for v in range(size):
                if not (row_used[i] & (1 << v)) and row_possible[i][v] == 0:
                    return False

        for j in range(size):
            for v in range(size):
                if not (col_used[j] & (1 << v)) and col_possible[j][v] == 0:
                    return False

        return True

    def is_valid_latin_square(square):
        """Check if a completed square is actually a valid Latin square"""
        # Check rows for duplicates
        for row in square:
            if len(set(row)) != size:
                return False

        # Check columns for duplicates
        for j in range(size):
            col = [square[i][j] for i in range(size)]
            if len(set(col)) != size:
                return False

        return True

    def find_most_constrained_cell():
        """Find empty cell with fewest possible values using enhanced heuristics"""
        best_cell = None
        min_choices = size + 1

        # Use a more sophisticated scoring system
        for i in range(size):
            for j in range(size):
                if square[i][j] == -1:
                    candidates = get_available_values_fast(i, j)
                    choices = len(candidates)

                    if choices == 0:
                        return (i, j), 0  # Dead end

                    if choices < min_choices:
                        min_choices = choices
                        best_cell = (i, j)
                        if choices == 1:
                            return best_cell, 1

        return best_cell, min_choices

    def save_state():
        """Save current state for backtracking"""
        return {
            "square": [row[:] for row in square],
            "row_used": row_used[:],
            "col_used": col_used[:],
            "row_possible": [
                [row_possible[i][v] for v in range(size)] for i in range(size)
            ],
            "col_possible": [
                [col_possible[j][v] for v in range(size)] for j in range(size)
            ],
        }

    def restore_state(state):
        """Restore state for backtracking"""
        nonlocal square, row_used, col_used, row_possible, col_possible
        # Fix: Properly restore the square contents, not just reassign the reference
        for i in range(size):
            for j in range(size):
                square[i][j] = state["square"][i][j]
        row_used[:] = state["row_used"]
        col_used[:] = state["col_used"]
        for i in range(size):
            for v in range(size):
                row_possible[i][v] = state["row_possible"][i][v]
        for j in range(size):
            for v in range(size):
                col_possible[j][v] = state["col_possible"][j][v]

    def backtrack():
        if timeout is not None:
            if time.time() - initial_time > timeout:
                raise TimeoutError("Backtracking timed out")

        # Check if we've found enough solutions
        if max_solutions is not None and len(solutions) >= max_solutions:
            return

        # Try constraint propagation first
        placements = propagate_constraints()
        if placements is False:
            return  # Invalid state after propagation

        # Check if puzzle is solved after propagation
        empty_cells = sum(
            1 for i in range(size) for j in range(size) if square[i][j] == -1
        )
        if empty_cells == 0:
            # All cells filled successfully - validate before saving
            solution = [row[:] for row in square]  # Deep copy
            if is_valid_latin_square(solution):
                solutions.append(solution)
            return

        # Find the most constrained empty cell
        cell, num_choices = find_most_constrained_cell()
        if num_choices > 1:
            branches.append(num_choices)

        if cell is None:
            # Should not happen after propagation, but just in case
            solution = [row[:] for row in square]  # Deep copy
            if is_valid_latin_square(solution):
                solutions.append(solution)
            return

        if num_choices == 0:
            return  # Dead end

        i, j = cell
        candidates = get_available_values_fast(i, j)

        # Order values by least constraining heuristic (try values that eliminate fewer possibilities first)
        def constraint_score(value):
            """Calculate how many possibilities this value would eliminate"""
            score = 0
            v = value - 1
            # Count constraints in the same row
            for k in range(size):
                if k != j and square[i][k] == -1:
                    if row_possible[i][v] & (1 << k):
                        score += 1
            # Count constraints in the same column
            for k in range(size):
                if k != i and square[k][j] == -1:
                    if col_possible[j][v] & (1 << k):
                        score += 1
            return score

        candidates.sort(key=constraint_score)

        # Try each candidate value
        for value in candidates:
            # Early termination check
            if max_solutions is not None and len(solutions) >= max_solutions:
                return

            # Save current state
            current_state = save_state()

            # Place the value
            square[i][j] = value
            update_constraints_fast(i, j, value)

            # Validity check and recurse
            if is_valid_state():
                backtrack()

            # Restore state for next candidate
            restore_state(current_state)

    # Validate that known values don't violate Latin square constraints
    for i in range(size):
        row_values = [square[i][j] for j in range(size) if square[i][j] != -1]
        if len(row_values) != len(set(row_values)):
            return [], []  # Duplicate values in row

    for j in range(size):
        col_values = [square[i][j] for i in range(size) if square[i][j] != -1]
        if len(col_values) != len(set(col_values)):
            return [], []  # Duplicate values in column

    # Initial constraint propagation - solve all obvious cells first
    initial_placements = propagate_constraints()
    if initial_placements is False:
        return [], []  # Invalid puzzle

    # Initial validity check
    if not is_valid_state():
        return [], []

    # Check if already solved by initial propagation
    empty_cells = sum(1 for i in range(size) for j in range(size) if square[i][j] == -1)
    if empty_cells == 0:
        solution = [row[:] for row in square]
        # Validate the solution before returning it
        if is_valid_latin_square(solution):
            return [solution], []
        else:
            return [], []  # Invalid solution, return no solutions

    # Try to find all completions
    try:
        backtrack()
        return solutions, branches
    except TimeoutError:
        return (
            solutions,
            branches,
        )  # Return whatever solutions we found before timing out


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
    """Return a random nxn square with n ones, n twos, etc."""
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
    solutions, branches = complete_latin_square_backtrack_all_solutions(
        size, known_values, known_wrong_values, timeout, max_solutions=1
    )
    return solutions[0] if solutions else None


def standardize_tile_tuple(correct_tiles):
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
        result = complete_latin_square_backtrack_all_solutions(
            N, known_values, known_wrong_values, max_solutions=2
        )
        solutions, branches = result
        if len(solutions) == 1:
            selected_solutions.append((selected_tiles, solutions[0]))
    return selected_solutions


if __name__ == "__main__":
    first_guess = cyclic_latin_square(5)
    tries = simulate_game(first_guess, verbose=True)
    print(f"Found solution in {len(tries) + 1} tries!")


def parse_puzzles_from_txt(txt_file, standardize_tiles=True):
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
                standardized_tiles = standardize_tile_tuple(tiles)
                if standardized_tiles not in seen_standardized_puzzles:
                    puzzles.append(tiles)
                    seen_standardized_puzzles.add(standardized_tiles)
            else:
                puzzles.append(tiles)
    return puzzles
