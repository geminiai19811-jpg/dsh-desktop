# DeepSeek Harness 桌面版

<p align="center">
  <a href="https://dsh.clawloop.app"><img src="https://img.shields.io/badge/%E5%AE%98%E7%BD%91-dsh.clawloop.app-4D6BFE?style=flat-square" alt="Official website" /></a>
  <a href="https://github.com/xingj404-lab/dsh-desktop/releases/latest"><img src="https://img.shields.io/github/v/release/xingj404-lab/dsh-desktop?label=%E6%9C%80%E6%96%B0%E7%89%88%E6%9C%AC&style=flat-square" alt="Latest release" /></a>
  <a href="https://github.com/xingj404-lab/dsh-desktop/actions/workflows/release.yml"><img src="https://img.shields.io/github/actions/workflow/status/xingj404-lab/dsh-desktop/release.yml?label=%E6%9E%84%E5%BB%BA%E7%8A%B6%E6%80%81&style=flat-square" alt="Build status" /></a>
  <a href="https://github.com/xingj404-lab/dsh-desktop/blob/main/README.md">English</a>
</p>

**dsh-desktop** 是 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（`dsh`）编程智能体的原生桌面应用。

它是一个基于 **Tauri v2** 的桌面外壳（shell），封装了现有的 `dsh web` 浏览器界面：

- 在本地启动 `dsh web` 后端（自动选择一个回环端口），
- 等后端就绪后，将其加载到原生窗口中，
- 增加原生菜单栏（编辑 / 视图 / 窗口）、系统托盘和窗口状态记忆，
- 在后台保活后端进程，崩溃后自动重启，
- 内置自带的 `node` 与 `dsh`，**最终用户无需安装任何环境**。

Harness 的界面本身没有改动 —— 本项目只提供原生外壳。

## ✨ 特性

- **开箱即用** —— 打包后的应用内置 Node.js 运行时和 `dsh` CLI，无需安装 Node、npm 或 CLI。
- **原生窗口** —— Dock 图标、菜单栏、缩放（⌘/Ctrl +/−、⌘/Ctrl 0）、刷新与开发者工具。
- **系统托盘** —— 关闭窗口会最小化到托盘而非退出，后端继续在后台运行。
- **窗口状态记忆** —— 记住窗口大小和位置。
- **后端自愈** —— 监视 `dsh web` 进程，崩溃后自动重启。
- **自动更新** —— 后台自动检测新版本，发现后左下角出现蓝色下载徽标，点击即可更新。
- **本地优先** —— 后端只绑定 `127.0.0.1`，不对外暴露端口。

## 📦 下载

请前往官网下载对应平台的最新版本：

