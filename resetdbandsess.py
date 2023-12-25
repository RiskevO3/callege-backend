import backend.controller as c
from backend import app

with app.app_context():
    print(c.reset_all_configuration())