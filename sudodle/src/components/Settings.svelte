<script>
  import { _ } from "svelte-i18n";
  export let settings;
  export let onStartGame;
  export let onCancel;

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
          <div class="setting-row">
            <div class="radio-group">
              {#each [4, 5, 6, 7, 8, 9] as size}
                <label class="radio-item">
                  <input
                    type="radio"
                    bind:group={settings.gridSize}
                    value={size}
                    aria-label="Grid size {size}x{size}"
                  />
                  <span>{size}×{size}</span>
                </label>
              {/each}
            </div>
          </div>
          <div class="setting-row">
            <div class="switch-setting">
              <div class="switch-container">
                <label class="switch">
                  <input
                    type="checkbox"
                    bind:checked={settings.visualCues}
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
                    bind:checked={settings.strictMode}
                    aria-label="Strict mode toggle"
                  />
                  <span class="slider"></span>
                </label>
                <span class="switch-text">{$_("strictMode")}</span>
              </div>
            </div>
          </div>
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
  }

  .settings-card {
    background: transparent;
    padding: 0;
    border-radius: 0;
    box-shadow: none;
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
