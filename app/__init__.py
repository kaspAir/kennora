"""Applikations-Factory fuer kennora.

Vorerst ein minimales, lauffaehiges Geruest: eine schlichte Startseite plus
der Health-Endpoint, den Deploy und Watchdog abfragen. Die eigentliche Domaene
(sprachbasierte Wissens-Externalisierung: Aussagen, Verbindungen, zwei Sichten)
kommt schrittweise hinzu.
"""
from flask import Flask, jsonify, render_template_string

from .version import GIT_SHA, __version__

_LANDING = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>kennora</title>
  <style>
    :root { color-scheme: light dark; }
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
           display: grid; place-items: center; min-height: 100vh; margin: 0; }
    main { text-align: center; padding: 2rem; }
    h1 { font-size: 2.5rem; margin: 0 0 .25rem; letter-spacing: .01em; }
    p { opacity: .7; margin: .25rem 0; }
    code { opacity: .5; font-size: .85rem; }
  </style>
</head>
<body>
  <main>
    <h1>kennora</h1>
    <p>Wissen entsteht im Gespräch.</p>
    <p><code>v{{ version }}{% if sha %} · {{ sha }}{% endif %}</code></p>
  </main>
</body>
</html>"""


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template_string(_LANDING, version=__version__, sha=GIT_SHA)

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok", version=__version__, sha=GIT_SHA)

    return app
