use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;

use tauri::{
    menu::{MenuBuilder, MenuItem, PredefinedMenuItem, SubmenuBuilder},
    tray::TrayIconBuilder,
    AppHandle, Manager, RunEvent, WindowEvent,
};
use tauri_plugin_dialog::DialogExt;
use tauri_plugin_updater::UpdaterExt;

mod backend;

/// Shared state between the backend watchdog thread and the UI commands.
pub struct AppState {
    /// PID of the running `dsh web` child, if any.
    pub pid: Mutex<Option<u32>>,
    /// Canonical loopback URL of the running backend, if ready.
    pub url: Mutex<Option<String>>,
    /// Current webview zoom scale.
    pub zoom: Mutex<f64>,
    /// Set once the app is exiting; stops the watchdog restart loop.
    pub shutting_down: AtomicBool,
    /// Keeps the tray icon alive for the process lifetime.
    pub tray: Mutex<Option<tauri::tray::TrayIcon>>,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            pid: Mutex::new(None),
            url: Mutex::new(None),
            zoom: Mutex::new(1.0),
            shutting_down: AtomicBool::new(false),
            tray: Mutex::new(None),
        }
    }
}

#[tauri::command]
fn get_backend_url(state: tauri::State<'_, AppState>) -> Option<String> {
    state.url.lock().unwrap().clone()
}

#[tauri::command]
fn restart_backend(state: tauri::State<'_, AppState>) -> Result<(), String> {
    // The watchdog loop always respawns; killing the current child (if any)
    // short-circuits the wait and triggers an immediate restart.
    if let Some(pid) = state.pid.lock().unwrap().as_ref().copied() {
        backend::graceful_kill(pid);
    }
    Ok(())
}

#[tauri::command]
fn quit_app(app: AppHandle) {
    app.exit(0);
}

fn build_menu(app: &tauri::App) -> tauri::Result<()> {
    let h = app.handle();

    let app_menu = SubmenuBuilder::new(h, "DeepSeek Harness")
        .item(&PredefinedMenuItem::about(h, None, None)?)
        .separator()
        .item(&MenuItem::with_id(h, "check-updates", "Check for Updates…", true, None::<&str>)?)
        .separator()
        .item(&PredefinedMenuItem::quit(h, Some("Quit DeepSeek Harness"))?)
        .build()?;

    let edit_menu = SubmenuBuilder::new(h, "Edit")
        .item(&PredefinedMenuItem::undo(h, None)?)
        .item(&PredefinedMenuItem::redo(h, None)?)
        .separator()
        .item(&PredefinedMenuItem::cut(h, None)?)
        .item(&PredefinedMenuItem::copy(h, None)?)
        .item(&PredefinedMenuItem::paste(h, None)?)
        .item(&PredefinedMenuItem::select_all(h, None)?)
        .build()?;

    let view_menu = SubmenuBuilder::new(h, "View")
        .item(&PredefinedMenuItem::fullscreen(h, None)?)
        .separator()
        .item(&MenuItem::with_id(h, "zoom-in", "Zoom In", true, Some("CmdOrCtrl+Plus"))?)
        .item(&MenuItem::with_id(h, "zoom-out", "Zoom Out", true, Some("CmdOrCtrl+-"))?)
        .item(&MenuItem::with_id(h, "zoom-reset", "Actual Size", true, Some("CmdOrCtrl+0"))?)
        .separator()
        .item(&MenuItem::with_id(h, "reload", "Reload", true, Some("CmdOrCtrl+R"))?)
        .item(&MenuItem::with_id(h, "toggle-devtools", "Toggle Developer Tools", true, Some("CmdOrCtrl+Shift+I"))?)
        .build()?;

    let window_menu = SubmenuBuilder::new(h, "Window")
        .item(&PredefinedMenuItem::minimize(h, None)?)
        .item(&PredefinedMenuItem::maximize(h, None)?)
        .separator()
        .item(&PredefinedMenuItem::close_window(h, None)?)
        .build()?;

    let menu = MenuBuilder::new(h)
        .items(&[&app_menu, &edit_menu, &view_menu, &window_menu])
        .build()?;

    app.set_menu(menu)?;
    Ok(())
}

