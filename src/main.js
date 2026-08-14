(function () {
  "use strict";

  const tauri = window.__TAURI__;
  const statusEl = document.getElementById("status");
  const detailEl = document.getElementById("detail");
  const actionsEl = document.getElementById("actions");

  function setStatus(text) {
    statusEl.textContent = text;
  }

  function setDetail(text) {
    detailEl.textContent = text || "";
  }

  function showActions(visible) {
    actionsEl.hidden = !visible;
  }

  function navigate(url) {
    if (url) {
      window.location.replace(url);
    }
  }

  async function invoke(name, args) {
    if (tauri && tauri.core && typeof tauri.core.invoke === "function") {
      try {
        return await tauri.core.invoke(name, args);
      } catch (err) {
        return null;
      }
    }
    return null;
  }

  function handle(payload) {
    if (!payload) return;
    switch (payload.state) {
      case "ready":
        setStatus("Ready");
        setDetail("");
        showActions(false);
        navigate(payload.url);
        break;
      case "starting":
        setStatus("Starting DeepSeek Harness…");
        setDetail(payload.message || "Booting the local backend.");
        showActions(false);
        break;
      case "stopped":
        setStatus("Backend stopped");
        setDetail(payload.message || "Restarting…");
        showActions(false);
        break;
      case "error":
        setStatus("Could not start DeepSeek Harness");
        setDetail(payload.message || "Unknown error.");
        showActions(true);
        break;
      default:
        break;
    }
  }

  async function init() {
    document.getElementById("retry").addEventListener("click", function () {
      setStatus("Starting DeepSeek Harness…");
      setDetail("");
      showActions(false);
      invoke("restart_backend");
    });
    document.getElementById("quit").addEventListener("click", function () {
      invoke("quit_app");
    });

    if (tauri && tauri.event && typeof tauri.event.listen === "function") {
      try {
        await tauri.event.listen("backend-status", function (event) {
          handle(event.payload);
        });
      } catch (err) {
        // If the IPC bridge is unavailable (e.g. running in a plain browser),
        // fall back to the on-load URL check below.
      }
    }

    // Race guard: the backend may have become ready before the listener
    // attached (e.g. on a fast start or after a window reload).
    const url = await invoke("get_backend_url");
    if (url) {
      navigate(url);
    }
  }

  init();
})();
