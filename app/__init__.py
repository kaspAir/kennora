"""Applikations-Factory fuer kennora.

Startseite im Marken-Look, Health-Endpoint, und die erste vertikale Scheibe des
Sitzungs-Loops: sprechen/tippen (in beliebiger Sprache) -> Aussagen, Grundsatz
und Kantenvorschläge -> Graph -> Baum-Sicht.
"""
import os

import base64

from flask import (Flask, abort, jsonify, redirect, render_template_string,
                   request, send_from_directory)

from .version import GIT_SHA, __version__

# Das Zeichen inline – so wirkt `currentColor` (Marke hell / Papier dunkel).
_ZEICHEN = """<svg viewBox="0 0 120 120" fill="none" stroke="currentColor"
     stroke-width="4" stroke-linecap="round" role="img" aria-label="kennora">
  <circle cx="60" cy="60" r="46"/>
  <circle cx="60" cy="60" r="27"/>
  <circle cx="60" cy="60" r="11"/>
  <path d="M 71.12 25.76 A 36 36 0 0 1 93.83 47.69"/>
</svg>"""

_KOPF = """  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#4076B9">
  <link rel="icon" href="/static/brand/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="/static/brand/favicon-32.png" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="/static/brand/apple-touch-icon.png">
  <link rel="manifest" href="/static/brand/site.webmanifest">
  <link rel="stylesheet" href="/static/css/kennora.css">"""

_LANDING = """<!doctype html><html lang="de"><head>
  <title>kennora</title>
  <meta name="description" content="Wissen entsteht im Gespräch.">
""" + _KOPF + """
</head><body>
  <main class="huelle">
    <div class="marke">
      <span class="marke__zeichen">{{ zeichen|safe }}</span>
      <h1 class="marke__wortmarke">kennora</h1>
      <p class="marke__claim">Wissen entsteht im Gespräch.</p>
      <p style="margin-top:1.4rem"><a class="btn btn--primary" href="/sitzung">Sprechen</a></p>
      <p class="marke__fuss">v{{ version }}{% if sha %} <span class="warm">·</span> {{ sha }}{% endif %}</p>
    </div>
  </main>
</body></html>"""