fn build_tray(app: &tauri::App) -> tauri::Result<tauri::tray::TrayIcon> {
    let h = app.handle();

    let show = MenuItem::with_id(h, "tray-show", "Show DeepSeek Harness", true, None::<&str>)?;
    let quit = MenuItem::with_id(h, "tray-quit", "Quit", true, None::<&str>)?;
    let menu = MenuBuilder::new(h).items(&[&show, &quit]).build()?;

    TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .tooltip("DeepSeek Harness")
        .menu(&menu)
        .on_menu_event(|app, event| match event.id().as_ref() {
            "tray-show" => show_main_window(app),
            "tray-quit" => app.exit(0),
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let tauri::tray::TrayIconEvent::Click { .. } = event {
                show_main_window(tray.app_handle());
            }
        })
        .build(app)
}

fn show_main_window(app: &AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.unminimize();
        let _ = w.set_focus();
    }
}

fn zoom(app: &AppHandle, factor: f64) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };
    let state = app.state::<AppState>();
    let mut current = state.zoom.lock().unwrap();
    let next = if factor == 0.0 {
        1.0
    } else {
        (*current * factor).clamp(0.5, 2.0)
    };
    *current = next;
    let _ = window.set_zoom(next);
}

fn reload(app: &AppHandle) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };
    let target = app
        .state::<AppState>()
        .url
        .lock()
        .unwrap()
        .clone()
        .unwrap_or_else(|| "index.html".to_string());
    if let Ok(url) = tauri::Url::parse(&target) {
        let _ = window.navigate(url);
    }
}

fn toggle_devtools(app: &AppHandle) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };
    if window.is_devtools_open() {
        let _ = window.close_devtools();
    } else {
        let _ = window.open_devtools();
    }
}

/// Menu entry: check for updates, ask, download, install, and restart.
fn check_for_updates(app: AppHandle) {
    std::thread::spawn(move || {
        // 1. Check for an update (async).
        let checked: Result<Option<tauri_plugin_updater::Update>, String> =
            tauri::async_runtime::block_on(async {
                let updater = app.updater().map_err(|e| e.to_string())?;
                updater.check().await.map_err(|e| e.to_string())
            });

        let update = match checked {
            Ok(Some(update)) => update,
            Ok(None) => {
                let _ = app
                    .dialog()
                    .message("You are running the latest version.")
                    .title("DeepSeek Harness")
                    .blocking_show();
                return;
            }
            Err(e) => {
                let _ = app
                    .dialog()
                    .message(format!("Update check failed: {e}"))
                    .title("DeepSeek Harness")
                    .blocking_show();
                return;
            }
        };

        // 2. Confirm before downloading.
        let yes = app
            .dialog()
            .message(format!(
                "DeepSeek Harness {} is available.\n\nDownload and install now?",
                update.version
            ))
            .title("Update Available")
            .buttons(tauri_plugin_dialog::MessageDialogButtons::OkCancelCustom(
                "Update".into(),
                "Later".into(),
            ))
            .blocking_show();

        if !yes {
            return;
        }

        // 3. Download + install (async), then restart.
        let downloaded = tauri::async_runtime::block_on(async {
            update
                .download_and_install(|_chunk_length, _content_length| {}, || {})
                .await
        });

        match downloaded {
            Ok(()) => app.restart(),
            Err(e) => {
                let _ = app
                    .dialog()
                    .message(format!("Update failed: {e}"))
                    .title("DeepSeek Harness")
                    .blocking_show();
            }
        }
    });
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_window_state::Builder::default().build())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![
            get_backend_url,
            restart_backend,
            quit_app
        ])
        .setup(|app| {
            build_menu(app)?;
            let tray = build_tray(app)?;
            *app.state::<AppState>().tray.lock().unwrap() = Some(tray);

            let handle = app.handle().clone();
            std::thread::spawn(move || {
                backend::start_watchdog(&handle);
            });
            Ok(())
        })
        .on_menu_event(|app, event| match event.id().as_ref() {
            "zoom-in" => zoom(app, 1.1),
            "zoom-out" => zoom(app, 0.9),
            "zoom-reset" => zoom(app, 0.0),
            "reload" => reload(app),
            "toggle-devtools" => toggle_devtools(app),
            "check-updates" => check_for_updates(app.clone()),
            _ => {}
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                // Close button hides to tray; the app keeps running (and keeps
                // the backend alive). Quit is via the tray menu or Cmd+Q.
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building dsh-desktop")
        .run(|app, event| {
            if let RunEvent::Exit = event {
                let state = app.state::<AppState>();
                state.shutting_down.store(true, Ordering::SeqCst);
                let pid = state.pid.lock().unwrap().as_ref().copied();
                if let Some(pid) = pid {
                    backend::graceful_kill(pid);
                }
            }
        });
}
