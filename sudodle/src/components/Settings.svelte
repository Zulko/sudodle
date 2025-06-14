<script>
  import { _ } from "svelte-i18n";

  let {
    mode = $bindable(),
    gridSize = $bindable(),
    strictMode = $bindable(),
    visualCues = $bindable(),
    difficulty = $bindable(),
    onStartGame,
    onCancel,
  } = $props();

  function handleKeydown(event) {
    if (event.key === "Escape") {
      onCancel();
    }
  }

  function handleModalClick(event) {
    // Prevent modal from closing when clicking on the modal content
    event.stopPropagation();
  }

  function handleStartGame() {
    onStartGame();
  }

  // Reset difficulty to normal if gridSize is 4 and current difficulty is not normal
  $effect(() => {
    if (gridSize === 4 && difficulty !== "normal") {
      difficulty = "normal";
    }
  });
</script>

<svelte:window onkeydown={handleKeydown} />

<div
  class="modal-overlay"
  onclick={onCancel}
  onkeydown={onCancel}
  role="dialog"
  aria-labelledby="modal-title"
  aria-modal="true"
  tabindex="0"
>
  <div
    class="modal"
    onclick={handleModalClick}
    onkeydown={handleModalClick}
    role="dialog"
    aria-labelledby="modal-title"
    aria-modal="true"
    tabindex="0"
  >
    <div class="modal-header">
      <h3 id="modal-title">{$_("startNewSudodle")}</h3>
    </div>

    <div class="modal-content">
      <div class="settings">
        <div class="settings-card">
          <div class="setting-row mode-selection">
            <div class="mode-buttons">
              <button
                class="mode-btn {mode === 'single-turn' ? 'active' : ''}"
                onclick={() => (mode = "single-turn")}
                type="button"
              >
                {$_("singleTurn")}
              </button>
              <button
                class="mode-btn {mode === 'guesses' ? 'active' : ''}"
                onclick={() => (mode = "guesses")}
                type="button"
              >
                {$_("multipleGuesses")}
              </button>
            </div>
          </div>
          <div class="setting-row">
            <div class="radio-group">
              {#each mode === "single-turn" ? [4, 5, 6, 7] : [4, 5, 6, 7, 8, 9] as size}
                <label class="radio-item">
                  <input
                    type="radio"
                    bind:group={gridSize}
                    value={size}
                    aria-label="Grid size {size}x{size}"
                  />
                  <span>{size}×{size}</span>
                </label>
              {/each}
            </div>
          </div>
          {#if mode === "single-turn"}
            <div class="setting-row">
              <div class="difficulty-group">
                {#each ["normal", "hard", "expert"] as difficultyLevel}
                  <label
                    class="difficulty-item {gridSize === 4 &&
                    difficultyLevel !== 'normal'
                      ? 'disabled'
                      : ''}"
                  >
                    <input
                      type="radio"
                      bind:group={difficulty}
                      value={difficultyLevel}
                      disabled={gridSize === 4 && difficultyLevel !== "normal"}
                      aria-label="Difficulty {difficultyLevel}"
                    />
                    <span
                      >{$_(
                        `difficulty${difficultyLevel.charAt(0).toUpperCase() + difficultyLevel.slice(1)}`
                      )}</span
                    >
                  </label>
                {/each}
              </div>
            </div>
          {/if}
          {#if mode !== "single-turn"}
            <div class="setting-row">
              <div class="switch-setting">
                <div class="switch-container">
                  <label class="switch">
                    <input
                      type="checkbox"
                      bind:checked={visualCues}
                      aria-label="Visual cues toggle"
                    />
                    <span class="slider"></span>
                  </label>
                  <span class="switch-text">{$_("visualCues")}</span>
                </div>
              </div>
            </div>
            <div class="setting-row">
              <div class="switch-setting">
                <div class="switch-container">
                  <label class="switch">
                    <input
                      type="checkbox"
                      bind:checked={strictMode}
                      aria-label="Strict mode toggle"
                    />
                    <span class="slider"></span>
                  </label>
                  <span class="switch-text">{$_("strictMode")}</span>
                </div>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>

    <div class="modal-actions">
      <button onclick={onCancel} class="cancel-btn"> {$_("cancel")} </button>
      <button onclick={handleStartGame} class="confirm-btn">
        <span>✨</span>
        {$_("newGame")}
      </button>
    </div>
  </div>
</div>

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal {
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    max-width: 400px;
    width: 95%;
    margin: 0.5rem;
    max-height: 90vh;
    overflow-y: auto;
  }

  .modal-header {
    padding: 1rem 1.5rem 0.5rem 1.5rem;
    border-bottom: 1px solid #eee;
  }

  .modal-header h3 {
    margin: 0;
    color: #2c3e50;
    font-size: 1.25rem;
    font-weight: 600;
  }

  .modal-content {
    padding: 1rem 0.7rem;
  }

  .modal-actions {
    padding: 1rem 1.5rem 1.5rem 1.5rem;
    display: flex;
    gap: 1rem;
    justify-content: center;
  }

  .cancel-btn {
    background: transparent;
    color: #95a5a6;
    border: 1px solid #ddd;
    padding: 0.75rem 1.5rem;
    border-radius: 0.25rem;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .cancel-btn:hover {
    background: #f8f9fa;
    color: #7f8c8d;
    border-color: #bbb;
  }

  .confirm-btn {
    background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.25rem;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .confirm-btn:hover {
    background: linear-gradient(135deg, #2980b9 0%, #1c6692 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
  }

  .settings {
    margin: 0;
    display: flex;
    justify-content: center;
    width: 100%;
  }

  .settings-card {
    background: transparent;
    padding: 0;
    border-radius: 0;
    box-shadow: none;
    width: 100%;
  }

  .setting-row {
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .setting-row:last-child {
    margin-bottom: 0;
  }

  .mode-selection {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #eee;
  }

  .mode-buttons {
    display: flex;
    gap: 0.75rem;
    width: 100%;
  }

  .mode-btn {
    flex: 1;
    background: #ffffff;
    border: 2px solid #e1e5e9;
    border-radius: 0.25rem;
    padding: 0.75rem 1rem;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.9rem;
    font-weight: 500;
    color: #2c3e50;
    text-align: center;
  }

  .mode-btn:hover {
    border-color: #3498db;
    background: #f8f9fa;
    color: #2980b9;
  }

  .mode-btn.active {
    border-color: #3498db;
    background: #3498db;
    color: #ffffff;
  }

  .radio-group {
    display: flex;
    gap: 0.3rem;
    flex-wrap: wrap;
  }

  .radio-item {
    display: flex;
    align-items: center;
    padding: 0.5rem 0.6rem;
    border: 2px solid #ddd;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.9rem;
    font-weight: 500;
    position: relative;
  }

  .radio-item:hover {
    border-color: #3498db;
    background: #f8f9fa;
  }

  .radio-item input[type="radio"] {
    position: absolute;
    opacity: 0;
    width: 100%;
    height: 100%;
    margin: 0;
    cursor: pointer;
  }

  .radio-item input[type="radio"]:checked + span {
    color: white;
  }

  .radio-item:has(input[type="radio"]:checked),
  .radio-item input[type="radio"]:checked + span {
    background: #3498db;
    border-color: #3498db;
    color: white;
  }

  .radio-item input[type="radio"]:checked {
    position: absolute;
    opacity: 0;
  }

  .radio-item span {
    pointer-events: none;
    z-index: 1;
  }

  .difficulty-group {
    display: flex;
    gap: 0.3rem;
    flex-wrap: wrap;
  }

  .difficulty-item {
    display: flex;
    align-items: center;
    padding: 0.5rem 0.6rem;
    border: 2px solid #ddd;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.9rem;
    font-weight: 500;
    position: relative;
  }

  .difficulty-item:hover {
    border-color: #3498db;
    background: #f8f9fa;
  }

  .difficulty-item input[type="radio"] {
    position: absolute;
    opacity: 0;
    width: 100%;
    height: 100%;
    margin: 0;
    cursor: pointer;
  }

  .difficulty-item input[type="radio"]:checked + span {
    color: white;
  }

  .difficulty-item:has(input[type="radio"]:checked),
  .difficulty-item input[type="radio"]:checked + span {
    background: #3498db;
    border-color: #3498db;
    color: white;
  }

  .difficulty-item input[type="radio"]:checked {
    position: absolute;
    opacity: 0;
  }

  .difficulty-item span {
    pointer-events: none;
    z-index: 1;
  }

  .difficulty-item.disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .difficulty-item.disabled:hover {
    border-color: #ddd;
    background: transparent;
  }

  .switch-setting {
    width: 100%;
    display: flex;
    justify-content: center;
  }

  .switch-container {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    justify-content: flex-start;
  }

  .switch-text {
    font-size: 0.9rem;
    color: #555;
    font-weight: 500;
    flex: 1;
  }

  .switch {
    position: relative;
    display: inline-block;
    width: 50px;
    height: 24px;
    flex-shrink: 0;
    order: -1;
  }

  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: 0.3s;
    border-radius: 24px;
  }

  .slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: 0.3s;
    border-radius: 50%;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .switch input:checked + .slider {
    background-color: #3498db;
  }

  .switch input:checked + .slider:before {
    transform: translateX(26px);
  }

  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .modal-overlay {
      background: rgba(0, 0, 0, 0.7);
    }

    .modal {
      background: #1e1e1e;
      color: #ffffff;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
    }

    .modal-header {
      border-bottom: 1px solid #444;
    }

    .modal-header h3 {
      color: #ffffff;
    }

    .mode-selection {
      border-bottom: 1px solid #444;
    }

    .mode-btn {
      background: #2a2a2a;
      border: 2px solid #555;
      color: #ffffff;
    }

    .mode-btn:hover {
      border-color: #3498db;
      background: #333;
      color: #64b5f6;
    }

    .mode-btn.active {
      border-color: #3498db;
      background: #3498db;
      color: #ffffff;
    }

    .cancel-btn {
      background: transparent;
      color: #aaa;
      border: 1px solid #555;
    }

    .cancel-btn:hover {
      background: #2a2a2a;
      color: #ccc;
      border-color: #777;
    }

    .radio-item {
      border: 2px solid #555;
      background: #2a2a2a;
      color: #ffffff;
    }

    .radio-item:hover {
      border-color: #3498db;
      background: #333;
    }

    .difficulty-item {
      border: 2px solid #555;
      background: #2a2a2a;
      color: #ffffff;
    }

    .difficulty-item:hover {
      border-color: #3498db;
      background: #333;
    }

    .difficulty-item.disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .difficulty-item.disabled:hover {
      border-color: #555;
      background: #2a2a2a;
    }

    .switch-text {
      color: #ccc;
    }

    .slider {
      background-color: #555;
    }

    .slider:before {
      background-color: #fff;
    }
  }
</style>
