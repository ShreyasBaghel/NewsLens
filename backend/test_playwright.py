import sys
import io

# Force utf-8 for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright
import time

def test_frontend():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch()
        page = browser.new_page()
        
        page.on("console", lambda msg: print(f"Browser console: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser error: {err}"))
        page.on("requestfailed", lambda req: print(f"Request failed: {req.url} {req.failure}"))
        
        print("Navigating to frontend...")
        page.goto("http://localhost:5173", timeout=60000)
        
        print("Waiting for network to be idle...")
        page.wait_for_load_state("networkidle")
        
        # Click the Administrator Profile if present
        try:
            print("Looking for login modal...")
            admin_btn = page.locator("text=Administrator Profile")
            if admin_btn.count() > 0:
                print("Clicking Administrator Profile...")
                admin_btn.first.click()
                time.sleep(2)
        except Exception as e:
            print(f"No login modal found: {e}")
            
        print("Waiting for articles to render...")
        time.sleep(5)
            
        print("Checking feed length text...")
        feed_text = page.locator("text=Showing").all_inner_texts()
        print(f"Feed length texts found: {feed_text}")
        
        error_el = page.locator(".error, .error-message, .error-banner")
        if error_el.count() > 0:
            print("ERROR FOUND ON PAGE:", error_el.first.inner_text())
        
        articles = page.locator(".article-card, article")
        count = articles.count()
        print(f"Total articles rendered on the frontend: {count}")
        
        page.screenshot(path="screenshot.png")
        print("Saved screenshot to screenshot.png")
        
        browser.close()

if __name__ == "__main__":
    test_frontend()
