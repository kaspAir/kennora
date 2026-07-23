"""Zwei Sichten aus **einem** Graphen.

- `baum_sicht`  – nur `gehört-zu`-Kanten, aufgeräumt, übergabereif (Nachfolge).
- `netz_sicht`  – alle übrigen (werttragenden) Kanten, assoziativ (privat).

Beide Projektionen laden Knoten und Kanten in einen In-Memory-Graphen
(NetworkX). Damit steht die volle Graph-Algorithmik zur Verfügung (Pfade,
Cluster, Zentralität), ohne einen Graph-Datenbank-Server zu betreiben.
"""
from __future__ import annotations

from typing import Optional

import networkx as nx

from .models import HIERARCHIE_TYP
from .store import GraphStore


def _lade_graph(store: GraphStore, owner_id: str) -> nx.MultiDiGraph:
    """Gesamten Graphen einer Person als NetworkX-MultiDiGraph laden."""
    g = nx.MultiDiGraph()
    for a in store.list_aussagen(owner_id):
        g.add_node(a.id, kernsatz=a.kernsatz, originalton=a.originalton,
                   grundsatz=a.grundsatz, reifegrad=a.reifegrad)
    for k in store.list_kanten(owner_id):
        g.add_edge(k.von_id, k.nach_id, key=k.id, typ=k.typ, staerke=k.staerke,
                   grundsatz_id=k.grundsatz_id, begruendung=k.begruendung,
                   reifegrad=k.reifegrad, gerichtet=k.gerichtet)
    return g


def baum_sicht(store: GraphStore, owner_id: str) -> list:
    """Nachfolge-Baum: nur `gehört-zu`. Konvention: von=Unterknoten, nach=Oberbegriff.

    Rückgabe: Liste der Wurzeln, jede als verschachteltes Dict
    {id, kernsatz, kinder:[...]}.
    """
    g = _lade_graph(store, owner_id)

    # Eltern-Beziehung nur aus gehört-zu-Kanten ableiten.
    eltern = {}          # kind_id -> parent_id
    kinder = {}          # parent_id -> [kind_id, ...]
    for von, nach, daten in g.edges(data=True):
        if daten.get("typ") == HIERARCHIE_TYP:
            eltern[von] = nach
            kinder.setdefault(nach, []).append(von)

    def teilbaum(nid: str) -> dict:
        knoten = g.nodes[nid]
        eintrag = {"id": nid, "kernsatz": knoten.get("kernsatz"),
                   "reifegrad": knoten.get("reifegrad")}
        if nid in kinder:
            eintrag["kinder"] = [teilbaum(k) for k in kinder[nid]]
        return eintrag

    wurzeln = [nid for nid in g.nodes if nid not in eltern]
    # stabile Reihenfolge: Wurzeln ohne eigene Kinder ans Ende
    wurzeln.sort(key=lambda n: (n not in kinder, n))
    return [teilbaum(w) for w in wurzeln]


def netz_sicht(store: GraphStore, owner_id: str,
               min_staerke: Optional[float] = None) -> dict:
    """Assoziatives Netz: alle Kanten AUSSER `gehört-zu`.

    `min_staerke` blendet schwache Verbindungen aus – die Basis für die
    zurückhaltende „nur die stärksten Verbindungen zeigen"-Logik.
    Rückgabe: {knoten:[...], kanten:[...]}.
    """
    g = _lade_graph(store, owner_id)
    knoten = [{"id": n, **{k: v for k, v in d.items()}} for n, d in g.nodes(data=True)]
    kanten = []
    for von, nach, daten in g.edges(data=True):
        if daten.get("typ") == HIERARCHIE_TYP:
            continue
        if min_staerke is not None and (daten.get("staerke") or 0) < min_staerke:
            continue
        kanten.append({
            "von": von, "nach": nach, "typ": daten.get("typ"),
            "staerke": daten.get("staerke"), "grundsatz_id": daten.get("grundsatz_id"),
            "begruendung": daten.get("begruendung"), "reifegrad": daten.get("reifegrad"),
        })
    # stärkste Verbindungen zuerst – so kann der Aufrufer leicht "Top-N" nehmen
    kanten.sort(key=lambda e: (e["staerke"] is not None, e["staerke"] or 0), reverse=True)
    return {"knoten": knoten, "kanten": kanten}
