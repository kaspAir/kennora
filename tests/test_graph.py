"""Wissensgraph: Persistenz, werttragende Kanten und die zwei Sicht-Projektionen.

Baut einen Ausschnitt des Ruth-Beispiels nach.
"""
import pytest

from app.graph import Aussage, Kante, create_store
from app.graph.projections import baum_sicht, netz_sicht


@pytest.fixture
def store(tmp_path):
    return create_store(str(tmp_path / "test.db"))


@pytest.fixture
def ruth_graph(store):
    """Kleiner, aber vollständiger Ausschnitt: Baum-Kanten + eine Netz-Kante."""
    o = "ruth"
    # Knoten
    ausschreibungen = store.add_aussage(Aussage("Ausschreibungen", o, reifegrad="bestätigt"))
    anforderungen = store.add_aussage(Aussage(
        "Anforderungen vorab mit den Fachleuten sauber klären.", o,
        originalton="d Aaforderige vorhär mit de Fachlüt suuber klären",
        reifegrad="bestätigt"))
    nachwuchs = store.add_aussage(Aussage("Nachwuchs / Weitergabe", o, reifegrad="bestätigt"))
    junge = store.add_aussage(Aussage(
        "Junge früh selbst Ausschreibungen führen lassen, auch wenn es nicht perfekt wird.", o,
        grundsatz="Man lernt nur, wenn man selbst handeln darf.", reifegrad="bestätigt"))
    enkel = store.add_aussage(Aussage(
        "Auch bei den Enkeln kleine Fehler zulassen, damit sie lernen.", o,
        originalton="mer mues sie chlini Fähler la mache",
        grundsatz="Man lernt nur, wenn man selbst handeln darf."))
    grundsatz = store.add_aussage(Aussage(
        "Menschen lernen nur, wenn sie selbst handeln dürfen.", o, reifegrad="bestätigt"))

    # Baum-Kanten (gehört-zu: Unterknoten -> Oberbegriff)
    store.add_kante(Kante(anforderungen.id, ausschreibungen.id, "gehört-zu", o,
                          reifegrad="bestätigt"))
    store.add_kante(Kante(junge.id, nachwuchs.id, "gehört-zu", o, reifegrad="bestätigt"))

    # Netz-Kante: die seltene, werttragende Verbindung
    store.add_kante(Kante(
        junge.id, enkel.id, "reimt-sich-auf", o,
        staerke=0.82, grundsatz_id=grundsatz.id,
        begruendung="gleicher Grundsatz: selbst handeln dürfen",
        reifegrad="bestätigt"))

    return store, o, {"junge": junge.id, "enkel": enkel.id, "grundsatz": grundsatz.id}


def test_kante_traegt_werte(ruth_graph):
    store, o, ids = ruth_graph
    reim = [k for k in store.list_kanten(o) if k.typ == "reimt-sich-auf"][0]
    assert reim.staerke == 0.82
    assert reim.grundsatz_id == ids["grundsatz"]
    assert reim.begruendung.startswith("gleicher Grundsatz")
    # reimt-sich-auf ist symmetrisch -> gerichtet wird automatisch False
    assert reim.gerichtet is False


def test_reifegrad_wechsel_bleibt_erhalten(store):
    o = "ruth"
    a = store.add_aussage(Aussage("hingeworfener Gedanke", o))
    assert a.reifegrad == "hingeworfen"
    a.reifegrad = "bestätigt"
    store.update_aussage(a)
    assert store.get_aussage(a.id).reifegrad == "bestätigt"


def test_baum_zeigt_nur_hierarchie(ruth_graph):
    store, o, _ = ruth_graph
    baum = baum_sicht(store, o)
    wurzeln = {w["kernsatz"] for w in baum}
    assert "Ausschreibungen" in wurzeln
    assert "Nachwuchs / Weitergabe" in wurzeln
    # unter Ausschreibungen hängt "Anforderungen ..."
    ausschr = next(w for w in baum if w["kernsatz"] == "Ausschreibungen")
    kinder = {k["kernsatz"] for k in ausschr.get("kinder", [])}
    assert any(k.startswith("Anforderungen") for k in kinder)


def test_netz_enthaelt_reim_aber_keine_hierarchie(ruth_graph):
    store, o, _ = ruth_graph
    netz = netz_sicht(store, o)
    typen = {k["typ"] for k in netz["kanten"]}
    assert "reimt-sich-auf" in typen
    assert "gehört-zu" not in typen          # Hierarchie gehört NICHT ins Netz
    # die werttragende Kante ist als stärkste zuerst gelistet
    assert netz["kanten"][0]["staerke"] == 0.82


def test_netz_min_staerke_filtert(ruth_graph):
    store, o, _ = ruth_graph
    # Schwelle über der einzigen Kante -> Netz ist leer (Basis der Zurückhaltung)
    netz = netz_sicht(store, o, min_staerke=0.9)
    assert netz["kanten"] == []
