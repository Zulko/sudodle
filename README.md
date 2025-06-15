# Sudodle

In Sudodle, the player must find a square where each digit appears once on each row and column, given some well-placed values (in green) and incorrectly-placed values (in yellow).

<img src="sudodle_screenshot.png" alt="Sudodle screenshot">

## Repository Structure

This project is organized into two main components:

- **`study/`** - Python-based analysis tools for game mechanics, puzzle generation algorithms (including a Rust program to mine larger sudodles), and the automated generation of a [puzzle book](./study/sudodles_puzzle_book.pdf)
- **`sudodle/`** - The complete web application powering [sudodle.app](https://sudodle.app), featuring over 1,500 hand-crafted puzzles and an innovative multi-turn game mode

## Running the web app for development

Run locally with 

```bash
npm install
npm run dev
```

The project is deployed on GitHub Pages from the `main` branch.
