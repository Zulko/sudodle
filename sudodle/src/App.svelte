<script>
  import { onMount } from "svelte";
  import { cyclicLatinSquare } from "./lib/generateSquare.js";

  // State management
  let settings = {
    gridSize: 5,
    strictMode: false,
    visualCues: true,
  };

  let solutionGrid = [];
  let currentGrid = [];
  let previousGrids = [];
  let gameState = "rules"; // 'rules', 'settings', 'playing', 'won'
  let currentTurn = 1;
  let maxGuesses = 6;
  let seed = null;

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
      gameState = "won";
    } else if (currentTurn >= maxGuesses) {
      // Game over - could add this state later
      gameState = "won"; // For now, treat as won
    } else {
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
    }
  }

  function newGame() {
    gameState = "settings";
    seed = null;
    previousGrids = [];
    currentTurn = 1;
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

  function proceedFromRules() {
    gameState = "settings";
  }
</script>

<main>
  <div class="container">
    <h1>Sudodle</h1>

    {#if gameState === "rules"}
      <section class="rules">
        <h2>How to Play</h2>
        <p>
          In Sudodle, you must guess a grid of numbers where each number appears
          only once in each row and column (a Latin square). After each guess,
          you'll get feedback on which tiles are correct. Use this information
          to make your next guess!
        </p>
        <button on:click={proceedFromRules} class="primary-btn">
          Let's Play!
        </button>
      </section>
    {/if}

    {#if gameState === "settings"}
      <section class="settings">
        <h2>Game Settings</h2>

        <div class="setting-group">
          <label for="gridSize">Grid Size:</label>
          <select id="gridSize" bind:value={settings.gridSize}>
            <option value={5}>5x5</option>
            <option value={6}>6x6</option>
            <option value={7}>7x7</option>
            <option value={8}>8x8</option>
            <option value={9}>9x9 (Full Sudoku)</option>
          </select>
        </div>

        <div class="setting-group">
          <label>
            <input type="checkbox" bind:checked={settings.strictMode} />
            Strict Mode (all guesses must be valid Latin squares)
          </label>
        </div>

        <div class="setting-group">
          <label>
            <input type="checkbox" bind:checked={settings.visualCues} />
            Visual Cues (highlight correct/incorrect positions)
          </label>
        </div>

        <button on:click={startGame} class="primary-btn"> Start Game </button>
      </section>
    {/if}

    {#if gameState === "playing" || gameState === "won"}
      <section class="game">
        <div class="game-info">
          <p>Turn {currentTurn} of {maxGuesses}</p>
          <p>Grid Size: {settings.gridSize}x{settings.gridSize}</p>
        </div>

        <!-- Previous Grids -->
        {#each previousGrids as prevGrid (prevGrid.turn)}
          <div class="previous-grid">
            <h3>Turn {prevGrid.turn}</h3>
            <!-- TODO: Replace with PreviousGrid component -->
            <div class="grid-placeholder">
              Previous Grid Component (Turn {prevGrid.turn})
            </div>
          </div>
        {/each}

        <!-- Current Grid -->
        {#if gameState === "playing"}
          <div class="current-grid">
            <h3>Current Turn ({currentTurn})</h3>
            <!-- TODO: Replace with CurrentGrid component -->
            <div class="grid-placeholder">Current Grid Component</div>
            <button on:click={checkGrid} class="primary-btn check-btn">
              Check
            </button>
          </div>
        {/if}

        <!-- Victory Screen -->
        {#if gameState === "won"}
          <div class="victory">
            <h2>🎉 Congratulations!</h2>
            <p>
              You solved the puzzle in {previousGrids.length + 1} guess{previousGrids.length ===
              0
                ? ""
                : "es"}!
            </p>
            <div class="victory-actions">
              <button on:click={shareGame} class="primary-btn">
                Share Game
              </button>
              <button on:click={newGame} class="secondary-btn">
                New Game
              </button>
            </div>
          </div>
        {/if}
      </section>
    {/if}
  </div>
</main>

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

  h2 {
    color: #34495e;
    margin-bottom: 1rem;
  }

  h3 {
    color: #7f8c8d;
    margin: 1rem 0 0.5rem 0;
    font-size: 1rem;
  }

  .rules {
    text-align: center;
    margin-bottom: 2rem;
  }

  .rules p {
    line-height: 1.6;
    margin-bottom: 1.5rem;
    color: #555;
  }

  .settings {
    margin-bottom: 2rem;
  }

  .setting-group {
    margin-bottom: 1rem;
  }

  .setting-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #555;
  }

  select {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid #ddd;
    border-radius: 0.5rem;
    font-size: 1rem;
    background: white;
  }

  select:focus {
    outline: none;
    border-color: #3498db;
  }

  input[type="checkbox"] {
    margin-right: 0.5rem;
    transform: scale(1.2);
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

  .secondary-btn {
    background: #95a5a6;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
    width: 100%;
  }

  .secondary-btn:hover {
    background: #7f8c8d;
  }

  .game-info {
    text-align: center;
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 0.5rem;
  }

  .game-info p {
    margin: 0.25rem 0;
    color: #555;
  }

  .previous-grid,
  .current-grid {
    margin-bottom: 2rem;
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

  .victory {
    text-align: center;
    padding: 2rem 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 1rem;
    margin-top: 2rem;
  }

  .victory h2 {
    color: white;
    margin-bottom: 1rem;
  }

  .victory p {
    margin-bottom: 1.5rem;
    font-size: 1.1rem;
  }

  .victory-actions {
    display: flex;
    gap: 1rem;
    flex-direction: column;
  }

  .victory-actions button {
    background: rgba(255, 255, 255, 0.2);
    border: 2px solid rgba(255, 255, 255, 0.3);
    color: white;
  }

  .victory-actions button:hover {
    background: rgba(255, 255, 255, 0.3);
  }

  /* Responsive design */
  @media (max-width: 480px) {
    .container {
      padding: 0.5rem;
    }

    h1 {
      font-size: 2rem;
    }

    .victory-actions {
      flex-direction: column;
    }
  }
</style>
