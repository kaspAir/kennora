"""Diktat: Speech-to-Text über einen OpenAI-kompatiblen Endpoint.

Anbieter-flexibel via Env (STT_API_URL/-KEY/-MODEL): OpenAI, Groq, Azure oder
eine CH-gehostete Whisper-Instanz (Datenresidenz). Ohne Key inaktiv – das
Deployment bleibt gefahrlos.

**Mehrsprachig:** STT_LANGUAGE ist bewusst LEER voreingestellt → der Dienst
erkennt die Sprache selbst. Das ist kennoras Kern: reden, wie einem der Schnabel
gewachsen ist. Nur setzen, wenn man bewusst auf eine Sprache festnageln will.

Zwei Antwortstile werden automatisch erkannt: synchron (`text` in der Antwort)
und asynchron (`batch_id` → `/results/{id}` pollen, z. B. Infomaniak AI Services
in Schweizer Rechenzentren).
"""
from __future__ import annotations

import os
import time

import requests

_TEXT_KEYS = ("text", "transcription", "transcript")
_FERTIG = {"done", "finished", "success", "succeeded", "completed", "complete", "ok"}
_FEHLER = {"error", "failed", "failure", "canceled", "cancelled"}
_KEIN_TEXT = _FERTIG | _FEHLER | {"pending", "processing", "running", "queued", "waiting"}


def _entpacke(d):
    while isinstance(d, dict) and isinstance(d.get("data"), (dict, list)):
        d = d["data"]
    return d


def _status(d):
    d = _entpacke(d)
    if isinstance(d, dict):
        for k in ("status", "state"):
            v = d.get(k)
            if isinstance(v, str):
                return v.strip().lower()
    return ""


def _text_aus(d):
    d = _entpacke(d)
    kandidaten = [d] if isinstance(d, dict) else (d if isinstance(d, list) else [])
    for eintrag in kandidaten:
        if not isinstance(eintrag, dict):
            continue
        for k in _TEXT_KEYS:
            v = eintrag.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        for v in eintrag.values():
            if isinstance(v, (dict, list)):
                t = _text_aus(v)
                if t:
                    return t
    return ""


class Transcriber:
    def __init__(self, api_url=None, api_key="", model="whisper-1", language="",
                 timeout=45, poll_timeout=100, poll_intervall=2.0):
        self.api_url = api_url or "https://api.openai.com/v1/audio/transcriptions"
        self.api_key = api_key or ""
        self.model = model
        self.language = language or ""        # leer -> Sprache NICHT senden (Auto)
        self.timeout = timeout
        self.poll_timeout = poll_timeout      # bewusst < Gunicorn-Worker-Timeout
        self.poll_intervall = poll_intervall

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _results_url(self, batch_id):
        basis = self.api_url.split("/openai/audio/transcriptions")[0].rstrip("/")
        return f"{basis}/results/{batch_id}"

    def transcribe(self, audio_bytes, filename="diktat.webm", mimetype="audio/webm") -> str:
        if not self.api_key or not audio_bytes:
            return ""
        data = {"model": self.model}
        if self.language:
            data["language"] = self.language
        resp = requests.post(
            self.api_url, headers={"Authorization": f"Bearer {self.api_key}"},
            files={"file": (filename, audio_bytes, mimetype)},
            data=data, timeout=self.timeout,
        )
        resp.raise_for_status()
        try:
            body = resp.json() or {}
        except ValueError:
            return (resp.text or "").strip()
        text = _text_aus(body)
        if text:
            return text
        entpackt = _entpacke(body)
        batch_id = entpackt.get("batch_id") if isinstance(entpackt, dict) else None
        return self._warte_auf_ergebnis(str(batch_id)) if batch_id else ""

    def _warte_auf_ergebnis(self, batch_id):
        url = self._results_url(batch_id)
        ende = time.monotonic() + self.poll_timeout
        while time.monotonic() < ende:
            try:
                r = requests.get(url, headers={"Authorization": f"Bearer {self.api_key}"},
                                 timeout=self.timeout)
            except requests.RequestException:
                return ""
            if r.status_code == 200:
                try:
                    body = r.json() or {}
                except ValueError:
                    body = {}
                if _status(body) in _FEHLER:
                    return ""
                text = _text_aus(body)
                if text:
                    return text
                if _status(body) in _FERTIG:
                    return self._download(batch_id)
            time.sleep(self.poll_intervall)
        return ""

    def _download(self, batch_id):
        try:
            r = requests.get(f"{self._results_url(batch_id)}/download",
                             headers={"Authorization": f"Bearer {self.api_key}"},
                             timeout=self.timeout)
        except requests.RequestException:
            return ""
        if r.status_code != 200:
            return ""
        try:
            return _text_aus(r.json() or {}) or ""
        except ValueError:
            return (r.text or "").strip()


def transcriber() -> Transcriber:
    """Baut den Transcriber aus der Umgebung (einfach, zustandslos)."""
    return Transcriber(
        api_url=os.environ.get("STT_API_URL"),
        api_key=os.environ.get("STT_API_KEY", ""),
        model=os.environ.get("STT_MODEL", "whisper-1"),
        language=os.environ.get("STT_LANGUAGE", ""),  # leer = mehrsprachig/Auto
    )
