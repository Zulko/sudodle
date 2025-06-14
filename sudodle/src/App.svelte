<script>
  import { onMount } from "svelte";
  import { _, locale, locales, isLoading } from "svelte-i18n";
  import "./lib/i18n.js";
  import {
    cyclicLatinSquare,
    uniformRandomLatinSquare,
    checkLatinSquare,
  } from "./lib/latinSquares.js";
  import Settings from "./components/Settings.svelte";
  import VictorySection from "./components/VictorySection.svelte";
  import CurrentGrid from "./components/CurrentGrid.svelte";
  import PreviousGrid from "./components/PreviousGrid.svelte";
  import LanguageFlags from "./components/LanguageFlags.svelte";

  // State management using $state
  let settings = $state({
    gridSize: 5,
    strictMode: false,
    seed: null,
    mode: "single-turn", // "guesses" or "single-turn"
    puzzleId: null,
    difficulty: "normal", // "normal", "hard", "expert"
  });

  let solutionGrid = $state([]);
  let currentGrid = $state([]);
  let previousGrids = $state([]);
  let gameState = $state("playing"); // 'playing', 'won'
  let currentTurn = $state(1);
  let maxGuesses = $state(6);
  let showSettingsModal = $state(false);
  let isTransitioning = $state(false);
  let currentGridFeedback = $state(null);
  let puzzles = $state(null);
  let tStart = $state(null);
  let gameEndTime = $state(null);

  // Tile indices for visual cues
  let tilesShownCorrect = $state({}); // {tileIndex: valueShownCorrectAtThisPosition}
  let tilesShownWrong = $state({}); // {tileIndex: [tile values shown wrong at this position]}

  // Create derived values to ensure reactivity
  let tilesCorrectForGrid = $derived(tilesShownCorrect);
  let tilesWrongForGrid = $derived(tilesShownWrong);

  // Derived values using $derived
  let isCheckDisabled = $derived(
    isTransitioning ||
      (settings.strictMode && !checkLatinSquare(currentGrid)) ||
      maxGuesses - currentTurn <= 0
  );

  let outOfTries = $derived(
    gameState === "playing" && maxGuesses - currentTurn <= 0
  );

  // Derived timing values
  let elapsedTimeFormatted = $derived(() => {
    if (!tStart || !gameEndTime) return "";

    const elapsedMs = gameEndTime - tStart;
    const totalSeconds = Math.floor(elapsedMs / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    return `${minutes}m:${seconds.toString().padStart(2, "0")}s`;
  });

  // Component lifecycle
  onMount(async () => {
    await parseURLparams();
    // Wait for i18n to be ready before starting the game
    const unsubscribe = isLoading.subscribe((loading) => {
      if (!loading) {
        startGame();
        unsubscribe();
      }
    });
  });

  // Handle mode change effects
  $effect(() => {
    if (settings.mode === "single-turn") {
      // If current grid size is not valid for single-turn, reset to 6
      if (settings.gridSize > 7) {
        settings.gridSize = 6;
      }
    }
  });

  // Watch for grid changes in single-turn mode
  $effect(() => {
    if (settings.mode === "single-turn" && currentGrid.length > 0) {
      autoCheckSingleTurn();
    }
  });

  // ===== URL/Parameter Management =====
  async function parseURLparams() {
    const urlParams = new URLSearchParams(window.location.search);

    if (urlParams.has("gridSize")) {
      settings.gridSize = parseInt(urlParams.get("gridSize"));
    }
    if (urlParams.has("strictMode")) {
      settings.strictMode = urlParams.get("strictMode") === "true";
    }
    if (urlParams.has("seed")) {
      settings.seed = parseInt(urlParams.get("seed"));
      settings.mode = "guesses";
    }
    if (urlParams.has("puzzleId")) {
      settings.puzzleId = urlParams.get("puzzleId");
      settings.gridSize = parseInt(settings.puzzleId[0]);
      settings.mode = "single-turn";
      puzzles = await loadPuzzles();
      for (const difficulty of ["normal", "hard", "expert"]) {
        if (
          puzzles[settings.gridSize][difficulty]?.includes(settings.puzzleId)
        ) {
          settings.difficulty = difficulty;
          break;
        }
      }
    }
  }

  function updateURL() {
    const params = new URLSearchParams();
    if (settings.puzzleId) {
      params.set("puzzleId", settings.puzzleId.toString());
    } else {
      params.set("gridSize", settings.gridSize.toString());
      params.set("strictMode", settings.strictMode.toString());
      if (settings.seed) {
        params.set("seed", settings.seed.toString());
      }
    }
    const newURL = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, "", newURL);
  }

  // ===== Grid Generation =====
  async function generateSolutionGrid() {
    if (!settings.seed) {
      settings.seed = Math.floor(Math.random() * 1000000);
    }
    solutionGrid = uniformRandomLatinSquare(settings.gridSize, settings.seed);
  }

  async function pickPuzzle() {
    if (!puzzles) {
      puzzles = await loadPuzzles();
    }
    const puzzlesForGridSizeAndDifficulty =
      puzzles[settings.gridSize]?.[settings.difficulty];

    if (
      !puzzlesForGridSizeAndDifficulty ||
      puzzlesForGridSizeAndDifficulty.length === 0
    ) {
      console.error(
        `No puzzles found for grid size ${settings.gridSize} and difficulty ${settings.difficulty}`
      );
      return;
    }
    const index = Math.floor(
      Math.random() * puzzlesForGridSizeAndDifficulty.length
    );
    settings.puzzleId = puzzlesForGridSizeAndDifficulty[index];
  }

  function initializeGridFromPuzzleId() {
    // Function to convert character to tile index
    function charToIndex(char) {
      if (char >= "0" && char <= "9") {
        return parseInt(char);
      } else if (char >= "A" && char <= "Z") {
        return char.charCodeAt(0) - "A".charCodeAt(0) + 10;
      } else if (char >= "a" && char <= "z") {
        return char.charCodeAt(0) - "a".charCodeAt(0) + 36;
      }
      return 0; // fallback
    }

    // Decode the puzzle ID to get tile indices
    const puzzle = [];
    for (let i = 1; i < settings.puzzleId.length; i++) {
      puzzle.push(charToIndex(settings.puzzleId[i]));
    }

    // Initialize correct tiles based on puzzle indices
    tilesShownCorrect = puzzle.reduce((acc, tileIndex) => {
      if (tileIndex < settings.gridSize * settings.gridSize) {
        const row = Math.floor(tileIndex / settings.gridSize);
        const col = tileIndex % settings.gridSize;
        acc[tileIndex] = currentGrid[row][col];
      }
      return acc;
    }, {});

    // Initialize objects to track incorrect tiles
    const wrongTiles = {};

    // The puzzle contains tile indices that should be marked as correct
    // Mark all OTHER positions (not in puzzle) as wrong
    for (
      let tileIndex = 0;
      tileIndex < settings.gridSize * settings.gridSize;
      tileIndex++
    ) {
      if (!puzzle.includes(tileIndex)) {
        const row = Math.floor(tileIndex / settings.gridSize);
        const col = tileIndex % settings.gridSize;
        const currentValue = currentGrid[row][col];
        wrongTiles[tileIndex] = [currentValue];
      }
    }

    // Update the tile tracking objects
    tilesShownWrong = wrongTiles;
  }

  async function loadPuzzles() {
    return fetch("puzzles.csv")
      .then((response) => response.text())
      .then((text) => {
        const puzzles = {};
        const lines = text.trim().split("\n");

        lines.forEach((line) => {
          if (line.length > 0) {
            const parts = line.split(",");
            if (parts.length >= 2) {
              const compactedPuzzle = parts[0];
              const difficulty = parts[1];
              const gridSize = parseInt(compactedPuzzle[0]);

              // Initialize nested structure for this grid size and difficulty if it doesn't exist
              if (!puzzles[gridSize]) {
                puzzles[gridSize] = {};
              }
              if (!puzzles[gridSize][difficulty]) {
                puzzles[gridSize][difficulty] = [];
              }

              puzzles[gridSize][difficulty].push(compactedPuzzle);
            }
          }
        });

        return puzzles;
      });
  }

  // ===== Visual Cues Update =====
  function updateVisualCues() {
    if (currentGrid.length === 0) {
      tilesShownCorrect = {};
      tilesShownWrong = {};
      return;
    }

    const correctTiles = {};
    const wrongTiles = {};

    for (let row = 0; row < settings.gridSize; row++) {
      for (let col = 0; col < settings.gridSize; col++) {
        const index = row * settings.gridSize + col;
        const currentValue = currentGrid[row]?.[col];

        // Find what value was previously shown as correct at this position
        let previouslyCorrectValue = null;
        for (const prevGrid of previousGrids) {
          if (prevGrid.feedback?.[row]?.[col]) {
            previouslyCorrectValue = prevGrid.grid[row][col];
            break; // Once we find a correct value, we can stop
          }
        }

        // If current value matches a previously correct value at this position
        if (
          previouslyCorrectValue !== null &&
          currentValue === previouslyCorrectValue
        ) {
          correctTiles[index] = currentValue;
        }

        // Collect all values that were incorrect at this position in previous attempts
        const incorrectValues = [];
        previousGrids.forEach((prevGrid) => {
          if (
            prevGrid.feedback?.[row] &&
            !prevGrid.feedback[row][col] &&
            !incorrectValues.includes(prevGrid.grid[row][col])
          ) {
            incorrectValues.push(prevGrid.grid[row][col]);
          }
        });

        // Only show as wrong if current value was previously shown as wrong at this position
        if (incorrectValues.includes(currentValue)) {
          wrongTiles[index] = incorrectValues;
        }
      }
    }
    tilesShownCorrect = correctTiles;
    tilesShownWrong = wrongTiles;
  }

  // ===== Game Flow/Logic =====
  async function startGame() {
    gameState = "playing";
    tStart = Date.now();
    gameEndTime = null;
    currentGrid = cyclicLatinSquare(settings.gridSize);
    previousGrids = [];

    if (settings.mode === "single-turn") {
      if (!settings.puzzleId) {
        await pickPuzzle();
      }
      initializeGridFromPuzzleId();
    } else {
      await generateSolutionGrid();
      currentTurn = 1;
      checkGridGuess();
      updateVisualCues();
    }
    updateURL();
  }

  function checkGridGuess() {
    const feedback = [];
    for (let i = 0; i < settings.gridSize; i++) {
      const row = [];
      for (let j = 0; j < settings.gridSize; j++) {
        row.push(currentGrid[i][j] === solutionGrid[i][j]);
      }
      feedback.push(row);
    }

    // Check if all tiles are correct (victory)
    const allCorrect = feedback.every((row) => row.every((cell) => cell));

    if (allCorrect) {
      // Immediately show feedback on current grid
      currentGridFeedback = feedback;
      isTransitioning = true;
      gameEndTime = Date.now();

      // After 1 second, move winning grid to previous grids and show victory
      setTimeout(() => {
        // Add the winning grid to previous grids with all-correct feedback
        previousGrids = [
          ...previousGrids,
          {
            grid: currentGrid.map((row) => [...row]),
            feedback: feedback,
            turn: currentTurn,
          },
        ];
        gameState = "won";
        currentGridFeedback = null;
        isTransitioning = false;

        // Scroll to victory section
        setTimeout(() => {
          window.scrollTo({
            top: document.documentElement.scrollHeight,
            behavior: "smooth",
          });
        }, 100); // Small delay to ensure DOM has updated
      }, 1000);
    } else if (currentTurn >= maxGuesses) {
      // Game over - could add this state later
      gameState = "won"; // For now, treat as won
    } else {
      // Immediately show feedback on current grid
      currentGridFeedback = feedback;
      isTransitioning = true;

      // After 1 second, move current grid to previous grids and show new grid
      setTimeout(() => {
        // Add current grid to previous grids with feedback
        previousGrids = [
          ...previousGrids,
          {
            grid: currentGrid.map((row) => [...row]),
            feedback: feedback,
            turn: currentTurn,
          },
        ];

        // Start next turn
        currentTurn++;
        // Initialize next grid with current grid as starting point
        currentGrid = currentGrid.map((row) => [...row]);
        currentGridFeedback = null;
        isTransitioning = false;

        // Update visual cues for the new turn
        updateVisualCues();

        // Scroll to bottom to keep current grid in view
        if (previousGrids.length > 1) {
          setTimeout(() => {
            window.scrollTo({
              top: document.documentElement.scrollHeight,
              behavior: "instant",
            });
          }, 2); // Small delay to ensure DOM has updated
        }
      }, 500);
    }

    // Update visual cues at the end of checkGridGuess
    updateVisualCues();
  }

  function autoCheckSingleTurn() {
    if (settings.mode !== "single-turn") return;

    // Only check for completion if there are wrong tiles to validate against
    if (Object.keys(tilesShownWrong).length === 0) return;

    // Check if current grid is a valid Latin square
    const isValidLatinSquare = checkLatinSquare(currentGrid);

    if (!isValidLatinSquare) return;

    // Check that no tile values correspond to tilesShownWrong
    const hasWrongTiles = currentGrid.some((row, i) =>
      row.some((cell, j) => {
        const tileIndex = i * settings.gridSize + j;
        return (
          tilesShownWrong[tileIndex] &&
          tilesShownWrong[tileIndex].includes(cell)
        );
      })
    );

    const isComplete = !hasWrongTiles;

    if (isComplete) {
      // Game won in single-turn mode
      const feedback = currentGrid.map((row) => row.map(() => true));

      currentGridFeedback = feedback;
      isTransitioning = true;
      gameEndTime = Date.now();

      setTimeout(() => {
        previousGrids.push({
          grid: currentGrid.map((row) => [...row]),
          feedback: feedback,
          turn: currentTurn,
        });
        gameState = "won";
        currentGridFeedback = null;
        isTransitioning = false;

        setTimeout(() => {
          window.scrollTo({
            top: document.documentElement.scrollHeight,
            behavior: "smooth",
          });
        }, 100);
      }, 1000);
    }
  }

  function newGame() {
    settings.seed = null;
    settings.puzzleId = null;
    previousGrids = [];
    currentTurn = 1;
    showSettingsModal = false;

    startGame();
  }

  // ===== UI/Modal Management =====
  function showNewGameModal() {
    showSettingsModal = true;
  }

  function hideSettingsModal() {
    showSettingsModal = false;
  }

  // ===== Sharing/External =====
  function shareGame() {
    const gameURL = window.location.href;
    let title = $_("shareTitle");
    if (gameState === "won") {
      const timeString = elapsedTimeFormatted();
      if (settings.mode === "single-turn") {
        title = $_("shareWinTitleSingleTurn", {
          values: { time: timeString },
        });
      } else {
        title = $_("shareWinTitleGuesses", {
          values: { time: timeString, count: previousGrids.length },
        });
      }
    }
    if (navigator.share) {
      navigator.share({
        title: title,
        url: gameURL,
      });
    } else {
      navigator.clipboard.writeText(gameURL);
      alert($_("urlCopied"));
    }
  }