_SITZUNG = """<!doctype html><html lang="de"><head>
  <title>kennora — sprechen</title>
""" + _KOPF + """
  <style>
    .seite { max-width: 760px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }
    .kopf { display:flex; align-items:center; gap:.6rem; margin-bottom:1.5rem; }
    .kopf .z { width:34px; height:34px; color:var(--marke); }
    .kopf h1 { font-family:var(--font-display); font-weight:500; font-size:1.7rem; margin:0; }
    textarea { width:100%; min-height:120px; font:inherit; padding:.8rem;
      border:1px solid rgba(128,128,128,.35); border-radius:var(--radius);
      background:transparent; color:var(--text); resize:vertical; }
    button { font:inherit; font-weight:600; color:#fff; background:var(--marke);
      border:none; border-radius:var(--radius); padding:.6rem 1.3rem; margin-top:.7rem;
      cursor:pointer; }
    .rueck { background:rgba(199,154,110,.14); border-left:3px solid var(--warm);
      padding:.8rem 1rem; border-radius:8px; margin:1.3rem 0; }
    .frage { font-style:italic; color:var(--text-leise); margin-top:.4rem; }
    .leise { color:var(--text-leise); font-size:.9rem; }
    h2 { font-family:var(--font-display); font-weight:500; margin:2rem 0 .5rem; }
    ul.baum { list-style:none; padding-left:1.1rem; border-left:1px solid rgba(128,128,128,.25); }
    ul.baum li { margin:.3rem 0; }
    .grundsatz { color:var(--warm); font-size:.85rem; }
    .netz li { margin:.35rem 0; }
    .typ { font-size:.75rem; letter-spacing:.05em; text-transform:uppercase;
      color:var(--marke); }
    .werkzeuge { display:flex; align-items:center; gap:.55rem; flex-wrap:wrap; margin:.2rem 0 .6rem; }
    .mic { background:transparent; color:var(--marke); border:1px solid var(--marke);
      margin-top:0; padding:.45rem 1rem; }
    .mic.rec { background:var(--marke); color:#fff; }
    select#mic-select { font:inherit; padding:.42rem; border-radius:8px;
      border:1px solid rgba(128,128,128,.35); background:transparent; color:var(--text); }
    .voice-status { color:var(--text-leise); font-size:.85rem; }
    .reset { margin-top:2.5rem; }
    .reset button { background:transparent; color:#b23b3b; border:1px solid #b23b3b;
      font-weight:600; border-radius:var(--radius); padding:.5rem 1.1rem; cursor:pointer; }
    ul.baum li.knoten { position:relative; }
    .reife { font-size:.8rem; margin-right:.15rem; }
    .reife.best { color:var(--marke); }
    .reife.bearb { color:var(--warm); }
    li.reife-roh > .ktext { opacity:.72; }
    .aktionen { opacity:.5; margin-left:.45rem; white-space:nowrap; transition:opacity .12s; }
    li.knoten:hover > .aktionen { opacity:1; }
    .aktionen form { display:inline; }
    .mini { display:inline-block; border:none; background:transparent; cursor:pointer;
      font-size:.9rem; line-height:1; padding:.1rem .28rem; color:var(--text-leise);
      text-decoration:none; border-radius:5px; }
    .mini:hover { color:var(--marke); background:color-mix(in oklab, var(--marke) 10%, transparent); }
    /* Bearbeiten-Seite */
    .bearb-form label { display:block; margin:1rem 0 .3rem; font-weight:600; }
    .bearb-form input { width:100%; font:inherit; padding:.6rem;
      border:1px solid rgba(128,128,128,.35); border-radius:var(--radius);
      background:transparent; color:var(--text); }
    .bearb-form .knoepfe { display:flex; gap:.6rem; align-items:center; margin-top:1.2rem; }
  </style>
</head><body>
  <div class="seite">
    <div class="kopf"><span class="z">{{ zeichen|safe }}</span>
      <h1>Erzähl mir, woran du gerade arbeitest.</h1></div>
    <p class="leise">Sprich oder schreib frei – in jeder Sprache. kennora ordnet im Hintergrund.</p>

    <form method="post" action="/sitzung">
      {% if stt_verfuegbar %}
      <div class="werkzeuge">
        <button type="button" class="mic" id="diktat-btn"
                data-endpoint="/diktat" data-stt="1">🎤 Sprechen</button>
        <select id="mic-select" style="display:none"></select>
        <span class="voice-status" id="voice-status"></span>
      </div>
      {% endif %}
      <textarea name="text" id="answer-text" placeholder="…" autofocus></textarea><br>
      <button type="submit">Ablegen</button>
    </form>

    {% if not verfuegbar or not stt_verfuegbar %}
      <p class="rueck">
        {% if not verfuegbar %}⚠️ Noch kein Modell konfiguriert
        (<code>ANTHROPIC_API_KEY</code> oder <code>KENNORA_LLM_BASE_URL</code>) –
        ohne das kann kennora das Gesagte nicht strukturieren, der Graph bleibt leer.{% endif %}
        {% if not stt_verfuegbar %}{% if not verfuegbar %}<br><br>{% endif %}🎤 Diktat ist
        noch nicht konfiguriert (<code>STT_API_KEY</code>) – bis dahin bitte tippen.{% endif %}
      </p>
    {% endif %}
    {% if fehler %}<p class="rueck">Es ist etwas schiefgelaufen: {{ fehler }}</p>{% endif %}
    {% if rueckgabe %}
      <div class="rueck">{{ rueckgabe }}
        {% if zwischenfrage %}<div class="frage">{{ zwischenfrage }}</div>{% endif %}
      </div>
    {% endif %}

    <h2>Dein Wissen — als Baum</h2>
    {% if baum_html %}{{ baum_html|safe }}{% else %}<p class="leise">Noch nichts abgelegt.</p>{% endif %}

    {% if netz %}
      <h2>Verbindungen — im Netz</h2>
      <ul class="netz">
      {% for k in netz %}
        <li><span class="typ">{{ k.typ }}</span> — {{ k.von_text }} ↔ {{ k.nach_text }}
          {% if k.begruendung %}<span class="leise">({{ k.begruendung }})</span>{% endif %}</li>
      {% endfor %}
      </ul>
    {% endif %}

    {% if dev %}
      <form class="reset" method="post" action="/reset"
            onsubmit="return confirm('Alle Testdaten dieser Sitzung wirklich löschen?');">
        <button type="submit">🗑 Testdaten zurücksetzen — nur dev</button>
      </form>
    {% endif %}

    <p style="margin-top:2.5rem"><a class="btn btn--ghost" href="/">&larr; kennora</a></p>
  </div>
  <script src="/static/js/diktat.js"></script>
</body></html>"""

