import subprocess
import time

def run_full_test():
    print("Starting backend...")
    backend_proc = subprocess.Popen(
        [".venv\\Scripts\\python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd="d:\\News_Dashboard\\backend",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    print("Starting frontend...")
    frontend_proc = subprocess.Popen(
        ["npm.cmd", "run", "dev", "--", "--port", "5173"],
        cwd="d:\\News_Dashboard\\frontend",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    print("Waiting 20 seconds for servers to start and vite to compile...")
    time.sleep(20)
    
    print("Running playwright test...")
    try:
        result = subprocess.run(
            [".venv\\Scripts\\python", "test_playwright.py"],
            cwd="d:\\News_Dashboard\\backend",
            capture_output=True,
            text=True
        )
        print("--- Playwright Output ---")
        print(result.stdout)
        if result.stderr:
            print("ERRORS:")
            print(result.stderr)
    finally:
        print("Cleaning up processes...")
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=5)
        except:
            backend_proc.kill()
        try:
            frontend_proc.wait(timeout=5)
        except:
            frontend_proc.kill()

if __name__ == "__main__":
    run_full_test()
