"""Wissensgraph-Domäne von kennora.

Ein einziges Substrat: **Aussagen** (Knoten) und **Kanten** (typisierte,
werttragende Verbindungen). Daraus werden zwei Sichten projiziert – ein
aufgeräumter Baum (nur `gehört-zu`) und ein assoziatives Netz (alle übrigen
Kantentypen).

Persistenz liegt hinter der Schnittstelle `GraphStore` (siehe `store.py`),
damit ein späterer Wechsel auf eine Graph-Datenbank ein Backend-Tausch bleibt
und kein Rewrite.
"""
from .models import Aussage, Kante, KANTEN_TYPEN, REIFEGRAD_AUSSAGE, REIFEGRAD_KANTE
from .store import GraphStore, SQLiteGraphStore, create_store

__all__ = [
    "Aussage", "Kante", "KANTEN_TYPEN", "REIFEGRAD_AUSSAGE", "REIFEGRAD_KANTE",
    "GraphStore", "SQLiteGraphStore", "create_store",
]
