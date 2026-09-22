"""Uvicorn import target: ``uvicorn portal.server:app``."""

import os

from portal.app import create_app
from portal.config import config_from_environ

app = create_app(config_from_environ(os.environ))
