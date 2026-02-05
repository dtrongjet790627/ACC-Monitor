# -*- coding: utf-8 -*-
"""
ACC Monitor - API Blueprint
"""
from flask import Blueprint

api_bp = Blueprint('api', __name__)

from app.api import routes, websocket
