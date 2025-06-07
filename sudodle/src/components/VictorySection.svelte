<script>
  export let onNewGame;
  export let onShareGame;
  export let guessCount;
</script>

<div class="victory">
  <h2>🎉 Congratulations!</h2>
  <p>
    You solved the puzzle in {guessCount} guess{guessCount === 1 ? "" : "es"}!
  </p>
  <div class="victory-actions">
    <button onclick={onShareGame} class="primary-btn">
      Share the link to this puzzle
    </button>
    <button onclick={onNewGame} class="secondary-btn"> New Game </button>
  </div>
</div>

<style>
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
</style>
