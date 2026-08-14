# DeepSeek Harness Desktop

<p align="center">
  <a href="https://github.com/xingj404-lab/dsh-desktop/releases/latest"><img src="https://img.shields.io/github/v/release/xingj404-lab/dsh-desktop?label=latest%20release&style=flat-square" alt="Latest release" /></a>
  <a href="https://github.com/xingj404-lab/dsh-desktop/actions/workflows/release.yml"><img src="https://img.shields.io/github/actions/workflow/status/xingj404-lab/dsh-desktop/release.yml?label=build&style=flat-square" alt="Build status" /></a>
  <a href="https://github.com/xingj404-lab/dsh-desktop/blob/main/README.zh-CN.md">中文</a>
</p>

**dsh-desktop** is the native desktop app for the [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (`dsh`) coding agent.

It is a **Tauri v2** shell around the existing `dsh web` browser surface:

- it starts the `dsh web` backend locally (on a loopback port it picks itself),
- waits until the backend is serving, then opens it in a native window,
- adds a native menu bar (Edit / View / Window), a system tray, and window-state memory,
- keeps the backend alive in the background and restarts it automatically on crash,
- bundles its own `node` + `dsh`, so **end users do not need to install anything**.

The harness UI itself is unchanged — this project only supplies the native shell.

## ✨ Features

- **Zero setup** — the packaged app carries its own Node.js runtime and `dsh` CLI; no Node, no npm, no CLI install required.
- **Native window** — dock icon, menu bar, zoom (⌘/Ctrl +/-, ⌘/Ctrl 0), reload, and devtools.
- **System tray** — closing the window hides the app to the tray instead of quitting; the backend keeps running in the background.
- **Window-state memory** — remembers window size and position across launches.
- **Self-healing backend** — the `dsh web` process is watched and restarted automatically if it crashes.
- **Local-first** — the backend binds to `127.0.0.1` only; nothing is exposed to the network.

## 📦 Download

Prebuilt installers are published on the [Releases](https://github.com/xingj404-lab/dsh-desktop/releases/latest) page.

| Platform | Asset | Notes |
| --- | --- | --- |
| **macOS** (Apple Silicon) | `DeepSeek.Harness_*_aarch64.dmg` | macOS 10.13+; unsigned build — see note below |
| **macOS** (Apple Silicon) | `DeepSeek.Harness_*_arm64.app.zip` | portable `.app` (unzip and drag to Applications) |
| **Windows** (x64) | `DeepSeek.Harness_*_x64-setup.exe` (NSIS) | Windows 10/11 x64 |
| **Windows** (x64) | `DeepSeek.Harness_*_x64_en-US.msi` (WiX) | Windows 10/11 x64 |

### macOS note (Gatekeeper)

The macOS build is **not signed with an Apple Developer certificate**, so Gatekeeper may block the first launch. To open it:

1. Right-click the app → **Open** → **Open** again in the dialog, or
2. In Terminal: `xattr -cr "/Applications/DeepSeek Harness.app"`

Linux users can build from source (see below).

## 🖥 Desktop vs. Web version

`dsh web` is the browser UI of the DeepSeek Harness. `dsh-desktop` runs exactly the same UI, but packaged as a desktop app.

| | **Web version** (`dsh web`) | **Desktop version** (`dsh-desktop`) |
| --- | --- | --- |
| How to start | Install Node + `npm i -g @deepseek-ai/dsh`, then run `dsh web` in a terminal | Download and double-click the installer |
| Where it runs | Any browser tab | A native, standalone window |
| Requires Node/dsh installed | ✅ yes | ❌ no (bundled) |
| Menu bar / dock icon | ❌ | ✅ |
| System tray & background running | ❌ | ✅ |
| Window size/position memory | ❌ | ✅ |
| Auto-restart of backend | ❌ (stops when terminal/process ends) | ✅ |
| Underlying UI | identical | identical |

Use the desktop version when you want a first-class, double-clickable app experience; use `dsh web` when you prefer running the harness in your own browser or on a remote machine.

## 🛠 Build from source

### Prerequisites

- **Rust** (a workspace-local install is enough): `./scripts/setup-rust.sh`, then `. ./scripts/env.sh`
- **Node.js 20+** (only needed to stage the self-contained backend; not required by end users)
- **npm** (to install the `@tauri-apps/cli` build tooling)

Platform extras:

- **macOS**: Xcode Command Line Tools (`xcode-select --install`).
- **Windows**: Visual Studio Build Tools (C++ workload) or the MSVC toolchain, and WebView2 (usually preinstalled on Windows 10/11).
- **Linux**: the Tauri system dependencies (`libwebkit2gtk-4.1`, `libgtk-3`, etc.) — see the [Tauri prerequisites](https://tauri.app/start/prerequisites/).

### 1. Clone and install dependencies

```sh
git clone git@github.com:xingj404-lab/dsh-desktop.git
cd dsh-desktop
npm install
```

### 2. Stage the backend (self-contained)

```sh
./scripts/bundle-backend.sh   # copies node + npm-installs @deepseek-ai/dsh into resources/backend
```

`bundle-backend.sh` reuses an existing local `dsh` install when it finds one (no network); otherwise it runs `npm install @deepseek-ai/dsh`. On Windows (Git Bash), stage it manually:

```sh
mkdir -p resources/backend
cp "$(node -e 'process.stdout.write(process.execPath)')" resources/backend/node.exe
cd resources/backend && npm init -y && npm install @deepseek-ai/dsh && cd ../..
```

### 3. Build

```sh
. ./scripts/env.sh            # macOS/Linux only
npm run build                 # `tauri build` → src-tauri/target/release/bundle/
```

Outputs:

- **macOS**: `DeepSeek Harness.app` + `DeepSeek Harness_*.dmg`
- **Windows**: `DeepSeek Harness_*_x64-setup.exe` (NSIS) + `DeepSeek Harness_*_x64_en-US.msi` (WiX)
- **Linux**: `.deb`, `.rpm`, AppImage

> **Tip**: `npm run build` uses the `"all"` bundle targets from `tauri.conf.json`. To build just the macOS `.app` and skip the DMG step, use `npx tauri build --bundles app`.

### Develop (hot reload)

```sh
npm install
. ./scripts/env.sh
npm run dev        # builds and launches the app in dev mode
```

In dev mode the backend is launched from `dsh` on `PATH` (or set `DSH_BIN=/path/to/dsh`).

## 🧩 How the backend is launched

1. `backend.rs` resolves the backend command from, in order: `DSH_BIN`, the bundled `resources/backend` (`node` + `node_modules/@deepseek-ai/dsh`), then `dsh` on `PATH`.
2. It binds a free loopback port and runs `dsh web --host 127.0.0.1 --port <port>`.
3. It probes the port until the server accepts connections, then emits the `backend-status { state: "ready", url }` event; the splash page navigates to that URL.
4. On crash it emits `stopped`/`error` and restarts automatically (with a longer backoff after hard errors such as a missing backend).

Closing the window hides the app to the tray; use the tray menu or ⌘/Ctrl+Q to quit.

## 📁 Project layout

```
src/                  the splash page shown while the backend boots (static, no bundler)
src-tauri/            the Tauri v2 app (Rust)
  src/main.rs         thin entry
  src/lib.rs          app setup: menu, tray, window events, commands
  src/backend.rs      `dsh web` child-process watchdog (spawn / probe / restart / kill)
scripts/              helpers (Rust install, env sourcing, backend staging, icon generation)
assets/icon-source.png  source icon (generated by scripts/gen-icon.py)
.github/workflows/    CI that builds macOS + Windows releases and publishes them
```

## 🙏 Acknowledgements

- [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (`@deepseek-ai/dsh`) — the underlying agent and web UI.
- [Tauri](https://tauri.app/) — the cross-platform app framework used for the shell.
