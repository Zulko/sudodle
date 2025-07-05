# Puzzle mining with a Rust program

This contains the code for a program that generates a random puzzle (by randomly selecting N "correct" tiles in a grid) and checks whether that puzzle has a unique solution, at which case it is written to a file.

For lower grid sizes, the program can iterate through all possible combinations of tiles to find all puzzles with a unique solution. However, starting at 7x7 grids, you need to use a random sampling approach to find puzzles with a unique solution.

The program is optimized for speed, but there is still room for improvement. See [README_OPTIMIZATIONS.md](README_OPTIMIZATIONS.md) for more details.

## Usage

Install `rust` and `cargo` then run this to compile the program:

```
cargo build --release
```

Now you can mine puzzles:

```bash
# 4x4 puzzles with 2 tiles placed
./target/release/find_puzzles --size 4 --placed 2 --processors 4 --out-file outputs/s4.txt

# 5x5 puzzles with 4 tiles placed
./target/release/find_puzzles --size 5 --placed 4 --processors 4 --out-file outputs/s5.txt

# 6x6 puzzles with 6 tiles placed
./target/release/find_puzzles --size 6 --placed 6 --processors 4 --out-file outputs/s6.txt

# 7x7 Puzzles with 7 tiles placed
./target/release/find_puzzles --size 7 --placed 10 --processors 4 --random-tries 10000000 --out-file outputs/s7-p10-10M.txt
```