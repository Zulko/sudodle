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

  // State management
  let settings = {
    gridSize: 5,
    strictMode: false,
    visualCues: true,
  };

  let solutionGrid = [];
  let currentGrid = [];
  let previousGrids = [];
  let gameState = "playing"; // 'playing', 'won'
  let currentTurn = 1;
  let maxGuesses = 6;
  let seed = null;
  let showSettingsModal = false;
  let isTransitioning = false;
  let currentGridFeedback = null;

  // Reactive statement to check if check button should be disabled
  $: isCheckDisabled =
    isTransitioning ||
    (settings.strictMode && !checkLatinSquare(currentGrid)) ||
    maxGuesses - currentTurn <= 0;

  // Reactive statement to check if out of tries
  $: outOfTries = gameState === "playing" && maxGuesses - currentTurn <= 0;

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

    // Wait for i18n to be ready before starting the game
    const unsubscribe = isLoading.subscribe((loading) => {
      if (!loading) {
        startGame();
        unsubscribe();
      }
    });
  });

  // Grid generation functions
  function generateSolutionGrid() {
    if (!seed) {
      seed = Math.floor(Math.random() * 1000000);
    }
    solutionGrid = uniformRandomLatinSquare(settings.gridSize, seed);
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
    seed = null;
    previousGrids = [];
    currentTurn = 1;
    showSettingsModal = false;
    startGame();
  }

  function showNewGameModal() {
    showSettingsModal = true;
  }

  function hideSettingsModal() {
    showSettingsModal = false;
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
    let title = $_("shareTitle");
    if (gameState === "won") {
      title = $_("shareWinTitle", { values: { count: previousGrids.length } });
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
          {$_("rules")}
        </p>
      </div>

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
                ? $_("checking")
                : settings.strictMode && !checkLatinSquare(currentGrid)
                  ? $_("cannotCheck")
                  : maxGuesses - currentTurn <= 0
                    ? $_("outOfGuesses")
                    : $_("checkWithGuesses", {
                        values: { count: maxGuesses - currentTurn },
                      })}
            </button>
          </div>
        {/if}

        <!-- Victory Screen -->
        {#if gameState === "won"}
          <VictorySection
            onNewGame={showNewGameModal}
            onShareGame={shareGame}
            guessCount={previousGrids.length}
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
    <Settings {settings} onStartGame={newGame} onCancel={hideSettingsModal} />
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
    background: #f5f5f5;
    color: #777;
    border-color: #ddd;
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
