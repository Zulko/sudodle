<script>
  export let onConfirm;
  export let onCancel;

  function handleKeydown(event) {
    if (event.key === "Escape") {
      onCancel();
    }
  }

  function handleModalClick() {
    // Prevent modal from closing when clicking on the modal content
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
      <h3 id="modal-title">Start a New Game?</h3>
    </div>

    <div class="modal-content">
      <p>Your current progress will be lost.</p>
    </div>

    <div class="modal-actions">
      <button onclick={onCancel} onkeydown={onCancel} class="cancel-btn">
        Cancel
      </button>
      <button onclick={onConfirm} onkeydown={onConfirm} class="confirm-btn">
        Start New Game
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
    width: 90%;
    margin: 1rem;
  }

  .modal-header {
    padding: 1.5rem 1.5rem 0.5rem 1.5rem;
    border-bottom: 1px solid #eee;
  }

  .modal-header h3 {
    margin: 0;
    color: #2c3e50;
    font-size: 1.25rem;
    font-weight: 600;
  }

  .modal-content {
    padding: 1rem 1.5rem;
  }

  .modal-content p {
    margin: 0;
    color: #555;
    line-height: 1.5;
  }

  .modal-actions {
    padding: 1rem 1.5rem 1.5rem 1.5rem;
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
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
    background: #e74c3c;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.25rem;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .confirm-btn:hover {
    background: #c0392b;
  }
</style>
