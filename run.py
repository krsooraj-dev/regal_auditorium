import os
import sys
import subprocess

def run_cmd(args):
    print(f"Executing: {' '.join(args)}")
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        sys.exit(1)

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)
    
    print("--- Regal Auditorium Digital Platform Bootstrapper ---")
    
    # 1. Install dependencies
    print("\n[Step 1/3] Installing dependencies...")
    run_cmd([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # 2. Run Database Seeding
    print("\n[Step 2/3] Checking and seeding database...")
    run_cmd([sys.executable, "-m", "backend.seed"])
    
    # 3. Start Uvicorn Server
    print("\n[Step 3/3] Launching FastAPI Web Server...")
    print("Open http://127.0.0.1:8000 in your browser to view the website.")
    print("Admin panel available at: http://127.0.0.1:8000/pages/admin.html")
    print("Press Ctrl+C to stop the server.\n")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "uvicorn", "backend.main:app", 
            "--host", "127.0.0.1", "--port", "8000", "--reload"
        ])
    except KeyboardInterrupt:
        print("\nWeb server stopped. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
