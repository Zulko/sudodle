<script>
  import { onMount } from "svelte";

  export let currentGrid;
  export let visualCues = true;
  export let previousGrids = [];
  export let solutionGrid = [];
  export let feedback = null;

  let draggedTile = null;
  let draggedPosition = null;
  let hoveredPosition = null;
  let recentlySwapped = [];
  let touchStartPosition = null;
  let isDragging = false;
  let currentTouchPosition = null;

  // Get the grid size
  $: gridSize = currentGrid.length;

  // Utility function to prevent default when possible
  // This prevents console errors when preventDefault() is called on passive event listeners
  function preventDefaultIfPossible(event) {
    try {
      event.preventDefault();
    } catch (e) {
      // Ignore passive event listener error - preventDefault is not possible
    }
  }

  // Force reactivity for tile classes when hover state changes
  $: hoveredPosition,
    draggedPosition,
    isDragging,
    recentlySwapped,
    (() => {
      // This reactive statement ensures tiles re-render when hover state changes
    })();

  function handleDragStart(event, row, col) {
    draggedTile = currentGrid[row][col];
    draggedPosition = { row, col };
    event.dataTransfer.effectAllowed = "move";
  }

  function handleDragOver(event) {
    preventDefaultIfPossible(event);
    event.dataTransfer.dropEffect = "move";

    // Find which tile is being hovered over
    let targetElement = event.target;

    // Make sure we're targeting a tile element
    if (targetElement && targetElement.classList.contains("tile")) {
      // Use data attributes instead of querySelector index for more reliable positioning
      const targetRow = parseInt(targetElement.getAttribute("data-row"));
      const targetCol = parseInt(targetElement.getAttribute("data-col"));

      if (!isNaN(targetRow) && !isNaN(targetCol)) {
        hoveredPosition = { row: targetRow, col: targetCol };
      }
    }
  }

  function handleDragEnter(event) {
    preventDefaultIfPossible(event);

    // Find which tile is being entered
    let targetElement = event.target;

    if (targetElement && targetElement.classList.contains("tile")) {
      // Use data attributes instead of querySelector index for more reliable positioning
      const targetRow = parseInt(targetElement.getAttribute("data-row"));
      const targetCol = parseInt(targetElement.getAttribute("data-col"));

      if (!isNaN(targetRow) && !isNaN(targetCol)) {
        hoveredPosition = { row: targetRow, col: targetCol };
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
    preventDefaultIfPossible(event);
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
    event.preventDefault(); // Prevent scrolling - now safe since we use non-passive listeners
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
        // Use data attributes instead of querySelector index for more reliable positioning
        const targetRow = parseInt(elementBelow.getAttribute("data-row"));
        const targetCol = parseInt(elementBelow.getAttribute("data-col"));

        if (!isNaN(targetRow) && !isNaN(targetCol)) {
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
      // Use data attributes instead of querySelector index for more reliable positioning
      const targetRow = parseInt(elementBelow.getAttribute("data-row"));
      const targetCol = parseInt(elementBelow.getAttribute("data-col"));

      if (!isNaN(targetRow) && !isNaN(targetCol)) {
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

      // Highlight the swapped tiles
      recentlySwapped = [
        { row: targetRow, col: targetCol },
        { row: draggedPosition.row, col: draggedPosition.col },
      ];

      // Clear the highlight after animation
      setTimeout(() => {
        recentlySwapped = [];
      }, 600);
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
    }

    // Add swap highlight class if this tile was recently swapped
    if (recentlySwapped.some((pos) => pos.row === row && pos.col === col)) {
      classes.push("recently-swapped");
    }

    // If we have immediate feedback, show it and return early
    if (feedback && feedback[row] && feedback[row][col] !== undefined) {
      if (feedback[row][col]) {
        // Check if this tile was already correct in previous turns
        const wasCorrectInPrevious = previousGrids.some(
          (prevGrid) =>
            prevGrid.feedback &&
            prevGrid.feedback[row] &&
            prevGrid.feedback[row][col]
        );

        if (wasCorrectInPrevious) {
          classes.push("feedback-correct");
        } else {
          classes.push("feedback-correct-new");
        }
      }
      // Don't add any class for incorrect tiles - leave them as default
      return classes.join(" ");
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

    // Check for duplicates in same row or column (only if not correct at position)
    const isCorrectAtPosition =
      solutionGrid[row] && solutionGrid[row][col] === value;
    const hasDuplicateInRow =
      currentGrid[row].filter((v) => v === value).length > 1;
    const hasDuplicateInCol = currentGrid.some(
      (r) => r[col] === value && r !== currentGrid[row]
    );

    if (!isCorrectAtPosition && (hasDuplicateInRow || hasDuplicateInCol)) {
      classes.push("duplicate");
    }

    return classes.join(" ");
  }

  // Set up non-passive touch event listeners to prevent console errors
  onMount(() => {
    const gridElement = document.querySelector(".grid");
    if (gridElement) {
      gridElement.addEventListener("touchmove", handleTouchMove, {
        passive: false,
      });
    }

    return () => {
      // Cleanup on component destroy
      if (gridElement) {
        gridElement.removeEventListener("touchmove", handleTouchMove);
      }
    };
  });
</script>

<div class="grid-container">
  <div class="instruction-label">Drag tiles to swap them</div>
  <div class="grid" style="--grid-size: {gridSize}">
    {#each currentGrid as row, rowIndex}
      {#each row as value, colIndex}
        <div
          class={getTileClasses(rowIndex, colIndex, value)}
          draggable="true"
          data-row={rowIndex}
          data-col={colIndex}
          ondragstart={(e) => handleDragStart(e, rowIndex, colIndex)}
          ondragover={handleDragOver}
          ondragenter={handleDragEnter}
          ondragleave={handleDragLeave}
          ondrop={(e) => handleDrop(e, rowIndex, colIndex)}
          ontouchstart={(e) => handleTouchStart(e, rowIndex, colIndex)}
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
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin: 1rem 0;
    /* Prevent layout shifts during feedback */
    position: relative;
  }

  .instruction-label {
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
    width: min(100%, 350px);
    aspect-ratio: 1;
    /* Ensure stable positioning during animations */
    position: relative;
    transform: translateZ(0); /* Create a new stacking context */
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
    cursor: grab;
    transition: all 0.2s ease;
    user-select: none;
    touch-action: none;
    /* Prevent layout shifts from transforms */
    transform: translateZ(0);
    will-change: transform;
  }

  .tile:hover {
    background: #f8f9fa;
    transform: translateZ(0) scale(1.05);
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
  }

  .tile:active {
    cursor: grabbing;
    transform: translateZ(0) scale(0.95);
  }

  /* Dragging states */
  .tile.dragging {
    opacity: 0.3;
  }

  /* Hover state during drag operations */
  .tile.drag-hover {
    transform: translateZ(0) translateY(-6px) scale(1.08) !important;
    box-shadow: 0 8px 16px rgba(52, 152, 219, 0.3) !important;
    background: #e3f2fd !important;
    border-color: #2196f3 !important;
    border-width: 2px !important;
    z-index: 10;
    transition: all 0.15s ease !important;
  }

  /* Recently swapped tiles pulse effect */
  .tile.recently-swapped {
    animation: swapPulse 0.6s ease-out;
  }

  @keyframes swapPulse {
    0% {
      transform: translateZ(0) scale(1);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    50% {
      transform: translateZ(0) scale(1.15);
      box-shadow: 0 6px 16px rgba(33, 150, 243, 0.3);
    }
    100% {
      transform: translateZ(0) scale(1);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
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
    transform: translateZ(0) scale(1.1);
  }

  /* Visual cues */
  .tile.correct-previous {
    background: #28a745;
    color: #ffffff;
  }

  .tile.incorrect-previous {
    background: #fff3cd;
    color: #856404;
    font-weight: 700;
  }

  .tile.duplicate {
    background: #ffffff;
    color: #e67e22;
    font-weight: 700;
  }

  /* Immediate feedback styles */
  .tile.feedback-correct {
    background: #28a745;
    color: #ffffff;
    font-weight: 700;
  }

  .tile.feedback-correct-new {
    background: #28a745;
    color: #ffffff;
    font-weight: 700;
    animation: correctPulse 0.6s ease-out;
  }

  @keyframes correctPulse {
    0% {
      transform: translateZ(0) scale(1);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }
    50% {
      transform: translateZ(0) scale(1.1);
      box-shadow: 0 6px 16px rgba(40, 167, 69, 0.4);
    }
    100% {
      transform: translateZ(0) scale(1);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }
  }

  /* Combination: both previously incorrect AND duplicate */
  .tile.incorrect-previous.duplicate {
    background: #fff3cd;
    color: #e67e22;
    font-weight: 700;
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
