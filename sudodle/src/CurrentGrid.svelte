<script>
  export let currentGrid;
  export let visualCues = true;
  export let previousGrids = [];
  export let solutionGrid = [];

  let draggedTile = null;
  let draggedPosition = null;

  // Get the grid size
  $: gridSize = currentGrid.length;

  function handleDragStart(event, row, col) {
    draggedTile = currentGrid[row][col];
    draggedPosition = { row, col };
    event.dataTransfer.effectAllowed = "move";
  }

  function handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }

  function handleDrop(event, targetRow, targetCol) {
    event.preventDefault();

    if (
      draggedPosition &&
      (draggedPosition.row !== targetRow || draggedPosition.col !== targetCol)
    ) {
      // Swap the tiles
      const newGrid = currentGrid.map((row) => [...row]);
      const temp = newGrid[targetRow][targetCol];
      newGrid[targetRow][targetCol] = draggedTile;
      newGrid[draggedPosition.row][draggedPosition.col] = temp;

      currentGrid = newGrid;
    }

    draggedTile = null;
    draggedPosition = null;
  }

  function getTileClasses(row, col, value) {
    let classes = ["tile"];

    if (!visualCues) return classes.join(" ");

    // Check if this position was correct in previous turns
    const wasCorrectInPrevious = previousGrids.some(
      (prevGrid) =>
        prevGrid.feedback &&
        prevGrid.feedback[row] &&
        prevGrid.feedback[row][col]
    );

    if (
      wasCorrectInPrevious &&
      solutionGrid[row] &&
      solutionGrid[row][col] === value
    ) {
      classes.push("correct-previous");
    }

    // Check if this value was incorrect at this position in previous turns
    const wasIncorrectAtPosition = previousGrids.some(
      (prevGrid) =>
        prevGrid.grid[row][col] === value &&
        prevGrid.feedback &&
        prevGrid.feedback[row] &&
        !prevGrid.feedback[row][col]
    );

    if (wasIncorrectAtPosition) {
      classes.push("incorrect-previous");
    }

    // Check for duplicates in same row or column
    const hasDuplicateInRow =
      currentGrid[row].filter((v) => v === value).length > 1;
    const hasDuplicateInCol = currentGrid.some(
      (r) => r[col] === value && r !== currentGrid[row]
    );

    if (hasDuplicateInRow || hasDuplicateInCol) {
      classes.push("duplicate");
    }

    return classes.join(" ");
  }
</script>

<div class="grid-container">
  <div class="grid" style="--grid-size: {gridSize}">
    {#each currentGrid as row, rowIndex}
      {#each row as value, colIndex}
        <div
          class={getTileClasses(rowIndex, colIndex, value)}
          draggable="true"
          ondragstart={(e) => handleDragStart(e, rowIndex, colIndex)}
          ondragover={handleDragOver}
          ondrop={(e) => handleDrop(e, rowIndex, colIndex)}
          role="gridcell"
          tabindex="0"
          aria-label="Tile at row {rowIndex + 1}, column {colIndex +
            1}, value {value}"
        >
          {value}
        </div>
      {/each}
    {/each}
  </div>
</div>

<style>
  .grid-container {
    display: flex;
    justify-content: center;
    margin: 1rem 0;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(var(--grid-size), 1fr);
    grid-template-rows: repeat(var(--grid-size), 1fr);
    gap: 2px;
    background: transparent;
    padding: 4px;
    border-radius: 8px;
    width: min(100%, 350px);
    aspect-ratio: 1;
  }

  .tile {
    background: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: clamp(1rem, 4vw, 1.5rem);
    font-weight: 600;
    color: #2c3e50;
    border: 1px solid #e1e5e9;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    cursor: grab;
    transition: all 0.2s ease;
    user-select: none;
    touch-action: none;
  }

  .tile:hover {
    background: #f8f9fa;
    transform: scale(1.05);
  }

  .tile:active {
    cursor: grabbing;
    transform: scale(0.95);
  }

  /* Visual cues */
  .tile.correct-previous {
    background: #d4edda;
    color: #155724;
  }

  .tile.incorrect-previous {
    color: #d2691e;
    font-weight: 700;
  }

  .tile.duplicate {
    color: #dc3545;
    font-weight: 700;
    background: #f8d7da;
  }

  /* Responsive adjustments */
  @media (max-width: 480px) {
    .grid {
      width: calc(100vw - 2rem);
      max-width: 300px;
    }

    .tile {
      font-size: clamp(0.8rem, 3.5vw, 1.2rem);
    }
  }

  /* Focus styles for accessibility */
  .tile:focus {
    outline: none;
    box-shadow:
      0 2px 4px rgba(0, 0, 0, 0.1),
      0 0 0 2px rgba(52, 152, 219, 0.3);
  }

  /* Drag feedback */
  .tile:where([draggable="true"]:hover) {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }
</style>
