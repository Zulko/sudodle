from .utils import cyclic_latin_square


def solve_sudodle_via_human_heuristics(
    N, known_values, known_incorrect, max_solutions, verbose=False
):
    """
    Solve an N×N Latin square with backtracking + constraint propagation.

    Inputs:
      - N: grid size
      - known_values: dict[(i,j)] = v  (cells pre-filled)
      - known_incorrect: dict[(i,j)] = {forbidden values}
      - max_solutions: stop after finding this many

    Returns: (solutions, n_branches)
      - solutions: list of completed grids
      - n_branches: how many times we had to branch
    """

    def vprint(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)

    # 1) Initialize domains for each cell
    domains = {}
    for i in range(N):
        for j in range(N):
            if (i, j) in known_values:
                domains[(i, j)] = {known_values[(i, j)]}
            else:
                forbidden = set(known_incorrect.get((i, j), []))
                domains[(i, j)] = set(range(1, N + 1)) - forbidden

    # 2) Track where each value can still go in each row/column
    row_pos = {(r, v): set(range(N)) for r in range(N) for v in range(1, N + 1)}
    col_pos = {(c, v): set(range(N)) for c in range(N) for v in range(1, N + 1)}

    # 3) Keep a set of already‐propagated assignments to avoid re-processing singletons
    assigned = set()

    def eliminate_cell(i, j, v):
        """Assign (i,j)=v, prune that v from all peers, and remove other values from (i,j)."""
        # only run once per cell
        if (i, j) in assigned:
            domains[(i, j)] = {v}
            return
        assigned.add((i, j))

        # fix the domain
        domains[(i, j)] = {v}
        row_pos[(i, v)].add("done")
        col_pos[(j, v)].add("done")

        # remove i from row_pos on the same row
        for row in range(N):
            if row != i:
                row_pos[(row, v)].discard(j)

        # remove j from row_pos on the same col
        for col in range(N):
            if col != j:
                col_pos[(col, v)].discard(i)

        # # forbid v in all other cells of row i
        # for jj in list(row_pos[(i, v)]):
        #     if jj != j:
        #         domains[(i, jj)].discard(v)

        # # forbid v in all other cells of col j
        # for ii in list(col_pos[(j, v)]):
        #     if ii != i:
        #         vprint(f"removing {ii} from 'values for {v} in col {j}'")
        #         col_pos[(j, v)].discard(ii)
        #         domains[(ii, j)].discard(v)

        # in (i,j), forbid all other values
        for vv in range(1, N + 1):
            row_pos[(i, vv)].discard(j)
            col_pos[(j, vv)].discard(i)

    # apply the initial known_values
    for (i, j), v in known_values.items():
        vprint(f"Applying known value: ({i}, {j}) set to {v}")
        eliminate_cell(i, j, v)
    for (i, j), vv in known_incorrect.items():
        for v in vv:
            vprint(
                f"Removing {j} from the possibilites for {v} on row {i}, "
                f"and {i} from the possibilites for {v} on col {j}",
            )
            vprint(row_pos[(i, v)])
            row_pos[(i, v)].discard(j)
            col_pos[(j, v)].discard(i)

    solutions = []
    branch_count = 0

    def propagate():
        """Keep applying forced moves until nothing changes or a contradiction appears."""
        queue = True
        while queue:
            queue = False

            # a) contradiction: any domain empty?
            for pos, dom in domains.items():
                if not dom:
                    vprint(f"Contradiction found: empty domain for {pos}")
                    return False

            # b) singletons: only propagate if not yet processed
            for (i, j), dom in list(domains.items()):
                if len(dom) == 1 and (i, j) not in assigned:
                    eliminate_cell(i, j, next(iter(dom)))
                    queue = True
                    break
            if queue:
                continue

            # c) unique‐position in rows
            for r in range(N):
                for v in range(1, N + 1):
                    if "done" in row_pos[(r, v)]:
                        continue
                    poss = row_pos[(r, v)]
                    if not poss:
                        vprint(
                            f"Contradiction: no possibilities for value {v} on row {r}"
                        )
                        return False
                    if len(poss) == 1:
                        c = next(iter(poss))
                        if (r, c) not in assigned:
                            vprint(f"Eliminating ({r}, {c}) = {v} for row")
                            eliminate_cell(r, c, v)
                            row_pos[(r, v)].add("done")
                            queue = True
                            break
                if queue:
                    break
            if queue:
                continue

            # d) unique‐position in cols
            for c in range(N):
                for v in range(1, N + 1):
                    if "done" in col_pos[(c, v)]:
                        continue
                    poss = col_pos[(c, v)]
                    if not poss:
                        vprint(
                            f"Contradiction: no possibilities for value {v} on col {c}"
                        )
                        return False
                    if len(poss) == 1:
                        i = next(iter(poss))
                        if (i, c) not in assigned:
                            vprint(f"Eliminating ({i}, {c}) = {v} for col")
                            eliminate_cell(i, c, v)
                            queue = True
                            break
                if queue:
                    break

        return True

    def backtrack():
        nonlocal branch_count
        if not propagate():
            vprint("Contradiction found in propagate")
            return False

        # is it fully assigned?
        if all(len(domains[(i, j)]) == 1 for i in range(N) for j in range(N)):
            sol = [[next(iter(domains[(i, j)])) for j in range(N)] for i in range(N)]
            solutions.append(sol)
            return len(solutions) >= max_solutions

        # pick the unfilled cell with smallest domain >1
        choices = [
            (i, j) for i in range(N) for j in range(N) if len(domains[(i, j)]) > 1
        ]
        i, j = min(choices, key=lambda pos: len(domains[pos]))
        opts = list(domains[(i, j)])
        branch_count += 1
        vprint(f"Branching on ({i}, {j}) with options {opts}")

        # snapshot current state
        saved_domains = {k: set(v) for k, v in domains.items()}
        saved_row_pos = {k: set(v) for k, v in row_pos.items()}
        saved_col_pos = {k: set(v) for k, v in col_pos.items()}
        saved_assigned = set(assigned)

        for v in opts:
            # restore
            domains.clear()
            domains.update({k: set(vv) for k, vv in saved_domains.items()})
            row_pos.clear()
            row_pos.update({k: set(vv) for k, vv in saved_row_pos.items()})
            col_pos.clear()
            col_pos.update({k: set(vv) for k, vv in saved_col_pos.items()})
            assigned.clear()
            assigned.update(saved_assigned)

            # try this value
            vprint(f"Trying value {v} for ({i}, {j})")
            eliminate_cell(i, j, v)
            if backtrack():
                return True

        return False

    backtrack()
    return solutions, branch_count


