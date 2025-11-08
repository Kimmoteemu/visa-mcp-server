# restart_bot.py
import subprocess
import sys
import time

BOT_SCRIPT = "bot.py"
PYTHON_EXECUTABLE = sys.executable

while True:
    try:
        process = subprocess.Popen([PYTHON_EXECUTABLE, BOT_SCRIPT])
        exit_code = process.wait()
        if exit_code == 0:
            print("bot.py exited normally. Restarting...")
        else:
            print(f"bot.py crashed with exit code {exit_code}. Restarting...")
        time.sleep(2)  # Optional: short delay before restart
    except KeyboardInterrupt:
        print("Received kill signal. Exiting.")
        break
    except Exception as e:
        print(f"Error running bot.py: {e}")
        time.sleep(2)
