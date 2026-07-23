"""Sitzungs-Loop: Extraktion (gestubbt) -> additiver Graph -> Sichten.

Der LLM-Aufruf wird durch einen Stub ersetzt; keine API/Keys nötig.
"""
import pytest

from app.graph import create_store
from app.graph.projections import baum_sicht, netz_sicht
from app.session import ingest


@pytest.fixture
def store(tmp_path):
    return create_store(str(tmp_path / "s.db"))


def test_erste_sitzung_baut_baum_additiv(store):
    def stub(transkript, kontext):
        return {
            "sprache": "de-CH",
            "aussagen": [
                {"temp_id": "n1", "kernsatz": "Ausschreibungen", "originalton": "",
                 "grundsatz": "", "anschluss_an": ""},
                {"temp_id": "n2",
                 "kernsatz": "Anforderungen vorab mit den Fachleuten klären.",
                 "originalton": "d Aaforderige vorhär klären",
                 "grundsatz": "Klarheit vor Vertrag.", "anschluss_an": ""},
            ],
            "kanten": [{"von": "n2", "nach": "n1", "typ": "gehört-zu", "begruendung": ""}],
            "rueckgabe": "Guter Anfang – Ausschreibungen nimmt Form an.",
            "zwischenfrage": "",
        }

    res = ingest(store, "demo", "s1", "…gesprochen…", llm=stub)

    assert len(res["aussagen"]) == 2
    assert res["sprache"] == "de-CH"
    assert res["rueckgabe"].startswith("Guter Anfang")
    # Reifegrade: Aussagen hingeworfen, Kante vorgeschlagen (Bestätigung später).
    assert all(a.reifegrad == "hingeworfen" for a in res["aussagen"])
    assert res["kanten"][0].reifegrad == "vorgeschlagen"
    # Originalton + Grundsatz + Sprache erhalten
    kind = next(a for a in res["aussagen"] if a.kernsatz.startswith("Anforderungen"))
    assert kind.originalton == "d Aaforderige vorhär klären"
    assert kind.grundsatz == "Klarheit vor Vertrag."
    assert kind.attribute.get("sprache") == "de-CH"
    # Baum: Ausschreibungen mit Kind
    baum = baum_sicht(store, "demo")
    wurzel = next(w for w in baum if w["kernsatz"] == "Ausschreibungen")
    assert any(k["kernsatz"].startswith("Anforderungen") for k in wurzel.get("kinder", []))


def test_zweite_sitzung_knuepft_an_bestehende_id(store):
    def stub1(t, k):
        return {"sprache": "de", "aussagen": [
            {"temp_id": "n1", "kernsatz": "Ausschreibungen", "originalton": "",
             "grundsatz": "", "anschluss_an": ""}],
            "kanten": [], "rueckgabe": "", "zwischenfrage": ""}

    res1 = ingest(store, "demo", "s1", "…", llm=stub1)
    wurzel_id = res1["aussagen"][0].id

    # Zweite Sitzung: neue Aussage hängt sich an die BESTEHENDE Wurzel (per id).
    def stub2(t, k):
        return {"sprache": "de", "aussagen": [
            {"temp_id": "m1", "kernsatz": "Nachträge sofort schriftlich.",
             "originalton": "", "grundsatz": "Schriftlichkeit beim Abwickeln.",
             "anschluss_an": wurzel_id}],
            "kanten": [], "rueckgabe": "Nachträge ist gewachsen.", "zwischenfrage": ""}

    ingest(store, "demo", "s2", "…", llm=stub2)

    baum = baum_sicht(store, "demo")
    wurzel = next(w for w in baum if w["kernsatz"] == "Ausschreibungen")
    kinder = {k["kernsatz"] for k in wurzel.get("kinder", [])}
    assert "Nachträge sofort schriftlich." in kinder


def test_reim_landet_im_netz_nicht_im_baum(store):
    def stub(t, k):
        return {"sprache": "de", "aussagen": [
            {"temp_id": "a", "kernsatz": "Junge selbst führen lassen.",
             "originalton": "", "grundsatz": "Selbst handeln dürfen.", "anschluss_an": ""},
            {"temp_id": "b", "kernsatz": "Enkeln Fehler zulassen.",
             "originalton": "", "grundsatz": "Selbst handeln dürfen.", "anschluss_an": ""}],
            "kanten": [{"von": "a", "nach": "b", "typ": "reimt-sich-auf",
                        "begruendung": "gleicher Grundsatz"}],
            "rueckgabe": "", "zwischenfrage": ""}

    ingest(store, "demo", "s1", "…", llm=stub)

    netz = netz_sicht(store, "demo")
    typen = {e["typ"] for e in netz["kanten"]}
    assert "reimt-sich-auf" in typen
    assert "gehört-zu" not in typen  # Reim gehört NICHT in den Baum


def test_leerer_beitrag_ist_geraeuschlos(store):
    res = ingest(store, "demo", "s1", "   ", llm=lambda t, k: {})
    assert res["aussagen"] == [] and res["rueckgabe"] == ""
