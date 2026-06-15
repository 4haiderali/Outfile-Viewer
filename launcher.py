import ctypes
import os
import socket
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

from PIL import Image
import pystray
from pystray import MenuItem as Item


APP_NAME = "OutfileViewer"
APP_TITLE = "Outfile Viewer"
PORT = 8600
MUTEX_NAME = "Global\\OutfileViewerSingleInstanceMutex"


TRAY_ICON = None


def already_running() -> bool:
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_error = kernel32.GetLastError()

    # ERROR_ALREADY_EXISTS = 183
    return last_error == 183


def get_log_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home()))
    log_dir = Path(local_app_data) / APP_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "OutfileViewer.log"


LOG_PATH = get_log_path()


def log(message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return str(Path(sys._MEIPASS) / relative_path)
    return str(Path(__file__).parent / relative_path)


def wait_for_server(port: int, timeout: int = 30) -> bool:
    start = time.time()

    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)

    return False


def open_browser() -> None:
    url = f"http://localhost:{PORT}"
    log(f"Opening browser: {url}")
    webbrowser.open(url)


def open_browser_when_ready() -> None:
    try:
        log("Browser thread started.")
        if wait_for_server(PORT):
            open_browser()
        else:
            log(f"Server did not become available on port {PORT} within timeout.")
    except Exception:
        log("Browser thread crashed:")
        log(traceback.format_exc())


def load_tray_icon_image() -> Image.Image:
    icon_path = Path(resource_path("out_viewer/Icon.ico"))

    if icon_path.exists():
        return Image.open(icon_path)

    return Image.new("RGB", (64, 64), "black")


def quit_app(icon=None, item=None) -> None:
    log("Quit requested from tray.")

    try:
        if icon is not None:
            icon.stop()
    except Exception:
        pass

    os._exit(0)


def start_tray_icon() -> None:
    global TRAY_ICON

    try:
        menu = pystray.Menu(
            Item("Open Outfile Viewer", lambda icon, item: open_browser()),
            Item("Quit Outfile Viewer", quit_app),
        )

        TRAY_ICON = pystray.Icon(
            APP_NAME,
            load_tray_icon_image(),
            APP_TITLE,
            menu,
        )

        log("Starting tray icon.")
        TRAY_ICON.run()

    except Exception:
        log("Tray icon crashed:")
        log(traceback.format_exc())


def start_streamlit_main_thread() -> None:
    app_path = resource_path("app.py")

    log(f"Resolved app.py path: {app_path}")
    log(f"app.py exists: {Path(app_path).exists()}")

    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.port",
        str(PORT),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
        "--global.developmentMode",
        "false",
    ]

    log(f"Streamlit argv: {sys.argv}")

    from streamlit.web.cli import main as streamlit_main

    log("Starting Streamlit in main thread.")
    streamlit_main()


def main() -> None:
    log("=" * 70)
    log("OutfileViewer launcher starting.")
    log(f"Executable: {sys.executable}")
    log(f"Frozen: {getattr(sys, 'frozen', False)}")
    log(f"_MEIPASS: {getattr(sys, '_MEIPASS', None)}")

    if already_running():
        log("Another instance is already running. Opening browser and exiting.")
        open_browser()
        return

    threading.Thread(target=start_tray_icon, daemon=True).start()
    threading.Thread(target=open_browser_when_ready, daemon=True).start()

    start_streamlit_main_thread()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log("Fatal launcher crash:")
        log(traceback.format_exc())
        raise