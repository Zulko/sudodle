<script>
  import { onMount } from "svelte";
  import { cyclicLatinSquare, checkLatinSquare } from "./lib/latinSquares.js";
  import Settings from "./components/Settings.svelte";
  import ConfirmNewGame from "./components/ConfirmNewGame.svelte";
  import VictorySection from "./components/VictorySection.svelte";
  import CurrentGrid from "./components/CurrentGrid.svelte";
  import PreviousGrid from "./components/PreviousGrid.svelte";

  // State management
  let settings = {
    gridSize: 5,
    strictMode: false,
    visualCues: true,
  };

  let solutionGrid = [];
  let currentGrid = [];
  let previousGrids = [];
  let gameState = "setup"; // 'setup', 'playing', 'won'
  let currentTurn = 1;
  let maxGuesses = 6;
  let seed = null;
  let showConfirmNewGame = false;
  let isTransitioning = false;
  let currentGridFeedback = null;

  // Reactive statement to check if check button should be disabled
  $: isCheckDisabled =
    isTransitioning || (settings.strictMode && !checkLatinSquare(currentGrid));

  // URL parameter handling
  onMount(() => {
    const urlParams = new URLSearchParams(window.location.search);

    if (urlParams.has("gridSize")) {
      settings.gridSize = parseInt(urlParams.get("gridSize"));
    }
    if (urlParams.has("strictMode")) {
      settings.strictMode = urlParams.get("strictMode") === "true";
    }
    if (urlParams.has("visualCues")) {
      settings.visualCues = urlParams.get("visualCues") === "true";
    }
    if (urlParams.has("seed")) {
      seed = parseInt(urlParams.get("seed"));
    }

    // If we have URL parameters, skip to game
    if (urlParams.toString()) {
      startGame();
    }
  });

  // Grid generation functions
  function generateSolutionGrid() {
    // TODO: Implement proper random latin square generation
    // For now, use cyclic latin square as placeholder
    if (!seed) {
      seed = Math.floor(Math.random() * 1000000);
    }
    solutionGrid = cyclicLatinSquare(settings.gridSize);
  }

  function initializeCurrentGrid() {
    currentGrid = cyclicLatinSquare(settings.gridSize);
  }

  // Game flow functions
  function startGame() {
    gameState = "playing";
    generateSolutionGrid();
    initializeCurrentGrid();
    previousGrids = [];
    currentTurn = 1;
    updateURL();
  }

  function checkGrid() {
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

        // Scroll to bottom to keep current grid in view
        setTimeout(() => {
          window.scrollTo({
            top: document.documentElement.scrollHeight,
            behavior: "instant",
          });
        }, 2); // Small delay to ensure DOM has updated
      }, 1000);
    }
  }

  function newGame() {
    gameState = "setup";
    seed = null;
    previousGrids = [];
    currentTurn = 1;
    showConfirmNewGame = false;
  }

  function showNewGameConfirm() {
    showConfirmNewGame = true;
  }

  function hideNewGameConfirm() {
    showConfirmNewGame = false;
  }

  function updateURL() {
    const params = new URLSearchParams();
    params.set("gridSize", settings.gridSize.toString());
    params.set("strictMode", settings.strictMode.toString());
    params.set("visualCues", settings.visualCues.toString());
    if (seed) {
      params.set("seed", seed.toString());
    }

    const newURL = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, "", newURL);
  }

  function shareGame() {
    const gameURL = window.location.href;
    if (navigator.share) {
      navigator.share({
        title: "Sudodle Game",
        url: gameURL,
      });
    } else {
      navigator.clipboard.writeText(gameURL);
      alert("Game URL copied to clipboard!");
    }
  }
</script>

<main>
  <div class="container">
    <h1>Sudodle</h1>

    <div class="rules">
      <p>
        Guess the correct grid knowing that each number appears only once in
        each row and column (a Latin square). After each guess, you'll get
        feedback on which tiles are correct. Use this information to make your
        next guess!
      </p>
    </div>

    {#if gameState === "setup"}
      <Settings {settings} onStartGame={startGame} />
    {/if}

    {#if gameState === "playing" || gameState === "won"}
      <section class="game">
        <!-- Previous Grids -->
        {#each previousGrids as prevGrid (prevGrid.turn)}
          <div class="previous-grid">
            <PreviousGrid previousGrid={prevGrid} />
          </div>
        {/each}

        <!-- Current/Final Grid -->
        {#if gameState === "playing"}
          <div class="current-grid">
            <CurrentGrid
              bind:currentGrid
              visualCues={settings.visualCues}
              {previousGrids}
              {solutionGrid}
              feedback={currentGridFeedback}
            />
            <button
              onclick={checkGrid}
              class="primary-btn check-btn {isTransitioning
                ? 'transitioning'
                : ''}"
              disabled={isCheckDisabled}
            >
              {isTransitioning
                ? "Checking..."
                : settings.strictMode && !checkLatinSquare(currentGrid)
                  ? "Cannot check - fix the non-unique numbers"
                  : `Check (${maxGuesses - currentTurn} guesses left)`}
            </button>
          </div>
        {/if}

        <!-- Victory Screen -->
        {#if gameState === "won"}
          <VictorySection
            onNewGame={newGame}
            onShareGame={shareGame}
            guessCount={previousGrids.length}
          />
        {/if}

        <!-- Discrete New Game button for during gameplay -->
        {#if gameState === "playing"}
          <div class="bottom-actions">
            <button onclick={showNewGameConfirm} class="discrete-btn">
              ↻ New Game
            </button>
          </div>
        {/if}
      </section>
    {/if}
  </div>
</main>

{#if showConfirmNewGame}
  <ConfirmNewGame onConfirm={newGame} onCancel={hideNewGameConfirm} />
{/if}

<style>
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
  .current-grid,
  .final-grid {
    margin-bottom: 2rem;
    /* Prevent layout shifts during transitions */
    position: relative;
    width: 100%;
  }

  .grid-placeholder {
    background: #f0f0f0;
    border: 2px dashed #ccc;
    padding: 2rem;
    text-align: center;
    border-radius: 0.5rem;
    color: #888;
    margin-bottom: 1rem;
  }

  .check-btn {
    margin-top: 1rem;
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
  }

  .discrete-btn {
    background: transparent;
    color: #95a5a6;
    border: 1px solid #ddd;
    padding: 0.5rem 1rem;
    border-radius: 0.25rem;
    font-size: 0.85rem;
    font-weight: 400;
    cursor: pointer;
    transition: all 0.2s;
  }

  .discrete-btn:hover {
    background: #f8f9fa;
    color: #7f8c8d;
    border-color: #bbb;
  }

  /* Responsive design */
  @media (max-width: 480px) {
    .container {
      padding: 0.5rem;
    }

    h1 {
      font-size: 2rem;
    }
  }
</style>
