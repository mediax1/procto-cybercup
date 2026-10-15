import os
import subprocess
import sys

def test_app_imports_with_mongodb_configuration():
    env = os.environ.copy()
    env.update({"MONGODB_URI": "mongodb://localhost:27017/atelier_test", "MONGODB_DATABASE": "atelier_test"})
    result = subprocess.run([sys.executable, "-c", "from app.main import app; print(app.title)"], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "Atelier Commerce API"
