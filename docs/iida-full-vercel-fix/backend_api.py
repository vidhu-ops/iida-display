"""Vercel FastAPI entrypoint.

Vercel auto-detects ``app.py`` first; this module is the explicit production API
when ``[tool.vercel] entrypoint`` is set to ``backend_api:app``.
"""
from backend.main import app

__all__ = ["app"]
