"""Capture high-resolution screenshots of Diagram Design Studio for documentation."""

import threading
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from diagram_design.studio.server import StudioServer, StudioRequestHandler

DOCS_SCREENSHOTS = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
DOCS_SCREENSHOTS.mkdir(parents=True, exist_ok=True)


def main():
    port = 8765
    server = StudioServer(("127.0.0.1", port), StudioRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Server started on http://127.0.0.1:{port}")

    time.sleep(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = context.new_page()

        # 1. Gallery View
        print("Capturing Gallery View...")
        page.goto(f"http://127.0.0.1:{port}/")
        page.wait_for_selector("#type-list", timeout=5000)
        time.sleep(1.5)  # wait for iframe diagram to load fonts and render
        gallery_png = DOCS_SCREENSHOTS / "studio-gallery.png"
        page.screenshot(path=str(gallery_png))
        print(f"Saved: {gallery_png}")

        # 2. Live Editor View
        print("Capturing Live Editor View...")
        page.click("button[data-view='studio']")
        time.sleep(1.5)
        editor_png = DOCS_SCREENSHOTS / "studio-editor.png"
        page.screenshot(path=str(editor_png))
        print(f"Saved: {editor_png}")

        # 3. Converter View
        print("Capturing Mermaid Converter View...")
        page.click("button[data-view='converter']")
        time.sleep(1)
        converter_png = DOCS_SCREENSHOTS / "studio-converter.png"
        page.screenshot(path=str(converter_png))
        print(f"Saved: {converter_png}")

        # 4. Doctor View
        print("Capturing Doctor View...")
        page.click("button[data-view='doctor']")
        time.sleep(1)
        doctor_png = DOCS_SCREENSHOTS / "studio-doctor.png"
        page.screenshot(path=str(doctor_png))
        print(f"Saved: {doctor_png}")

        browser.close()

    server.shutdown()
    server.server_close()
    print("Done capturing screenshots!")


if __name__ == "__main__":
    main()
