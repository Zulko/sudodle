<script>
  import { onMount, tick } from "svelte";
  import { flip } from "svelte/animate";
  import { _ } from "svelte-i18n";

  // Props using Svelte 5 runes
  let {
    currentGrid = $bindable(),
    tilesShownCorrect = {},
    tilesShownWrong = {},
    feedback = null,
    mode = "guesses",
    isTransitioning = false,
    onFirstInteraction = () => {},
  } = $props();

  // State variables using Svelte 5 runes
  let draggedTile = $state(null);
  let draggedIndex = $state(null);
  let hoveredIndex = $state(null);
  let recentlySwapped = $state([]);
  let touchStartPosition = $state(null);
  let isDragging = $state(false);
  let currentTouchPosition = $state(null);
  let clickedTiles = $state([]); // Track recently clicked tiles for pulse effect
  let dragStartTime = $state(null); // Track when drag started to distinguish from clicks
  let touchStartTime = $state(null); // Track when touch started
  let hasTouchMoved = $state(false); // Track if touch has moved significantly
  let lastTouchHandled = $state(0); // Prevent double handling of touch + click

  // Undo functionality
  let pastCurrentGridsForUndo = $state([]);

  // Create stable tiles with unique keys based on content
  let tiles = $state([]);
  let lastGameId = $state(null);
  let gameIdCounter = $state(0);

  // Get the grid size - derived value
  const gridSize = $derived(currentGrid.length);

  // Calculate border radius based on grid size - larger grids get smaller radius
  const borderRadius = $derived(
    (() => {
      const radiusMap = {
        4: 10,
        5: 8,
        6: 7,
        7: 6,
        8: 5,
        9: 4,
      };
      return radiusMap[gridSize] || Math.max(4, 14 - gridSize); // fallback formula
    })()
  );

  // Calculate dragging tile size based on grid size
  const draggingTileSize = $derived(
    (() => {
      const sizes = {
        4: 80,
        5: 70,
        6: 58,
        7: 50,
        8: 44,
        9: 39,
      };
      return sizes[gridSize] || 60; // fallback to 60px
    })()
  );

  // Mobile sizes
  const mobileDraggingTileSize = $derived(
    (() => {
      const mobileSizes = {
        4: 65,
        5: 55,
        6: 48,
        7: 42,
        8: 37,
        9: 33,
      };
      return mobileSizes[gridSize] || 50; // fallback to 50px
    })()
  );

  // Derived value for undo button state
  const canUndo = $derived(pastCurrentGridsForUndo.length > 1);

  // Create a game identifier based on current grid - derived from grid state
  const currentGameId = $derived(() => {
    if (currentGrid.length === 0) return null;

    // Create a content hash to detect when grid content changes (new game)
    const gridContentHash = currentGrid.flat().join(",");
    const expectedInitialContent = Array.from({ length: gridSize }, (_, i) =>
      Array.from({ length: gridSize }, (_, j) => ((i + j) % gridSize) + 1)
    )
      .flat()
      .join(",");

    // If we're at initial state, create new game ID
    if (gridContentHash === expectedInitialContent) {
      return `${gridSize}-${Date.now()}-${gameIdCounter}`;
    }

    // Otherwise return consistent ID for this grid size
    return `${gridSize}-game`;
  });

  // Check if current grid content matches what's in tiles array
  function tilesMatchCurrentGrid() {
    if (tiles.length !== gridSize * gridSize) return false;

    for (let row = 0; row < currentGrid.length; row++) {
      for (let col = 0; col < currentGrid[row].length; col++) {
        const index = row * gridSize + col;
        if (tiles[index]?.value !== currentGrid[row][col]) {
          return false;
        }
      }
    }
    return true;
  }

  // Initialize tiles with stable keys based on value and initial position
  $effect.pre(() => {
    if (
      currentGrid.length > 0 &&
      (currentGameId !== lastGameId ||
        tiles.length !== gridSize * gridSize ||
        !tilesMatchCurrentGrid())
    ) {
      tiles = [];
      for (let row = 0; row < currentGrid.length; row++) {
        for (let col = 0; col < currentGrid[row].length; col++) {
          tiles.push({
            // Stable key based on value and original position - this never changes!
            id: `tile-${currentGrid[row][col]}-at-${row}-${col}-${currentGameId}`,
            value: currentGrid[row][col],
          });
        }
      }
      lastGameId = currentGameId;
    }
  });

  // Helper functions to convert between index and row/col
  function indexToRowCol(index) {
    return {
      row: Math.floor(index / gridSize),
      col: index % gridSize,
    };
  }

  // Helper function to compare grids
  function gridsEqual(grid1, grid2) {
    if (!grid1 || !grid2 || grid1.length !== grid2.length) return false;
    for (let i = 0; i < grid1.length; i++) {
      if (!grid1[i] || !grid2[i] || grid1[i].length !== grid2[i].length)
        return false;
      for (let j = 0; j < grid1[i].length; j++) {
        if (grid1[i][j] !== grid2[i][j]) return false;
      }
    }
    return true;
  }

  // Helper function to compare tiles arrays
  function tilesEqual(tiles1, tiles2) {
    if (!tiles1 || !tiles2 || tiles1.length !== tiles2.length) return false;
    for (let i = 0; i < tiles1.length; i++) {
      if (
        tiles1[i].id !== tiles2[i].id ||
        tiles1[i].value !== tiles2[i].value
      ) {
        return false;
      }
    }
    return true;
  }

  // Update currentGrid from tiles array order
  function updateCurrentGrid() {
    const newGrid = Array(gridSize)
      .fill(null)
      .map(() => Array(gridSize).fill(0));
    tiles.forEach((tile, index) => {
      const { row, col } = indexToRowCol(index);
      newGrid[row][col] = tile.value;
    });
    currentGrid = newGrid;
  }

  // Undo function
  function undoGridChange() {
    if (pastCurrentGridsForUndo.length > 1) {
      // Remove the current state and go back to the previous one
      pastCurrentGridsForUndo = pastCurrentGridsForUndo.slice(0, -1);
      const previousTiles =
        pastCurrentGridsForUndo[pastCurrentGridsForUndo.length - 1];
      // Restore the tiles array directly to maintain tile IDs for animations
      tiles = previousTiles.map((tile) => ({ ...tile }));
      // Update currentGrid to match the restored tiles
      updateCurrentGrid();
    }
  }

  // Track tiles changes for undo functionality
  $effect(() => {
    if (tiles.length > 0) {
      // Create a deep copy of the current tiles array and add it to history
      const tilesCopy = tiles.map((tile) => ({ ...tile }));

      // Only add if it's different from the last stored tiles
      const lastStored =
        pastCurrentGridsForUndo[pastCurrentGridsForUndo.length - 1];
      if (!lastStored || !tilesEqual(tilesCopy, lastStored)) {
        pastCurrentGridsForUndo = [...pastCurrentGridsForUndo, tilesCopy];
      }
    }
  });

  // Reset undo history when game ID changes (new game started)
  $effect(() => {
    if (currentGameId) {
      pastCurrentGridsForUndo = [];
    }
  });

  // Reset undo history when visual cues change (new puzzle or updated context)
  $effect(() => {
    // Watch for changes in tilesShownCorrect or tilesShownWrong
    if (tilesShownCorrect || tilesShownWrong) {
      pastCurrentGridsForUndo = [];
    }
  });

  // Utility function to prevent default when possible
  function preventDefaultIfPossible(event) {
    try {
      event.preventDefault();
    } catch (e) {
      // Ignore passive event listener error - preventDefault is not possible
    }
  }

  function handleDragStart(event, tileIndex) {
    // In single-turn mode, don't allow dragging tiles that were previously correct
    if (mode === "single-turn") {
      const currentValue = tiles[tileIndex].value;
      if (
        tileIndex in tilesShownCorrect &&
        tilesShownCorrect[tileIndex] === currentValue
      ) {
        event.preventDefault();
        return;
      }
    }

    // Trigger first interaction callback for wake lock
    onFirstInteraction();

    draggedTile = tiles[tileIndex];
    draggedIndex = tileIndex;
    dragStartTime = Date.now();
    event.dataTransfer.effectAllowed = "move";
  }

  function handleDragOver(event) {
    preventDefaultIfPossible(event);
    event.dataTransfer.dropEffect = "move";

    // Find which tile is being hovered over
    let targetElement = event.target;

    // Make sure we're targeting a tile element
    if (targetElement && targetElement.classList.contains("tile")) {
      const targetIndex = parseInt(targetElement.getAttribute("data-index"));
      if (!isNaN(targetIndex)) {
        // In single-turn mode, don't set hover state on correct tiles
        if (mode === "single-turn") {
          const targetValue = tiles[targetIndex].value;
          if (
            targetIndex in tilesShownCorrect &&
            tilesShownCorrect[targetIndex] === targetValue
          ) {
            hoveredIndex = null;
            return;
          }
        }
        hoveredIndex = targetIndex;
      }
    }
  }

  function handleDragEnter(event) {
    preventDefaultIfPossible(event);

    // Find which tile is being entered
    let targetElement = event.target;

    if (targetElement && targetElement.classList.contains("tile")) {
      const targetIndex = parseInt(targetElement.getAttribute("data-index"));
      if (!isNaN(targetIndex)) {
        // In single-turn mode, don't set hover state on correct tiles
        if (mode === "single-turn") {
          const targetValue = tiles[targetIndex].value;
          if (
            targetIndex in tilesShownCorrect &&
            tilesShownCorrect[targetIndex] === targetValue
          ) {
            hoveredIndex = null;
            return;
          }
        }
        hoveredIndex = targetIndex;
      }
    }
  }

  function handleDragLeave(event) {
    // Clear hover state when leaving a tile
    if (
      !event.relatedTarget ||
      !event.relatedTarget.classList.contains("tile")
    ) {
      hoveredIndex = null;
    }
  }

  function handleDrop(event, targetIndex) {
    preventDefaultIfPossible(event);
    swapTiles(targetIndex);
    hoveredIndex = null;
  }

  // Touch event handlers
  function handleTouchStart(event, tileIndex) {
    // In single-turn mode, don't allow touch interaction with tiles that were previously correct
    if (mode === "single-turn") {
      const currentValue = tiles[tileIndex].value;
      if (
        tileIndex in tilesShownCorrect &&
        tilesShownCorrect[tileIndex] === currentValue
      ) {
        return;
      }
    }

    // Trigger first interaction callback for wake lock
    onFirstInteraction();

    draggedTile = tiles[tileIndex];
    draggedIndex = tileIndex;
    touchStartTime = Date.now();
    hasTouchMoved = false;
    touchStartPosition = {
      x: event.touches[0].clientX,
      y: event.touches[0].clientY,
    };
    // Don't set isDragging immediately - wait for movement
    currentTouchPosition = {
      x: event.touches[0].clientX,
      y: event.touches[0].clientY,
    };
  }

  function handleTouchMove(event) {
    if (draggedIndex === null || !touchStartPosition) return;

    const currentX = event.touches[0].clientX;
    const currentY = event.touches[0].clientY;

    // Calculate movement distance
    const deltaX = Math.abs(currentX - touchStartPosition.x);
    const deltaY = Math.abs(currentY - touchStartPosition.y);
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

    // If moved significantly, start dragging
    if (distance > 10 && !hasTouchMoved) {
      hasTouchMoved = true;
      isDragging = true;
      dragStartTime = Date.now();
      event.preventDefault(); // Prevent scrolling only when dragging
    }

    if (isDragging) {
      event.preventDefault(); // Prevent scrolling - now safe since we use non-passive listeners
      currentTouchPosition = {
        x: currentX,
        y: currentY,
      };

      // Find which tile is being hovered over during touch drag
      const elementBelow = document.elementFromPoint(currentX, currentY);

      if (elementBelow && elementBelow.classList.contains("tile")) {
        const targetIndex = parseInt(elementBelow.getAttribute("data-index"));
        if (!isNaN(targetIndex)) {
          // In single-turn mode, don't set hover state on correct tiles
          if (mode === "single-turn") {
            const targetValue = tiles[targetIndex].value;
            if (
              targetIndex in tilesShownCorrect &&
              tilesShownCorrect[targetIndex] === targetValue
            ) {
              hoveredIndex = null;
              return;
            }
          }
          hoveredIndex = targetIndex;
        }
      } else {
        hoveredIndex = null;
      }
    }
  }

  function handleTouchEnd(event) {
    if (draggedIndex === null || !touchStartPosition) return;

    // If this was a tap (no significant movement), handle as click
    if (!hasTouchMoved && touchStartTime && Date.now() - touchStartTime < 300) {
      handleTileClick(event, draggedIndex);
      lastTouchHandled = Date.now(); // Set after handling to prevent synthetic click
    } else if (isDragging) {
      // Handle as drag operation
      const touch = event.changedTouches[0];
      const elementBelow = document.elementFromPoint(
        touch.clientX,
        touch.clientY
      );

      if (elementBelow && elementBelow.classList.contains("tile")) {
        const targetIndex = parseInt(elementBelow.getAttribute("data-index"));
        if (!isNaN(targetIndex)) {
          swapTiles(targetIndex);
        }
      }
    }

    // Reset touch state
    touchStartPosition = null;
    touchStartTime = null;
    hasTouchMoved = false;
    isDragging = false;
    currentTouchPosition = null;
    hoveredIndex = null;
    draggedTile = null;
    draggedIndex = null;
    dragStartTime = null;
  }

  function swapTiles(targetIndex) {
    if (draggedIndex !== null && draggedIndex !== targetIndex) {
      // In single-turn mode, don't allow swapping with tiles that were previously correct
      if (mode === "single-turn") {
        const targetValue = tiles[targetIndex].value;
        if (
          targetIndex in tilesShownCorrect &&
          tilesShownCorrect[targetIndex] === targetValue
        ) {
          // Reset drag state without swapping
          draggedTile = null;
          draggedIndex = null;
          dragStartTime = null;
          return;
        }
      }

      // Don't swap if both tiles have the same value (no effect on grid)
      if (tiles[draggedIndex].value === tiles[targetIndex].value) {
        // Reset drag state without swapping
        draggedTile = null;
        draggedIndex = null;
        dragStartTime = null;
        return;
      }

      // Swap tiles in the array - this changes their positions while keeping stable keys
      const newTiles = [...tiles];
      [newTiles[draggedIndex], newTiles[targetIndex]] = [
        newTiles[targetIndex],
        newTiles[draggedIndex],
      ];

      tiles = newTiles;

      // Update currentGrid
      updateCurrentGrid();

      // Get row/col for recently swapped highlighting
      const draggedPos = indexToRowCol(draggedIndex);
      const targetPos = indexToRowCol(targetIndex);

      // Highlight the swapped positions
      recentlySwapped = [
        { row: draggedPos.row, col: draggedPos.col },
        { row: targetPos.row, col: targetPos.col },
      ];

      // Clear the highlight after animation
      setTimeout(() => {
        recentlySwapped = [];
      }, 800);
    }

    draggedTile = null;
    draggedIndex = null;
    dragStartTime = null;
  }

  function getTileClasses(tileIndex, value) {
    const { row, col } = indexToRowCol(tileIndex);
    let classes = ["tile"];

    // Add drag/interaction classes
    if (isDragging && draggedIndex === tileIndex) {
      classes.push("dragging");
    }

    // Only add hover effect if not a correct tile in single-turn mode
    if (
      hoveredIndex === tileIndex &&
      draggedIndex !== tileIndex &&
      !(
        mode === "single-turn" &&
        tileIndex in tilesShownCorrect &&
        tilesShownCorrect[tileIndex] === value
      )
    ) {
      classes.push("drag-hover");
    }

    if (recentlySwapped.some((pos) => pos.row === row && pos.col === col)) {
      classes.push("recently-swapped");
    }

    if (clickedTiles.some((pos) => pos.row === row && pos.col === col)) {
      classes.push("clicked-pulse");
    }

    // Handle immediate feedback (highest priority)
    if (feedback?.[row]?.[col] !== undefined) {
      if (feedback[row][col]) {
        classes.push(
          tileIndex in tilesShownCorrect &&
            tilesShownCorrect[tileIndex] === value
            ? "feedback-correct"
            : "feedback-correct-new"
        );
      }
      return classes.join(" ");
    }

    // Handle previously correct tiles
    if (
      tileIndex in tilesShownCorrect &&
      tilesShownCorrect[tileIndex] === value
    ) {
      classes.push("correct-previous");
      return classes.join(" ");
    }

    // Handle previously incorrect tiles
    if (
      tileIndex in tilesShownWrong &&
      tilesShownWrong[tileIndex].includes(value)
    ) {
      classes.push("incorrect-previous");
    }

    // Handle duplicates (checked separately)
    const inRow = currentGrid[row].filter((v) => v === value).length > 1;
    const inCol = currentGrid.some(
      (r) => r[col] === value && r !== currentGrid[row]
    );
    const hasDuplicates = inRow || inCol;

    if (hasDuplicates) {
      classes.push("duplicate");
    }

    return classes.join(" ");
  }

  // Handle tile click to increment value
  async function handleTileClick(event, tileIndex) {
    // In single-turn mode, don't allow clicks on tiles that were previously correct
    if (mode === "single-turn") {
      const currentValue = tiles[tileIndex].value;
      if (
        tileIndex in tilesShownCorrect &&
        tilesShownCorrect[tileIndex] === currentValue
      ) {
        return; // Don't allow interaction with previously correct tiles
      }
    }

    // Prevent double handling from touch + click events (short window for synthetic clicks)
    const now = Date.now();
    if (now - lastTouchHandled < 100) {
      return;
    }

    // Don't process click if we were dragging
    if (dragStartTime && now - dragStartTime < 200) {
      return;
    }

    // Trigger first interaction callback for wake lock
    onFirstInteraction();

    const tile = tiles[tileIndex];
    const { row, col } = indexToRowCol(tileIndex);

    // Increment value: 1->2->3->...->gridSize->0->1
    let newValue;
    if (tile.value === 0) {
      newValue = 1;
    } else if (tile.value >= gridSize) {
      newValue = 1;
    } else {
      newValue = tile.value + 1;
    }

    // Update the tile value
    const newTiles = [...tiles];
    newTiles[tileIndex] = { ...tile, value: newValue };
    tiles = newTiles;

    // Update the grid
    updateCurrentGrid();

    // Remove any existing pulse for this tile to force reflow
    clickedTiles = clickedTiles.filter(
      (ct) => ct.row !== row || ct.col !== col
    );
    await tick(); // Wait for DOM update

    // Add pulse effect
    clickedTiles = [...clickedTiles, { row, col, timestamp: Date.now() }];

    // Remove pulse effect after animation
    setTimeout(() => {
      clickedTiles = clickedTiles.filter(
        (ct) => ct.row !== row || ct.col !== col
      );
    }, 300); // match the animation duration
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
  <div class="instruction-label">{$_("dragTilesInstruction")}</div>
  <div
    class="grid"
    style="--grid-size: {gridSize}; --border-radius: {borderRadius}px"
  >
    {#each tiles as tile, index (tile.id)}
      {@const { row, col } = indexToRowCol(index)}
      <div
        class={getTileClasses(index, tile.value)}
        draggable="true"
        data-index={index}
        data-row={row}
        data-col={col}
        animate:flip={{ duration: draggedIndex === index ? 0 : 300 }}
        ondragstart={(e) => handleDragStart(e, index)}
        ondragover={handleDragOver}
        ondragenter={handleDragEnter}
        ondragleave={handleDragLeave}
        ondrop={(e) => handleDrop(e, index)}
        ontouchstart={(e) => handleTouchStart(e, index)}
        ontouchend={handleTouchEnd}
        onclick={(e) => handleTileClick(e, index)}
        onkeydown={(e) => handleTileClick(e, index)}
        role="gridcell"
        tabindex="0"
        aria-label="Tile at row {row + 1}, column {col + 1}, value {tile.value}"
      >
        {tile.value}
      </div>
    {/each}
  </div>

  <!-- Undo Button -->
  <button
    onclick={undoGridChange}
    class="undo-btn"
    disabled={!canUndo || isTransitioning}
  >
    ↶ Undo
  </button>

  <!-- Dragging tile overlay -->
  {#if isDragging && currentTouchPosition && draggedTile}
    <div
      class="dragging-tile"
      style="left: {currentTouchPosition.x -
        draggingTileSize / 2}px; top: {currentTouchPosition.y -
        draggingTileSize /
          2}px; width: {draggingTileSize}px; height: {draggingTileSize}px;"
    >
      {draggedTile.value}
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

  .undo-btn {
    background: #f8f9fa;
    color: #6c757d;
    border: 1px solid #dee2e6;
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    width: 95%;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
  }

  .undo-btn:hover:not(:disabled) {
    background: #e9ecef;
    color: #495057;
    border-color: #adb5bd;
  }

  .undo-btn:disabled {
    background: #f8f9fa;
    color: #adb5bd;
    border-color: #dee2e6;
    cursor: not-allowed;
    opacity: 0.6;
  }

  .grid {
    display: flex;
    flex-wrap: wrap;
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

  .dragging-tile {
    position: fixed;
    /* Size will be set via inline styles */
    background: white;
    border: 1px solid #e1e5e9;
    border-radius: var(--border-radius, 10px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: clamp(1rem, 4vw, 1.5rem);
    font-weight: 600;
    color: #2c3e50;
    pointer-events: none;
    z-index: 1000;
    transform: translateZ(0);
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
    border-radius: var(--border-radius, 10px);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    cursor: grab;
    /* Only transition box-shadow, background, and color, not transform */
    transition:
      box-shadow 0.2s,
      background 0.2s,
      color 0.2s;
    user-select: none;
    touch-action: none;
    /* Prevent layout shifts from transforms */
    transform: translateZ(0);
    will-change: transform;
    /* Ensure transforms don't break layout */
    position: relative;
    /* Create isolation context to contain transforms */
    isolation: isolate;
    /* Flexbox sizing for square tiles */
    width: calc((100% - (var(--grid-size) - 1) * 2px) / var(--grid-size));
    height: calc((100% - (var(--grid-size) - 1) * 2px) / var(--grid-size));
    flex-shrink: 0;
  }

  .tile:hover {
    background: #f8f9fa;
    transform: translateZ(0) scale(1.02);
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
  }

  .tile:active {
    cursor: grabbing;
    transform: translateZ(0) scale(0.98);
  }

  /* Dragging states */
  .tile.dragging {
    opacity: 0.3;
  }

  /* Hover state during drag operations - different styles for different grid sizes */
  .tile.drag-hover {
    background: #e3f2fd !important;
    border-color: #2196f3 !important;
    /* More pronounced raise effect with proper isolation */
    transform: translateZ(0) translateY(-4px) scale(1.02) !important;
    box-shadow: 0 8px 16px rgba(52, 152, 219, 0.4) !important;
    z-index: 10;
    transition: all 0.15s ease !important;
  }

  /* Recently swapped tiles pulse effect */
  .tile.recently-swapped {
    animation: swapPulse 0.8s ease-out;
    z-index: 20;
  }

  /* Clicked tiles pulse effect */
  .tile.clicked-pulse {
    animation: clickPulse 0.22s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 15;
  }

  @keyframes swapPulse {
    0% {
      transform: translateZ(0) scale(1);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    50% {
      transform: translateZ(0) scale(1.05);
      box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);
    }
    100% {
      transform: translateZ(0) scale(1);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
  }

  @keyframes clickPulse {
    0% {
      transform: translateZ(0) scale(1);
    }
    50% {
      transform: translateZ(0) scale(1.15);
    }
    100% {
      transform: translateZ(0) scale(1);
    }
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
      font-size: clamp(1.2rem, 5vw, 1.8rem);
    }

    .dragging-tile {
      font-size: clamp(1.2rem, 5vw, 1.8rem);
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

  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .instruction-label {
      color: #aaa;
    }

    .tile {
      background: #2a2a2a;
      color: #ffffff;
      border: 1px solid #555;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    }
    .dragging-tile {
      background: #2a2a2a;
      border: 1px solid #555;
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    }
    .tile:hover {
      background: #333;
      box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
    }
    .tile.drag-hover {
      background: #1a4c7d !important;
      border-color: #2196f3 !important;
      box-shadow: 0 8px 16px rgba(52, 152, 219, 0.6) !important;
    }
    .tile.duplicate {
      background: #2a2a2a;
      color: #cf5910;
      font-weight: 700;
    }
    .tile.incorrect-previous {
      background: #dbd17a;
      color: #504f4c;
      font-weight: 700;
    }
    .tile.incorrect-previous.duplicate {
      background: #dbd17a;
      color: #b64e0e;
      font-weight: 700;
    }

    .undo-btn {
      background: #2a2a2a;
      color: #888;
      border: 1px solid #555;
    }

    .undo-btn:hover:not(:disabled) {
      background: #333;
      color: #bbb;
      border-color: #666;
    }

    .undo-btn:disabled {
      background: #1a1a1a;
      color: #555;
      border-color: #333;
    }
  }
</style>
