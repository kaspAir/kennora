"""Applikations-Factory fuer kennora.

Vorerst ein minimales, lauffaehiges Geruest: eine schlichte Startseite im
Marken-Look plus der Health-Endpoint, den Deploy und Watchdog abfragen. Die
eigentliche Domaene (sprachbasierte Wissens-Externalisierung: Aussagen,
Verbindungen, zwei Sichten) kommt schrittweise hinzu.
"""
from flask import (Flask, jsonify, redirect, render_template_string,
                   send_from_directory)

from .version import GIT_SHA, __version__

# Das Zeichen inline – so wirkt `currentColor` (Marke hell / Papier dunkel)
# und es entsteht kein zusaetzlicher Request.
_ZEICHEN = """<svg viewBox="0 0 120 120" fill="none" stroke="currentColor"
     stroke-width="4" stroke-linecap="round" role="img" aria-label="kennora">
  <circle cx="60" cy="60" r="46"/>
  <circle cx="60" cy="60" r="27"/>
  <circle cx="60" cy="60" r="11"/>
  <path d="M 71.12 25.76 A 36 36 0 0 1 93.83 47.69"/>
</svg>"""

_LANDING = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>kennora</title>
  <meta name="description" content="Wissen entsteht im Gespräch.">
  <meta name="theme-color" content="#4076B9">
  <link rel="icon" href="/static/brand/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="/static/brand/favicon-32.png" sizes="32x32" type="image/png">
  <link rel="icon" href="/static/brand/favicon-16.png" sizes="16x16" type="image/png">
  <link rel="apple-touch-icon" href="/static/brand/apple-touch-icon.png">
  <link rel="manifest" href="/static/brand/site.webmanifest">
  <link rel="stylesheet" href="/static/css/kennora.css">
</head>
<body>
  <main class="huelle">
    <div class="marke">
      <span class="marke__zeichen">{{ zeichen|safe }}</span>
      <h1 class="marke__wortmarke">kennora</h1>
      <p class="marke__claim">Wissen entsteht im Gespräch.</p>
      <p class="marke__fuss">v{{ version }}{% if sha %} <span class="warm">·</span> {{ sha }}{% endif %}</p>
    </div>
  </main>
</body>
</html>"""


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template_string(_LANDING, zeichen=_ZEICHEN,
                                      version=__version__, sha=GIT_SHA)

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok", version=__version__, sha=GIT_SHA)

    @app.get("/favicon.ico")
    def favicon():
        return send_from_directory(app.static_folder, "brand/favicon.ico")

    return app