_BEARBEITEN = """<!doctype html><html lang="de"><head>
  <title>kennora — überarbeiten</title>
""" + _KOPF + """
  <style>
    .seite { max-width:640px; margin:0 auto; padding:2rem 1.25rem 4rem; }
    .kopf { display:flex; align-items:center; gap:.6rem; margin-bottom:.6rem; }
    .kopf .z { width:32px; height:32px; color:var(--marke); }
    .kopf h1 { font-family:var(--font-display); font-weight:500; font-size:1.5rem; margin:0; }
    textarea { width:100%; min-height:110px; font:inherit; padding:.7rem;
      border:1px solid rgba(128,128,128,.35); border-radius:var(--radius);
      background:transparent; color:var(--text); resize:vertical; }
    label { display:block; margin:1.1rem 0 .3rem; font-weight:600; }
    input { width:100%; font:inherit; padding:.6rem;
      border:1px solid rgba(128,128,128,.35); border-radius:var(--radius);
      background:transparent; color:var(--text); }
    .leise { color:var(--text-leise); font-size:.9rem; }
    .original { color:var(--text-leise); font-size:.9rem; margin-top:.8rem; font-style:italic; }
    .knoepfe { display:flex; gap:.6rem; align-items:center; margin-top:1.3rem; }
    .knoepfe button { font:inherit; font-weight:600; color:#fff; background:var(--marke);
      border:none; border-radius:var(--radius); padding:.6rem 1.4rem; cursor:pointer; }
  </style>
</head><body>
  <div class="seite">
    <div class="kopf"><span class="z">{{ zeichen|safe }}</span><h1>Aussage überarbeiten</h1></div>
    <p class="leise">Deine Korrektur wird die massgebliche Fassung – der Reifegrad wechselt auf «überarbeitet».</p>
    <form method="post" action="/aussage/{{ a.id }}">
      <label>Kernsatz</label>
      <textarea name="kernsatz" autofocus>{{ a.kernsatz }}</textarea>
      <label>Grundsatz <span class="leise" style="font-weight:400">— das Prinzip dahinter</span></label>
      <input name="grundsatz" value="{{ a.grundsatz or '' }}" placeholder="(optional)">
      {% if a.originalton %}<p class="original">Originalton (bleibt erhalten): „{{ a.originalton }}"</p>{% endif %}
      <div class="knoepfe">
        <button type="submit">Speichern</button>
        <a class="btn btn--ghost" href="/sitzung">Abbrechen</a>
      </div>
    </form>
  </div>
</body></html>"""

# Fester Demo-Kontext für die Scheibe (noch keine Accounts/Auth).
_OWNER = "demo"
_SITZUNG_ID = "dev"


def _demo_aussage(store, aussage_id):
    """Lädt eine Aussage der Demo-Person – oder 404 (schützt fremde Daten)."""
    a = store.get_aussage(aussage_id)
    if not a or a.owner_id != _OWNER:
        abort(404)
    return a


def _db_pfad():
    return os.environ.get("KENNORA_DB", "data/kennora.db")


def _is_dev() -> bool:
    """Nur die dev-Stufe (die Pipeline setzt APP_ENV je Stufe)."""
    return os.environ.get("APP_ENV", "").strip().lower() == "dev"


# Reifegrad → (CSS-Slug ohne Umlaut, sichtbarer Marker)
_REIFE = {
    "hingeworfen":  ("roh",   '<span class="reife" title="hingeworfen">○</span>'),
    "bestätigt":    ("best",  '<span class="reife best" title="bestätigt">✓</span>'),
    "überarbeitet": ("bearb", '<span class="reife bearb" title="überarbeitet – von dir">✎</span>'),
}


def _baum_html(knoten) -> str:
    if not knoten:
        return ""
    teile = ["<ul class=\"baum\">"]
    for k in knoten:
        aid = _escape(k.get("id", ""))
        rg = k.get("reifegrad", "hingeworfen")
        slug, marker = _REIFE.get(rg, _REIFE["hingeworfen"])
        g = k.get("grundsatz")
        gs = f' <span class="grundsatz">· {_escape(g)}</span>' if g else ""
        aktionen = (
            '<span class="aktionen">'
            f'<form method="post" action="/aussage/{aid}/bestaetigen">'
            '<button class="mini" title="Bestätigen">✓</button></form>'
            f'<a class="mini" href="/aussage/{aid}/bearbeiten" title="Überarbeiten">✎</a>'
            f'<form method="post" action="/aussage/{aid}/loeschen" '
            "onsubmit=\"return confirm('Diese Aussage löschen?');\">"
            '<button class="mini" title="Löschen">🗑</button></form>'
            '</span>'
        )
        teile.append(
            f'<li class="knoten reife-{slug}">{marker} '
            f'<span class="ktext">{_escape(k.get("kernsatz", ""))}</span>{gs}{aktionen}'
        )
        if k.get("kinder"):
            teile.append(_baum_html(k["kinder"]))
        teile.append("</li>")
    teile.append("</ul>")
    return "".join(teile)


