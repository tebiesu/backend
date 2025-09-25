import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
routes = [r.path for r in app.routes]
print("All routes:", routes)
if "/auth/register" in routes:
    print("Register route registered")
else:
    print("Register route NOT registered - check imports in main.py")