def generate_cyclic_square(N):
    square = [[0] * N for _ in range(N)]
    for i in range(N):
        square[i][i] = i + 1
    return square


def score_puzzle_difficulty(puzzle, grid_size):
    cyclic_square = cyclic_latin_square(grid_size)
    known_values = {(i, j): cyclic_square[i][j] for i, j in puzzle}
    known_incorrect = {
        (i, j): [cyclic_square[i][j]]
        for i in range(grid_size)
        for j in range(grid_size)
    }
    solutions, n_branches = solve_sudodle_via_human_heuristics(
        N=grid_size,
        known_values=known_values,
        known_incorrect=known_incorrect,
        max_solutions=2,
    )
    if len(solutions) > 1:
        solutions_txt = "\n----\n".join(
            [
                "\n".join([" ".join(str(v) for v in row) for row in solution])
                for solution in solutions
            ]
        )
        raise ValueError(
            f"Found {len(solutions)} solutions for {puzzle}:\n{solutions_txt}"
        )
    return n_branches


if __name__ == "__main__":
    N = 6
    cyclic_square = cyclic_latin_square(N)
    placed_tiles = [(0, 0), (0, 1), (1, 0), (3, 5), (4, 4), (4, 5)]
    placed_tiles = [(0, 0), (0, 1), (1, 2), (1, 3), (2, 2), (5, 1)]
    # placed_tiles = [(0, 0), (0, 1), (1, 2), (1, 3)]
    placed_tiles = [(0, 0), (0, 1), (1, 0), (3, 5), (4, 4), (4, 5)]
    placed_tiles = [(0, 1), (0, 3), (1, 2), (2, 0), (3, 4), (4, 1), (5, 5)]
    known_values = {(i, j): cyclic_square[i][j] for i, j in placed_tiles}
    known_incorrect = {
        (i, j): [cyclic_square[i][j]]
        for i in range(N)
        for j in range(N)
        if (i, j) not in placed_tiles
    }
    max_solutions = 20
    solutions, branch_count = solve_sudodle_via_human_heuristics(
        N, known_values, known_incorrect, max_solutions, verbose=True
    )
    print(solutions)
    print(branch_count)
