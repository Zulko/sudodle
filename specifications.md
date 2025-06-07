# Sudodle

Sudoku meets Wordle.

## Rules

In sudodle, the player must guess a grid of numbers where each number appears only once in each row and column (also known as a latin square). After completing the grid with a first guess, the player is given feedback on which tiles of the grid where guessed correctly. the player uses that information to make a second guess, and so on until the grid is completed or the player runs out of guesses.

## Variants

The grid can be 5x5, 6x6, 7x7, 8x8 or 9x9. When it is 9x9, the grid is a proper sudoku, meaning its 3x3 subgrids contain all numbers from 1 to 9.

In the strict variant, all the players' guesses must be valid latin squares. In the relaxed variant, the player can make guesses that are not valid latin squares, but the solution is still a latin square.

## User experience

The web application is a single page. It is responsive and fits within the narrow width of a mobile phone.

- First, the rules are briefly explasined
- Then some options are presented: grid size, strict mode, and visual cues.
- Then comes the first grid on which the user will make their first guess. This grid is prefilled with a cyclic latin square:

1 2 3 4 5
2 3 4 5 1
3 4 5 1 2
4 5 1 2 3
5 1 2 3 4

The player can modify the grid by dragging a title over another tile, which results in the two tiles being exchanged.

Under the grid is a button "Check". Upon clicking the button, the grid reveals (in green) the tiles that were guessed correctly.

Victory: If all tiles are green, the player has won. Text appears below the grid, congratulating the player and showing how many guesses they used. It features a button to share the game url or copy it. It also contains a button to start a new game.

Next turn: if there was no victory yet, the current grid is frozen, and a new grid is open below it, initialized with the positions of the previous grid.

If the player ticked the "visual cues" checkbox, the following visual cues will be given:
- Tiles with numbers that were validated as having the correct number in a previous turn have a green background.
- Tiles with numbers that were shown to be incorrect at this position in a previous turn are shown in dark orange font.
- Tiles with numbers that have another same number in the same row or column are shown in bold red font.

The player can then make a second guess, click "Check" again, and so on until the grid is completed or the player runs out of guesses.

## Shareable URL

the game url keeps track of the options selected
- gridSize=5,6,7,8,9
- strictMode=true,false
- visualCues=true,false
- seed (random number that led to the current grid)

## Architecture

State:
- settings: gridSize, strictMode, visualCues
- solutionGrid (the grid generated from the current seed)
- currentGrid: the grid on which the player is currently guessing
- previousGrids: the grids that were guessed before the current grid. They have feedback (correct tiles)

The main component is `App.svelte`. It keeps the state of the game, displays the grids, and handles the logic of the game.

Maybe one component `Settings.svelte` for the settings.

One component `CurrentGrid.svelte` for the current grid. Allows to swap titles. Has visual cues.
Parameters:
- currentGrid as a bound parameter.
- visualCues: true/false.

One component `PreviousGrid.svelte` for the previous grid. Has feedback (correct tiles) but is otherwise frozen.
