<script lang="ts">
  import { _, locale } from "svelte-i18n";

  // PWA installation logic
  let deferredPrompt = $state(null);
  let showInstallButton = $state(false);
  let isIOS = $state(false);
  let isInStandaloneMode = $state(false);

  $effect(() => {
    // Check if running in standalone mode (already installed)
    isInStandaloneMode =
      window.matchMedia("(display-mode: standalone)").matches ||
      (window.navigator as any).standalone === true;

    // Check if iOS
    isIOS =
      /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as any).MSStream;

    // Show install button if not in standalone mode and either:
    // - We have a deferred prompt (Android/Chrome)
    // - We're on iOS (manual installation)
    showInstallButton = !isInStandaloneMode && (deferredPrompt || isIOS);

    // Listen for the beforeinstallprompt event
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      deferredPrompt = e;
      showInstallButton = !isInStandaloneMode;
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener(
        "beforeinstallprompt",
        handleBeforeInstallPrompt
      );
    };
  });

  const handleInstallApp = async () => {
    if (isIOS) {
      // Show iOS installation instructions
      alert(
        $locale === "fr"
          ? "Pour installer Sudodle sur iOS :\n1. Appuyez sur l'icône de partage en bas\n2. Sélectionnez 'Sur l'écran d'accueil'\n3. Appuyez sur 'Ajouter'"
          : "To install Sudodle on iOS:\n1. Tap the share icon at the bottom\n2. Select 'Add to Home Screen'\n3. Tap 'Add'"
      );
    } else if (deferredPrompt) {
      // Show the install prompt
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;

      if (outcome === "accepted") {
        showInstallButton = false;
      }

      deferredPrompt = null;
    }
  };
</script>

{#if showInstallButton}
  <p class="install-app-link">
    <a onclick={handleInstallApp} class="install-app-btn">
      {$_("installApp") || "Install Sudodle as an app"}
      <span class="install-icon">📱</span>
    </a>
  </p>
{/if}

<style>
  .install-app-link {
    margin-top: 0.75rem;
    margin-bottom: 0;
    opacity: 0.7;
    font-size: 1rem;
  }

  .install-app-btn {
    color: #64748b;
    text-decoration: underline;
    text-decoration-color: rgba(100, 116, 139, 0.4);
    transition: all 0.2s ease;
    font-weight: 400;
  }

  .install-app-btn:hover {
    color: #3498db;
    text-decoration-color: #3498db;
  }

  .install-icon {
    margin-left: 0.5rem;
  }

  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .install-app-btn {
      color: #a0aec0;
      text-decoration-color: rgba(160, 174, 192, 0.4);
    }

    .install-app-btn:hover {
      color: #3498db;
      text-decoration-color: #3498db;
    }
  }
</style>
