import sys
import os

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now import the app
from dashboard.app import app

if __name__ == "__main__":
    print("Starte Trading Dashboard auf http://localhost:8050")
    app.run(debug=True, host="0.0.0.0", port=8050)
