<script>
  export let settings;
  export let onStartGame;
</script>

<div class="settings">
  <div class="settings-card">
    <div class="setting-row">
      <label class="setting-label">Grid Size and options</label>
      <div class="radio-group">
        <label class="radio-item">
          <input type="radio" bind:group={settings.gridSize} value={5} />
          <span>5×5</span>
        </label>
        <label class="radio-item">
          <input type="radio" bind:group={settings.gridSize} value={6} />
          <span>6×6</span>
        </label>
        <label class="radio-item">
          <input type="radio" bind:group={settings.gridSize} value={7} />
          <span>7×7</span>
        </label>
        <label class="radio-item">
          <input type="radio" bind:group={settings.gridSize} value={8} />
          <span>8×8</span>
        </label>
        <label class="radio-item">
          <input type="radio" bind:group={settings.gridSize} value={9} />
          <span>9×9</span>
        </label>
      </div>
    </div>

    <div class="setting-row">
      <div class="switch-setting">
        <div class="switch-container">
          <label class="switch">
            <input type="checkbox" bind:checked={settings.strictMode} />
            <span class="slider"></span>
          </label>
          <span class="switch-text"
            >All guesses must be latin squares (harder!)</span
          >
        </div>
      </div>
    </div>

    <div class="setting-row">
      <div class="switch-setting">
        <div class="switch-container">
          <label class="switch">
            <input type="checkbox" bind:checked={settings.visualCues} />
            <span class="slider"></span>
          </label>
          <span class="switch-text">Highlight correct/incorrect positions</span>
        </div>
      </div>
    </div>
  </div>

  <button on:click={onStartGame} class="start-btn">
    <span>🎯</span>
    Start Game
  </button>
</div>

<style>
  .settings {
    margin-bottom: 2rem;
  }

  .settings-card {
    background: white;
    padding: 1.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }

  .setting-row {
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .setting-label {
    font-weight: 500;
    color: #555;
    min-width: 80px;
    flex-shrink: 0;
  }

  .radio-group {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .radio-item {
    display: flex;
    align-items: center;
    padding: 0.5rem 0.75rem;
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
  }

  .switch-container {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .switch-text {
    font-size: 0.9rem;
    color: #555;
    font-weight: 500;
  }

  .switch {
    position: relative;
    display: inline-block;
    width: 50px;
    height: 24px;
    flex-shrink: 0;
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

  .start-btn {
    background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
    color: white;
    border: none;
    padding: 0.875rem 1.5rem;
    border-radius: 0.5rem;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    width: 100%;
    margin-top: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .start-btn:hover {
    background: linear-gradient(135deg, #2980b9 0%, #1c6692 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
  }
</style>
