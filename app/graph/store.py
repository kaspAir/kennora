"""Persistenz des Wissensgraphen hinter einer austauschbaren Schnittstelle.

`GraphStore` ist die Schnittstelle; `SQLiteGraphStore` die Implementierung für
dev (null Ops). Für test/prod kann dieselbe Schnittstelle mit MariaDB bedient
werden, für später ggf. mit einer Graph-Datenbank – ohne dass die Domäne davon
etwas merkt.
"""
from __future__ import annotations

import json
import os
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional

from .models import Aussage, Kante, HIERARCHIE_TYP

_SCHEMA = """
CREATE TABLE IF NOT EXISTS aussagen (
    id             TEXT PRIMARY KEY,
    owner_id       TEXT NOT NULL,
    mandant_id     TEXT,
    kernsatz       TEXT NOT NULL,
    originalton    TEXT,
    grundsatz      TEXT,
    reifegrad      TEXT NOT NULL DEFAULT 'hingeworfen',
    quelle_sitzung TEXT,
    embedding      TEXT,          -- JSON-Liste von Floats (vorerst optional)
    attribute      TEXT,          -- JSON-Objekt für flexible Zusatzwerte
    erstellt_am    TEXT NOT NULL,
    geaendert_am   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kanten (
    id             TEXT PRIMARY KEY,
    owner_id       TEXT NOT NULL,
    mandant_id     TEXT,
    von_id         TEXT NOT NULL,
    nach_id        TEXT NOT NULL,
    typ            TEXT NOT NULL,
    gerichtet      INTEGER NOT NULL DEFAULT 1,
    staerke        REAL,          -- Kanten-WERT: Gewicht/Konfidenz 0..1
    grundsatz_id   TEXT,          -- Kanten-WERT: vermittelnder Grundsatz-Knoten
    begruendung    TEXT,          -- Kanten-WERT: z. B. Unterscheidungsmerkmal
    reifegrad      TEXT NOT NULL DEFAULT 'vorgeschlagen',
    quelle_sitzung TEXT,
    attribute      TEXT,          -- JSON: typ-spezifische Zusatzwerte
    erstellt_am    TEXT NOT NULL,
    FOREIGN KEY (von_id)  REFERENCES aussagen(id) ON DELETE CASCADE,
    FOREIGN KEY (nach_id) REFERENCES aussagen(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_aussagen_owner ON aussagen(owner_id);
CREATE INDEX IF NOT EXISTS idx_kanten_owner   ON kanten(owner_id);
CREATE INDEX IF NOT EXISTS idx_kanten_von     ON kanten(von_id);
CREATE INDEX IF NOT EXISTS idx_kanten_nach    ON kanten(nach_id);
CREATE INDEX IF NOT EXISTS idx_kanten_typ     ON kanten(typ);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GraphStore(ABC):
    """Schnittstelle für die Graph-Persistenz (Repository-Muster)."""

    @abstractmethod
    def add_aussage(self, a: Aussage) -> Aussage: ...

    @abstractmethod
    def get_aussage(self, aussage_id: str) -> Optional[Aussage]: ...

    @abstractmethod
    def update_aussage(self, a: Aussage) -> Aussage: ...

    @abstractmethod
    def list_aussagen(self, owner_id: str) -> List[Aussage]: ...

    @abstractmethod
    def add_kante(self, k: Kante) -> Kante: ...

    @abstractmethod
    def list_kanten(self, owner_id: str, typ: Optional[str] = None) -> List[Kante]: ...

    @abstractmethod
    def reset_owner(self, owner_id: str) -> None:
        """Löscht ALLE Aussagen und Kanten einer Person (für dev-Testdaten)."""


class SQLiteGraphStore(GraphStore):
    """SQLite-Implementierung – file-basiert, null Ops, ideal für dev."""

    def __init__(self, pfad: str = "data/kennora.db"):
        self.pfad = pfad
        self._con = sqlite3.connect(pfad)
        self._con.row_factory = sqlite3.Row
        self._con.execute("PRAGMA foreign_keys = ON")
        self._con.executescript(_SCHEMA)
        self._con.commit()

    # -- Aussagen --------------------------------------------------------------

    def add_aussage(self, a: Aussage) -> Aussage:
        self._con.execute(
            """INSERT INTO aussagen
               (id, owner_id, mandant_id, kernsatz, originalton, grundsatz,
                reifegrad, quelle_sitzung, embedding, attribute,
                erstellt_am, geaendert_am)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (a.id, a.owner_id, a.mandant_id, a.kernsatz, a.originalton, a.grundsatz,
             a.reifegrad, a.quelle_sitzung, _dump(a.embedding), _dump(a.attribute),
             a.erstellt_am, a.geaendert_am),
        )
        self._con.commit()
        return a

    def get_aussage(self, aussage_id: str) -> Optional[Aussage]:
        row = self._con.execute(
            "SELECT * FROM aussagen WHERE id = ?", (aussage_id,)
        ).fetchone()
        return _aussage_aus_row(row) if row else None

    def update_aussage(self, a: Aussage) -> Aussage:
        a.geaendert_am = _now()
        self._con.execute(
            """UPDATE aussagen SET
                 kernsatz=?, originalton=?, grundsatz=?, reifegrad=?,
                 quelle_sitzung=?, embedding=?, attribute=?, geaendert_am=?
               WHERE id=?""",
            (a.kernsatz, a.originalton, a.grundsatz, a.reifegrad,
             a.quelle_sitzung, _dump(a.embedding), _dump(a.attribute),
             a.geaendert_am, a.id),
        )
        self._con.commit()
        return a

    def list_aussagen(self, owner_id: str) -> List[Aussage]:
        rows = self._con.execute(
            "SELECT * FROM aussagen WHERE owner_id = ? ORDER BY erstellt_am",
            (owner_id,),
        ).fetchall()
        return [_aussage_aus_row(r) for r in rows]

    # -- Kanten ----------------------------------------------------------------

    def add_kante(self, k: Kante) -> Kante:
        self._con.execute(
            """INSERT INTO kanten
               (id, owner_id, mandant_id, von_id, nach_id, typ, gerichtet,
                staerke, grundsatz_id, begruendung, reifegrad, quelle_sitzung,
                attribute, erstellt_am)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (k.id, k.owner_id, k.mandant_id, k.von_id, k.nach_id, k.typ,
             1 if k.gerichtet else 0, k.staerke, k.grundsatz_id, k.begruendung,
             k.reifegrad, k.quelle_sitzung, _dump(k.attribute), k.erstellt_am),
        )
        self._con.commit()
        return k

    def list_kanten(self, owner_id: str, typ: Optional[str] = None) -> List[Kante]:
        if typ is None:
            rows = self._con.execute(
                "SELECT * FROM kanten WHERE owner_id = ? ORDER BY erstellt_am",
                (owner_id,),
            ).fetchall()
        else:
            rows = self._con.execute(
                "SELECT * FROM kanten WHERE owner_id = ? AND typ = ? ORDER BY erstellt_am",
                (owner_id, typ),
            ).fetchall()
        return [_kante_aus_row(r) for r in rows]

    def reset_owner(self, owner_id: str) -> None:
        self._con.execute("DELETE FROM kanten WHERE owner_id = ?", (owner_id,))
        self._con.execute("DELETE FROM aussagen WHERE owner_id = ?", (owner_id,))
        self._con.commit()

    def close(self):
        self._con.close()


def create_store(pfad: str = "data/kennora.db") -> GraphStore:
    """Factory – heute SQLite. Hier wird später der Backend-Wechsel entschieden."""
    ordner = os.path.dirname(pfad)
    if ordner:
        os.makedirs(ordner, exist_ok=True)
    return SQLiteGraphStore(pfad)


# --- (De-)Serialisierung ------------------------------------------------------

def _dump(wert) -> Optional[str]:
    return None if wert is None else json.dumps(wert, ensure_ascii=False)


def _load(text) -> Optional[object]:
    return None if text is None else json.loads(text)


def _aussage_aus_row(r: sqlite3.Row) -> Aussage:
    return Aussage(
        id=r["id"], owner_id=r["owner_id"], mandant_id=r["mandant_id"],
        kernsatz=r["kernsatz"], originalton=r["originalton"], grundsatz=r["grundsatz"],
        reifegrad=r["reifegrad"], quelle_sitzung=r["quelle_sitzung"],
        embedding=_load(r["embedding"]), attribute=_load(r["attribute"]) or {},
        erstellt_am=r["erstellt_am"], geaendert_am=r["geaendert_am"],
    )


def _kante_aus_row(r: sqlite3.Row) -> Kante:
    return Kante(
        id=r["id"], owner_id=r["owner_id"], mandant_id=r["mandant_id"],
        von_id=r["von_id"], nach_id=r["nach_id"], typ=r["typ"],
        gerichtet=bool(r["gerichtet"]), staerke=r["staerke"],
        grundsatz_id=r["grundsatz_id"], begruendung=r["begruendung"],
        reifegrad=r["reifegrad"], quelle_sitzung=r["quelle_sitzung"],
        attribute=_load(r["attribute"]) or {}, erstellt_am=r["erstellt_am"],
    )
