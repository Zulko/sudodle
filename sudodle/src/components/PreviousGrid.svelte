<script>
  export let previousGrid;

  // Get the grid size from the grid data
  $: gridSize = previousGrid.grid.length;

  function getOrdinal(num) {
    const suffix = ["th", "st", "nd", "rd"];
    const v = num % 100;
    return num + (suffix[(v - 20) % 10] || suffix[v] || suffix[0]);
  }

  function getTileClasses(row, col) {
    let classes = ["tile"];

    // Check if this tile was correct
    if (
      previousGrid.feedback &&
      previousGrid.feedback[row] &&
      previousGrid.feedback[row][col]
    ) {
      classes.push("correct");
    }

    return classes.join(" ");
  }
</script>

<div class="grid-container">
  <div class="turn-label">{getOrdinal(previousGrid.turn)} guess</div>
  <div class="grid" style="--grid-size: {gridSize}">
    {#each previousGrid.grid as row, rowIndex}
      {#each row as value, colIndex}
        <div
          class={getTileClasses(rowIndex, colIndex)}
          role="gridcell"
          aria-label="Previous guess: row {rowIndex + 1}, column {colIndex +
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
    flex-direction: column;
    align-items: center;
    margin: 1rem 0;
  }

  .turn-label {
    font-size: 0.9rem;
    color: #7f8c8d;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(var(--grid-size), 1fr);
    grid-template-rows: repeat(var(--grid-size), 1fr);
    gap: 2px;
    background: transparent;
    padding: 4px;
    border-radius: 8px;
    width: min(90%, 315px);
    aspect-ratio: 1;
  }

  .tile {
    background: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: clamp(1rem, 4vw, 1.5rem);
    font-weight: 600;
    color: #2c3e50;
    border: 1px solid #e1e5e9;
    border-radius: 10px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    user-select: none;
    transition: none;
  }

  .tile.correct {
    background: #52c965;
    color: #ffffff;
  }

  /* Responsive adjustments */
  @media (max-width: 480px) {
    .grid {
      width: calc(100vw - 2rem);
      max-width: 300px;
    }

    .tile {
      font-size: clamp(1.2rem, 5vw, 1.8rem);
    }
  }

  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .turn-label {
      color: #aaa;
    }

    .tile {
      background: #2a2a2a;
      color: #ffffff;
      border: 1px solid #444;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    }

    .tile.correct {
      background: #52c965;
      color: #ffffff;
    }
  }
</style>