</script>

{#if $isLoading}
  <div class="loading">
    <div class="loading-spinner"></div>
    <p>Loading...</p>
  </div>
{:else}
  <main>
    <LanguageFlags />

    <div class="container">
      <h1>{$_("title")}</h1>

      <div class="rules">
        <p>
          {settings.mode === "guesses"
            ? $_("rulesGuesses")
            : $_("rulesSingleTurn")}
        </p>
      </div>

      <section class="game">
        <!-- Previous Grids -->
        {#if previousGrids.length > 1 || gameState === "won"}
          {#each previousGrids as prevGrid (prevGrid.turn)}
            <div class="previous-grid">
              <PreviousGrid previousGrid={prevGrid} />
            </div>
          {/each}
        {/if}

        <!-- Current/Final Grid -->
        {#if gameState === "playing"}
          <div class="current-grid">
            <CurrentGrid
              bind:currentGrid
              tilesShownCorrect={tilesCorrectForGrid}
              tilesShownWrong={tilesWrongForGrid}
              feedback={currentGridFeedback}
              mode={settings.mode}
              {isTransitioning}
            />

            {#if settings.mode === "guesses"}
              <button
                onclick={checkGridGuess}
                class="primary-btn check-btn {isTransitioning
                  ? 'transitioning'
                  : ''}"
                disabled={isCheckDisabled}
              >
                {isTransitioning
                  ? $_("checking")
                  : settings.strictMode && !checkLatinSquare(currentGrid)
                    ? $_("cannotCheck")
                    : maxGuesses - currentTurn <= 0
                      ? $_("outOfGuesses")
                      : $_("checkWithGuesses", {
                          values: { count: maxGuesses - currentTurn },
                        })}
              </button>
            {/if}
          </div>
        {/if}

        <!-- Victory Screen -->
        {#if gameState === "won"}
          <VictorySection
            onNewGame={showNewGameModal}
            onShareGame={shareGame}
            guessCount={previousGrids.length}
            elapsedTime={elapsedTimeFormatted()}
            gameMode={settings.mode}
          />
        {/if}

        <!-- Discrete New Game button for during gameplay -->
        {#if gameState === "playing"}
          <div class="bottom-actions">
            <button
              onclick={showNewGameModal}
              class="discrete-btn {outOfTries ? 'out-of-tries' : ''}"
            >
              ↻ {$_("newGame")}
            </button>
            <button onclick={shareGame} class="discrete-btn share-btn">
              🔗 {$_("shareThisPuzzle")}
            </button>
          </div>
        {/if}
      </section>
    </div>
  </main>

  {#if showSettingsModal}
    <Settings
      bind:mode={settings.mode}
      bind:gridSize={settings.gridSize}
      bind:strictMode={settings.strictMode}
      bind:difficulty={settings.difficulty}
      onStartGame={newGame}
      onCancel={hideSettingsModal}
    />
  {/if}
{/if}

<style>
  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto",
      sans-serif;
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  .loading p {
    color: #666;
    font-size: 1rem;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  .container {
    max-width: 400px;
    margin: 0 auto;
    padding: 1rem;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto",
      sans-serif;
  }

  h1 {
    text-align: center;
    color: #2c3e50;
    margin-top: 0;
    margin-bottom: 2rem;
    font-size: 2.5rem;
  }

  .rules {
    margin-bottom: 2rem;
  }

  .rules p {
    line-height: 1.6;
    margin-bottom: 1.5rem;
    color: #555;
    text-align: left;
  }

  .previous-grid,
  .current-grid {
    margin-bottom: 2rem;
    /* Prevent layout shifts during transitions */
    position: relative;
    width: 100%;
  }

  .primary-btn {
    background: #3498db;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
    width: 100%;
    margin-bottom: 0.5rem;
  }

  .primary-btn:hover {
    background: #2980b9;
  }

  .primary-btn:disabled,
  .primary-btn.transitioning {
    background: #ffffff;
    color: #7f8c8d;
    border: 1px solid #ddd;
    cursor: not-allowed;
    opacity: 1;
  }

  .primary-btn:disabled:hover,
  .primary-btn.transitioning:hover {
    background: #ffffff;
    color: #7f8c8d;
  }

  .bottom-actions {
    margin-top: 3rem;
    text-align: center;
    display: flex;
    gap: 0.75rem;
    justify-content: center;
    flex-wrap: wrap;
  }

  .discrete-btn {
    background: #fafafa;
    color: #999;
    border: 1px solid #eee;
    padding: 0.4rem 0.8rem;
    border-radius: 0.25rem;
    font-size: 0.8rem;
    font-weight: 400;
    cursor: pointer;
    transition: all 0.2s;
    flex: 0 1 auto;
    white-space: nowrap;
  }

  .discrete-btn:hover {
    background: #f5f5f5;
    color: #777;
    border-color: #ddd;
  }

  .discrete-btn.out-of-tries {
    background: #3498db;
    color: white;
    border: 1px solid #3498db;
    font-weight: 500;
  }

  .discrete-btn.out-of-tries:hover {
    background: #2980b9;
    border-color: #2980b9;
  }

  .discrete-btn.share-btn {
    background: #fafafa;
    color: #999;
    border: 1px solid #eee;
  }

  .discrete-btn.share-btn:hover {
    background: #222;
    color: #888;
    border-color: #444;
  }

  /* Responsive design */
  @media (max-width: 480px) {
    .container {
      padding: 0.5rem;
    }

    h1 {
      font-size: 2rem;
    }

    .bottom-actions {
      gap: 0.5rem;
    }
  }

  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .loading {
      background-color: #0f0f0f;
      color: #ffffff;
    }

    .loading p {
      color: #ccc;
    }

    .container {
      background-color: #0f0f0f;
      color: #ffffff;
    }

    h1 {
      color: #ffffff;
    }

    .rules p {
      color: #ccc;
    }

    .primary-btn:disabled,
    .primary-btn.transitioning {
      background: #2a2a2a;
      color: #888;
      border: 1px solid #555;
    }

    .primary-btn:disabled:hover,
    .primary-btn.transitioning:hover {
      background: #2a2a2a;
      color: #888;
    }

    .discrete-btn {
      background: #1a1a1a;
      color: #666;
      border: 1px solid #333;
    }

    .discrete-btn:hover {
      background: #222;
      color: #888;
      border-color: #444;
    }

    .discrete-btn.out-of-tries {
      background: #3498db;
      color: white;
      border: 1px solid #3498db;
    }

    .discrete-btn.out-of-tries:hover {
      background: #2980b9;
      border-color: #2980b9;
    }

    .discrete-btn.share-btn {
      background: #1a1a1a;
      color: #666;
      border: 1px solid #333;
    }

    .discrete-btn.share-btn:hover {
      background: #222;
      color: #888;
      border-color: #444;
    }
  }
</style>
