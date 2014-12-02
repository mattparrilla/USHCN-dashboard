import os
import inspect

ABSOLUTE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(
    inspect.currentframe())))

from flask import Flask

app = Flask(__name__)
app.config.from_object('config')

from main import views
