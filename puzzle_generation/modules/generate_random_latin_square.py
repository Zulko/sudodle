import random
import time


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
