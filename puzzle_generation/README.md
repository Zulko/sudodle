# A study of Sudodles

In this folder we study the game of Sudodle and "mine" new puzzles. Below are some summaries of the of the methods and results.

# Sudodle

To create a Sudodle with a NxN grid we need to find a minimal subset of positions such that "these positions are correctly-paced digits, and all other digits are incorrectly placed" constitutes a problem with a unique solution. Up to 6x6 grids, we can find all possible sudodles by considering all the possible subsets of "correctly placed positions" and checking whether they create a valid problem. This takes generally a few minutes. However, starting at 7x7 grids, the number of puzzles to explore becomes very large, there are 8 billion subsets of 10 positions in a 7x7 grid, and solving 8 billion puzzles would take time. So for these grid sizes we just randomly sample possible puzzles and hope to find some with a unique solution. This is done efficiently using a Rust program.

Some numbers:

- For 4x4 grids, we need at least 2 "correct" positions. There are 26 problems involving 2 "correct" positions (after removing problems that are "equivalent by simple symmetries").
- For 5x5 grids, we need at least 4 "correct" positions. There are 1500 problems involving 4 "correct" positions. Around 500 of these problems can be solved by logically deducing the digits one by on (these are classified as "easy" puzzles), the rest requires to take a guess at some point and backtrack later (these are classified as "hard" puzzles or "expert" depending on the amount of guesses needed). Using 5 correct positions also allows to find interesting new puzzles, both easy and hard.
- For 6x6 grids, we need at least 6 "correct" positions. There are 57 unique-by-symmetry problems involving 6 correct positions. The most interesting 
- For 7x7 grids, scanning 30 million combinations with 9 correct positions yields 0 solution, so 10 "correct" positions seem to be needed. With 10 correct positions, one must scan 100,000 random puzzles to find one with a unique solution.

# Multi-turn sudodle

In a multi-turn Sudodle, the player can propose successive guesses to gather more information. These games are much simpler to generate than the standard Sudodle, we just pick a random latin square at the beginning and let the user find it using successive guesses.

Using a constraint solver, which can be seen as an expert sudoky player who can use all the information available, we find that:
- The 5x5 grid can always be solved in 3 guesses, and even 2 guesses slightly more than 50% of the time.
- The 6x6 grid can be solved in 3 guesses in general, and 2 guesses ~10% if the time.
- The 7x7 grid can be solved in 3 guesses 90% of the time. A 4th guess is needed ~10% if the time.
- The 8x8 grid can always be solved in 4 guesses, and as little as 3 guesses more than 50% of the time.
- The 9x9 grid needs 4 guesses, although if you are lucky (10% of the time) you might solve it in 3 guesses.

Simulations on a 5x5 grid show that:
- Any latin square as a starting grid leads to wins in 2 (>50% of the time) or 3 guesses. These might be the best starting grids.
- If instead of a latin square, we start with a random grid, 3 turns are still enough, are needed more than 50% of the time.
- The worse starting grid is the one with only "1" in the first row, and "2" in the second row, etc. It requires 3 and sometimes even 4 guesses.