👉 **[dsh.clawloop.app](https://dsh.clawloop.app)**

预编译安装包也同步发布在 [GitHub Releases](https://github.com/xingj404-lab/dsh-desktop/releases/latest)（macOS `.dmg` / `.app.zip`，Windows NSIS `.exe` / WiX `.msi`）。

### macOS 说明（Gatekeeper）

macOS 版本**未使用 Apple 开发者证书签名**，首次打开可能被 Gatekeeper 拦截。解决办法：

1. 右键点击应用 → **打开** → 在弹出的对话框中再次点击 **打开**；或
2. 在终端执行：`xattr -cr "/Applications/DeepSeek Harness.app"`

Linux 用户可从源码构建（见下文）。

## 🖥 桌面版与 Web 版的区别

`dsh web` 是 DeepSeek Harness 的浏览器界面，`dsh-desktop` 运行的是完全相同的界面，但打包成了桌面应用。

| | **Web 版**（`dsh web`） | **桌面版**（`dsh-desktop`） |
| --- | --- | --- |
| 启动方式 | 安装 Node + `npm i -g @deepseek-ai/dsh`，再在终端运行 `dsh web` | 下载安装包，双击打开 |
| 运行位置 | 浏览器标签页 | 原生独立窗口 |
| 需要安装 Node/dsh | ✅ 是 | ❌ 否（已内置） |
| 菜单栏 / Dock 图标 | ❌ | ✅ |
| 系统托盘与后台运行 | ❌ | ✅ |
| 窗口大小 / 位置记忆 | ❌ | ✅ |
| 后端自动重启 | ❌（进程结束即停止） | ✅ |
| 底层界面 | 完全一致 | 完全一致 |

想要双击即用的原生体验就选桌面版；更喜欢在自己的浏览器里运行、或在远程机器上使用，就用 `dsh web`。

## 🛠 从源码构建

### 环境要求

- **Rust**（工作区本地安装即可）：`./scripts/setup-rust.sh`，然后 `. ./scripts/env.sh`
- **Node.js 20+**（仅用于打包自包含后端；最终用户不需要）
- **npm**（用于安装 `@tauri-apps/cli` 构建工具）

平台额外依赖：

- **macOS**：Xcode 命令行工具（`xcode-select --install`）。
- **Windows**：Visual Studio Build Tools（C++ 工作负载）或 MSVC 工具链，以及 WebView2（Windows 10/11 通常已预装）。
- **Linux**：Tauri 系统依赖（`libwebkit2gtk-4.1`、`libgtk-3` 等）—— 见 [Tauri 前置条件](https://tauri.app/start/prerequisites/)。

### 1. 克隆并安装依赖

```sh
git clone git@github.com:xingj404-lab/dsh-desktop.git
cd dsh-desktop
npm install
```

### 2. 打包后端（自包含）

```sh
./scripts/bundle-backend.sh   # 复制 node，并 npm 安装 @deepseek-ai/dsh 到 resources/backend
```

`bundle-backend.sh` 若发现本机已有 `dsh` 安装会直接复用（无需联网），否则执行 `npm install @deepseek-ai/dsh`。在 Windows（Git Bash）下手动打包：

```sh
mkdir -p resources/backend
cp "$(node -e 'process.stdout.write(process.execPath)')" resources/backend/node.exe
cd resources/backend && npm init -y && npm install @deepseek-ai/dsh && cd ../..
```

### 3. 构建

```sh
. ./scripts/env.sh            # 仅 macOS / Linux
npm run build                 # `tauri build` → src-tauri/target/release/bundle/
```

产物：

- **macOS**：`DeepSeek Harness.app` + `DeepSeek Harness_*.dmg`
- **Windows**：`DeepSeek Harness_*_x64-setup.exe`（NSIS）+ `DeepSeek Harness_*_x64_en-US.msi`（WiX）
- **Linux**：`.deb`、`.rpm`、AppImage

> **提示**：`npm run build` 使用 `tauri.conf.json` 中的 `"all"` 打包目标。只想构建 macOS `.app` 并跳过 DMG，可执行 `npx tauri build --bundles app`。

### 开发模式（热更新）

```sh
npm install
. ./scripts/env.sh
npm run dev        # 以开发模式构建并启动应用
```

开发模式下后端从 `PATH` 中的 `dsh` 启动（或通过 `DSH_BIN=/path/to/dsh` 指定）。

## 🧩 后端启动流程

1. `backend.rs` 按以下优先级解析后端命令：`DSH_BIN`、内置的 `resources/backend`（`node` + `node_modules/@deepseek-ai/dsh`）、最后是 `PATH` 中的 `dsh`。
2. 绑定一个空闲回环端口，执行 `dsh web --host 127.0.0.1 --port <port>`。
3. 轮询端口直到服务可连接，然后发出 `backend-status { state: "ready", url }` 事件；启动页随之跳转到该 URL。
4. 崩溃时发出 `stopped` / `error` 并自动重启（硬错误如缺少后端时采用更长的退避间隔）。

关闭窗口会最小化到托盘；使用托盘菜单或 ⌘/Ctrl+Q 退出。

## 📁 项目结构

```
src/                  后端启动期间的启动页（纯静态，无打包器）
src-tauri/            Tauri v2 应用（Rust）
  src/main.rs         极简入口
  src/lib.rs          应用初始化：菜单、托盘、窗口事件、命令
  src/backend.rs      `dsh web` 子进程看门狗（启动 / 探测 / 重启 / 终止）
scripts/              辅助脚本（Rust 安装、环境加载、后端打包、图标生成）
assets/icon-source.png  源图标（由 scripts/gen-icon.py 生成）
.github/workflows/    构建 macOS + Windows 发布包并发布的 CI
```

## 🙏 致谢

- [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（`@deepseek-ai/dsh`）—— 底层的智能体与 Web 界面。
- [Tauri](https://tauri.app/) —— 本外壳所使用的跨平台应用框架。