def _escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _sicht(store):
    """Baum + Netz für die Anzeige aufbereiten (Kernsatz statt id in Kanten)."""
    from .graph.projections import baum_sicht, netz_sicht

    text = {a.id: a.kernsatz for a in store.list_aussagen(_OWNER)}

    def _grundsatz_anreichern(knoten):
        for k in knoten:
            a = store.get_aussage(k["id"])
            if a and a.grundsatz:
                k["grundsatz"] = a.grundsatz
            if k.get("kinder"):
                _grundsatz_anreichern(k["kinder"])
        return knoten

    baum = _grundsatz_anreichern(baum_sicht(store, _OWNER))
    netz = netz_sicht(store, _OWNER)["kanten"]
    for k in netz:
        k["von_text"] = text.get(k["von"], k["von"])
        k["nach_text"] = text.get(k["nach"], k["nach"])
    return _baum_html(baum), netz


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

    def _render_sitzung(rueckgabe="", zwischenfrage="", fehler=""):
        from . import llm, stt
        from .graph import create_store
        store = create_store(_db_pfad())
        baum_html, netz = _sicht(store)
        return render_template_string(
            _SITZUNG, zeichen=_ZEICHEN, verfuegbar=llm.verfuegbar(),
            stt_verfuegbar=stt.transcriber().available, dev=_is_dev(),
            baum_html=baum_html, netz=netz, rueckgabe=rueckgabe,
            zwischenfrage=zwischenfrage, fehler=fehler)

    @app.get("/sitzung")
    def sitzung():
        return _render_sitzung()

    @app.post("/sitzung")
    def sitzung_ablegen():
        from .graph import create_store
        from .session import ingest

        store = create_store(_db_pfad())
        text = request.form.get("text", "")
        rueckgabe = zwischenfrage = fehler = ""
        if text.strip():
            try:
                ergebnis = ingest(store, _OWNER, _SITZUNG_ID, text)
                rueckgabe = ergebnis["rueckgabe"]
                zwischenfrage = ergebnis["zwischenfrage"]
            except Exception as e:  # noqa: BLE001 – dem Nutzer sichtbar machen
                fehler = f"{e.__class__.__name__}: {e}"
        return _render_sitzung(rueckgabe, zwischenfrage, fehler)

    @app.post("/diktat")
    def diktat():
        from . import stt
        tr = stt.transcriber()
        if not tr.available:
            return jsonify(error="STT ist nicht konfiguriert.")
        daten = request.get_json(silent=True) or {}
        b64 = daten.get("audio", "")
        if not b64:
            return jsonify(text="")
        try:
            audio = base64.b64decode(b64)
        except Exception:  # noqa: BLE001
            return jsonify(error="ungültiges Audio")
        try:
            text = tr.transcribe(audio, mimetype=daten.get("mime", "audio/webm"))
        except Exception as e:  # noqa: BLE001
            # Konkret werden: Der STT-Dienst-Status + Antwort helfen bei der
            # Diagnose (falscher Key/URL/Modell) viel mehr als der Klassenname.
            resp = getattr(e, "response", None)
            if resp is not None:
                try:
                    detail = (resp.text or "")[:300]
                except Exception:  # noqa: BLE001
                    detail = ""
                return jsonify(error=f"HTTP {resp.status_code} vom STT-Dienst: {detail}")
            return jsonify(error=f"{e.__class__.__name__}: {e}")
        return jsonify(text=text)

    @app.post("/reset")
    def reset():
        # Hart auf dev begrenzt: auf test/int/prod existiert die Funktion nicht.
        if not _is_dev():
            abort(404)
        from .graph import create_store
        create_store(_db_pfad()).reset_owner(_OWNER)
        return redirect("/sitzung")

    @app.post("/aussage/<aussage_id>/bestaetigen")
    def aussage_bestaetigen(aussage_id):
        from .graph import create_store
        store = create_store(_db_pfad())
        a = _demo_aussage(store, aussage_id)
        a.reifegrad = "bestätigt"      # Nicken: das Rohe wird bestätigt
        store.update_aussage(a)
        return redirect("/sitzung")

    @app.get("/aussage/<aussage_id>/bearbeiten")
    def aussage_bearbeiten(aussage_id):
        from .graph import create_store
        a = _demo_aussage(create_store(_db_pfad()), aussage_id)
        return render_template_string(_BEARBEITEN, zeichen=_ZEICHEN, a=a)

    @app.post("/aussage/<aussage_id>")
    def aussage_speichern(aussage_id):
        from .graph import create_store
        store = create_store(_db_pfad())
        a = _demo_aussage(store, aussage_id)
        kern = request.form.get("kernsatz", "").strip()
        if kern:
            a.kernsatz = kern
        a.grundsatz = request.form.get("grundsatz", "").strip() or None
        a.reifegrad = "überarbeitet"   # die Korrektur der Person ist massgeblich
        store.update_aussage(a)
        return redirect("/sitzung")

    @app.post("/aussage/<aussage_id>/loeschen")
    def aussage_loeschen(aussage_id):
        from .graph import create_store
        store = create_store(_db_pfad())
        _demo_aussage(store, aussage_id)   # Owner-Schutz
        store.delete_aussage(aussage_id)
        return redirect("/sitzung")

    return app
