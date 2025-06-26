import time


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
