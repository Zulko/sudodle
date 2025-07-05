from .generate_random_latin_square import uniform_random_latin_square
from .utils import compare_squares, cyclic_latin_square
from .solve_sudodle_semi_optimized import complete_latin_square_backtrack
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm.auto import tqdm


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


if __name__ == "__main__":
    from utils import cyclic_latin_square

    first_guess = cyclic_latin_square(5)
    tries = simulate_game(first_guess, verbose=True)
    print(f"Found solution in {len(tries) + 1} tries!")
