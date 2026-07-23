"""Anbindung an Claude (Anthropic) über das offizielle SDK.

Dev-Bootstrap: direkt gegen die Anthropic-API via ``ANTHROPIC_API_KEY``.
Datenschutz-Weg (später, bewusst vertagt): ``KENNORA_LLM_BASE_URL`` auf den
Vorschalt-/Pseudonymisierungsdienst zeigen lassen – dann ist der Wechsel nur
ein Basis-URL-Tausch, kein Rewrite (analog zu den anderen Produkten, die alle
LLM-Aufrufe über die Schicht routen).
"""
from __future__ import annotations

import json
import os

# Default bewusst das stärkste Modell für die nuancierte, mehrsprachige
# Urteilsarbeit (Kernsatz/Grundsatz/Kanten). Für Volumen via Env umstellbar.
MODELL = os.environ.get("KENNORA_LLM_MODELL", "claude-opus-4-8")


def verfuegbar() -> bool:
    """True, wenn ein Weg zum Modell konfiguriert ist (Key, Token oder Proxy)."""
    return bool(
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        or os.environ.get("KENNORA_LLM_BASE_URL")
    )


def _client():
    import anthropic  # Lazy: App bootet auch ohne installiertes SDK / ohne Key.

    kwargs = {}
    base = os.environ.get("KENNORA_LLM_BASE_URL")
    if base:
        kwargs["base_url"] = base.rstrip("/")
    return anthropic.Anthropic(**kwargs)


def strukturiert(system: str, prompt: str, schema: dict, max_tokens: int = 8000) -> dict:
    """Ein Aufruf mit GARANTIERT schema-konformem JSON (structured outputs).

    Adaptives Thinking lässt Claude die Denktiefe je Aufgabe selbst wählen.
    """
    client = _client()
    resp = client.messages.create(
        model=MODELL,
        max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": schema}},
    )
    text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), "")
    return json.loads(text)
