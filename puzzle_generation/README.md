# A study of Sudodles

In this folder we study the game of Sudodle. In this game, we must guess the position of numbers in latin square, where each number appears once on each row and column. We start from standard cyclic latin square where we are told which positions are "correct", and we must guess the rest of the grid.
There are two variants: in the single-turn variant or "paper sudodle" (because it can be played on a piece of paper), there is enough information at the beginning to solve the puzzle, while in the multi-turn variant or "app" variant, we take successive guesses.


# Paper sudodle


## Rules

> Larissa made a Latin square, where each number appears once on each row and each column. Quentin says "I made one too, and some positions are identical" and he marks them. What is Quentin's square?

## Numbers

To create a paper sudodle puzzle, we need to find a minimal subset of positions such that "these positions are correct and the others are wrong" constitutes a problem with a unique solution. Up to 6x6 grids, the problem can be brute-forced: we can try all the possible subsets of positions and check if they create a valid problem. However, starting at 7x7 grids, the numbers become very large, there are 8 billion subsets of 10 positions in a 7x7 grid, and solving 8 billion puzzles would take time. So for these grid sizes we just randomly sample possible puzzles and hope to find some with a unique solution.

The numbers of puzzles given below are after puzzles that are equivalent by symmetry are deduplicated. There are probably more equivalences between the problems (via number permutations, rows permutations, etc).

- For 4x4 grids, we need at least 2 "correct" positions. There are 26 problems involving 2 "correct" positions.
- For 5x5 grids, we need at least 4 "correct" positions. There are 1500 problems involving 4 "correct" positions. Around 500 of these problems can be solved by logically deducing the digits one by one, the rest requires to take a guess at some point and backtrack later.
- For 6x6 grids, we need at least 6 "correct" positions. There are 57 problems involving 6 "correct" positions.
- For 7x7 grids, scanning 30 million combinations with 9 correct positions yields 0 solution, so 10 "correct" positions seem to be needed. With 10 correct positions, one must scan 100,000 random puzzles to find one with a unique solution.

# Multi-turn sudodle

## Rules

## Number of turns needed

Using a constraint solver, which can be seen as an expert sudoky player who can use all the information available, we find that:
- The 5x5 grid can always be solved in 3 guesses, and even 2 guesses slightly more than 50% of the time.
- The 6x6 grid can be solved in 3 guesses in general, and 2 guesses ~10% if the time.
- The 7x7 grid can be solved in 3 guesses 90% of the time. A 4th guess is needed ~10% if the time.
- The 8x8 grid can always be solved in 4 guesses, and as little as 3 guesses more than 50% of the time.
- The 9x9 grid needs 4 guesses, although if you are lucky (10% of the time) you might solve it in 3 guesses.


## Best starting strategies

Simulations on a 5x5 grid show that:
- Any latin square as a starting grid leads to wins in 2 (>50% of the time) or 3 guesses. These might be the best starting grids.
- If instead of a latin square, we start with a random grid, 3 turns are still enough, are needed more than 50% of the time.
- The worse starting grid is the one with only "1" in the first row, and "2" in the second row, etc. It requires 3 and sometimes even 4 guesses.