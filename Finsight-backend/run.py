# run.py
from app import create_app
import os

env = os.getenv("FLASK_ENV", "dev")    # dev, test, prod 중 하나
app = create_app(config_name=env)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=(env=="dev"), use_reloader=True)
