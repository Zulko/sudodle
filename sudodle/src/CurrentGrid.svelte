<script>
  export let currentGrid;
  export let visualCues = true;
  export let previousGrids = [];
  export let solutionGrid = [];

  let draggedTile = null;
  let draggedPosition = null;
  let hoveredPosition = null;
  let touchStartPosition = null;
  let isDragging = false;
  let currentTouchPosition = null;

  // Get the grid size
  $: gridSize = currentGrid.length;

  // Force reactivity for tile classes when hover state changes
  $: hoveredPosition,
    draggedPosition,
    isDragging,
    (() => {
      // This reactive statement ensures tiles re-render when hover state changes
    })();

  function handleDragStart(event, row, col) {
    draggedTile = currentGrid[row][col];
    draggedPosition = { row, col };
    event.dataTransfer.effectAllowed = "move";
  }

  function handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";

    // Find which tile is being hovered over
    let targetElement = event.target;

    // Make sure we're targeting a tile element
    if (targetElement && targetElement.classList.contains("tile")) {
      const tiles = Array.from(document.querySelectorAll(".tile"));
      const targetIndex = tiles.indexOf(targetElement);

      if (targetIndex >= 0) {
        const targetRow = Math.floor(targetIndex / gridSize);
        const targetCol = targetIndex % gridSize;
        hoveredPosition = { row: targetRow, col: targetCol };
      }
    }
  }

  function handleDragEnter(event) {
    event.preventDefault();

    // Find which tile is being entered
    let targetElement = event.target;

    if (targetElement && targetElement.classList.contains("tile")) {
      const tiles = Array.from(document.querySelectorAll(".tile"));
      const targetIndex = tiles.indexOf(targetElement);

      if (targetIndex >= 0) {
        const targetRow = Math.floor(targetIndex / gridSize);
        const targetCol = targetIndex % gridSize;
        hoveredPosition = { row: targetRow, col: targetCol };
        console.log("Hover position set:", hoveredPosition);
      }
    }
  }

  function handleDragLeave(event) {
    // Clear hover state when leaving a tile
    if (
      !event.relatedTarget ||
      !event.relatedTarget.classList.contains("tile")
    ) {
      hoveredPosition = null;
    }
  }

  function handleDrop(event, targetRow, targetCol) {
    event.preventDefault();
    swapTiles(targetRow, targetCol);
    hoveredPosition = null;
  }

  // Touch event handlers
  function handleTouchStart(event, row, col) {
    draggedTile = currentGrid[row][col];
    draggedPosition = { row, col };
    touchStartPosition = {
      x: event.touches[0].clientX,
      y: event.touches[0].clientY,
    };
    isDragging = true;
    currentTouchPosition = {
      x: event.touches[0].clientX,
      y: event.touches[0].clientY,
    };
  }

  function handleTouchMove(event) {
    event.preventDefault(); // Prevent scrolling
    if (isDragging && draggedPosition) {
      currentTouchPosition = {
        x: event.touches[0].clientX,
        y: event.touches[0].clientY,
      };

      // Find which tile is being hovered over during touch drag
      const elementBelow = document.elementFromPoint(
        event.touches[0].clientX,
        event.touches[0].clientY
      );

      if (elementBelow && elementBelow.classList.contains("tile")) {
        const tiles = Array.from(document.querySelectorAll(".tile"));
        const targetIndex = tiles.indexOf(elementBelow);

        if (targetIndex >= 0) {
          const targetRow = Math.floor(targetIndex / gridSize);
          const targetCol = targetIndex % gridSize;
          hoveredPosition = { row: targetRow, col: targetCol };
        }
      } else {
        hoveredPosition = null;
      }
    }
  }

  function handleTouchEnd(event) {
    if (!draggedPosition || !touchStartPosition) return;

    const touch = event.changedTouches[0];
    const elementBelow = document.elementFromPoint(
      touch.clientX,
      touch.clientY
    );

    if (elementBelow && elementBelow.classList.contains("tile")) {
      // Find the grid position of the target tile
      const tiles = Array.from(document.querySelectorAll(".tile"));
      const targetIndex = tiles.indexOf(elementBelow);

      if (targetIndex >= 0) {
        const targetRow = Math.floor(targetIndex / gridSize);
        const targetCol = targetIndex % gridSize;
        swapTiles(targetRow, targetCol);
      }
    }

    // Reset touch state
    touchStartPosition = null;
    isDragging = false;
    currentTouchPosition = null;
    hoveredPosition = null;
  }

  function swapTiles(targetRow, targetCol) {
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

    // Add dragging class if this tile is being dragged
    if (
      isDragging &&
      draggedPosition &&
      draggedPosition.row === row &&
      draggedPosition.col === col
    ) {
      classes.push("dragging");
    }

    // Add hover class if this tile is being hovered over during drag
    if (
      hoveredPosition &&
      hoveredPosition.row === row &&
      hoveredPosition.col === col &&
      !(
        draggedPosition &&
        draggedPosition.row === row &&
        draggedPosition.col === col
      )
    ) {
      classes.push("drag-hover");
      console.log(`Adding drag-hover class to tile at ${row},${col}`);
    }

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
          ondragenter={handleDragEnter}
          ondragleave={handleDragLeave}
          ondrop={(e) => handleDrop(e, rowIndex, colIndex)}
          ontouchstart={(e) => handleTouchStart(e, rowIndex, colIndex)}
          ontouchmove={handleTouchMove}
          ontouchend={handleTouchEnd}
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

  <!-- Dragging tile overlay -->
  {#if isDragging && currentTouchPosition && draggedTile}
    <div
      class="dragging-tile"
      style="left: {currentTouchPosition.x -
        25}px; top: {currentTouchPosition.y - 25}px;"
    >
      {draggedTile}
    </div>
  {/if}
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

  /* Dragging states */
  .tile.dragging {
    opacity: 0.3;
  }

  /* Hover state during drag operations */
  .tile.drag-hover {
    transform: translateY(-6px) scale(1.08) !important;
    box-shadow: 0 8px 16px rgba(52, 152, 219, 0.3) !important;
    background: #e3f2fd !important;
    border-color: #2196f3 !important;
    border-width: 2px !important;
    z-index: 10;
    transition: all 0.15s ease !important;
  }

  .dragging-tile {
    position: fixed;
    width: 50px;
    height: 50px;
    background: white;
    border: 1px solid #e1e5e9;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    font-weight: 600;
    color: #2c3e50;
    pointer-events: none;
    z-index: 1000;
    transform: scale(1.1);
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
