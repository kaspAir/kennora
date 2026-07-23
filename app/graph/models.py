"""Datenmodell des Wissensgraphen: Aussage (Knoten) und Kante (werttragend)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# --- kontrollierte Vokabulare -------------------------------------------------

# Kantentypen. `gehört-zu` ist der EINZIGE hierarchische Typ – nur er bildet den
# Nachfolge-Baum. Alle übrigen leben im Netz.
KANTEN_TYPEN = (
    "gehört-zu",              # Unterknoten -> Oberbegriff (Baum)
    "widerspricht",           # steht im Widerspruch (oft nur Zwischenschritt)
    "führt-zu",               # Ursache/Begründung -> Folge
    "reimt-sich-auf",         # nicht-offensichtliche Assoziation (Netz-Magie)
    "unterscheidet-sich-durch",  # zwei Aussagen, getrennt durch ein Merkmal
)

HIERARCHIE_TYP = "gehört-zu"

REIFEGRAD_AUSSAGE = ("hingeworfen", "bestätigt", "überarbeitet")
REIFEGRAD_KANTE = ("vorgeschlagen", "bestätigt", "verworfen")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _neue_id(praefix: str) -> str:
    return f"{praefix}_{uuid.uuid4().hex[:12]}"


# --- Knoten -------------------------------------------------------------------

@dataclass
class Aussage:
    """Kleinste, für sich stehende Wissenseinheit.

    Zwei Ebenen bleiben bewusst erhalten: der geglättete `kernsatz` und der
    wörtliche `originalton` (die Stimme der Person). `grundsatz` ist das
    abstrahierte Prinzip dahinter – First-Class, weil daran die Verbindungssuche
    hängt.
    """
    kernsatz: str
    owner_id: str
    originalton: Optional[str] = None
    grundsatz: Optional[str] = None
    mandant_id: Optional[str] = None
    reifegrad: str = "hingeworfen"
    quelle_sitzung: Optional[str] = None
    embedding: Optional[list] = None            # Vektor; vorerst optional
    attribute: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: _neue_id("a"))
    erstellt_am: str = field(default_factory=_now)
    geaendert_am: str = field(default_factory=_now)

    def __post_init__(self):
        if self.reifegrad not in REIFEGRAD_AUSSAGE:
            raise ValueError(f"Unbekannter Reifegrad: {self.reifegrad!r}")


# --- Kante (Property-Edge) ----------------------------------------------------

@dataclass
class Kante:
    """Typisierte Verbindung, die selbst Werte trägt.

    Nicht bloss (von, typ, nach): `staerke`, `grundsatz_id`, `begruendung`,
    `reifegrad` und das freie `attribute`-Feld machen sie zur Property-Edge –
    genau das, was Ranking und die zurückhaltende Verbindungs-Auswahl brauchen.
    """
    von_id: str
    nach_id: str
    typ: str
    owner_id: str
    gerichtet: bool = True
    staerke: Optional[float] = None             # 0..1, z. B. Embedding-Ähnlichkeit
    grundsatz_id: Optional[str] = None          # vermittelnder Grundsatz-Knoten
    begruendung: Optional[str] = None
    reifegrad: str = "vorgeschlagen"
    mandant_id: Optional[str] = None
    quelle_sitzung: Optional[str] = None
    attribute: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: _neue_id("k"))
    erstellt_am: str = field(default_factory=_now)

    def __post_init__(self):
        if self.typ not in KANTEN_TYPEN:
            raise ValueError(f"Unbekannter Kantentyp: {self.typ!r}")
        if self.reifegrad not in REIFEGRAD_KANTE:
            raise ValueError(f"Unbekannter Kanten-Reifegrad: {self.reifegrad!r}")
        # reimt-sich-auf ist von Natur aus symmetrisch
        if self.typ == "reimt-sich-auf":
            self.gerichtet = False

    @property
    def hierarchisch(self) -> bool:
        return self.typ == HIERARCHIE_TYP
