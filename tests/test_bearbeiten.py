"""Aussagen bestätigen, überarbeiten, löschen – inkl. Owner-Schutz."""
import pytest

from app import create_app
from app.graph import Aussage, Kante, create_store


@pytest.fixture
def db(tmp_path, monkeypatch):
    pfad = str(tmp_path / "s.db")
    monkeypatch.setenv("KENNORA_DB", pfad)
    return pfad


@pytest.fixture
def client(db):
    return create_app().test_client()


def _seed(db, owner="demo", kernsatz="Ein roher Gedanke", grundsatz=None):
    store = create_store(db)
    a = Aussage(kernsatz, owner, grundsatz=grundsatz)
    store.add_aussage(a)
    return a


def test_bestaetigen_hebt_reifegrad(client, db):
    a = _seed(db)
    assert a.reifegrad == "hingeworfen"
    r = client.post(f"/aussage/{a.id}/bestaetigen")
    assert r.status_code in (302, 303)
    assert create_store(db).get_aussage(a.id).reifegrad == "bestätigt"


def test_bearbeiten_formular_zeigt_werte(client, db):
    a = _seed(db, kernsatz="Kultur macht den Menschen", grundsatz="Prinzip X")
    html = client.get(f"/aussage/{a.id}/bearbeiten").get_data(as_text=True)
    assert "Kultur macht den Menschen" in html
    assert "Prinzip X" in html


def test_speichern_setzt_ueberarbeitet(client, db):
    a = _seed(db, kernsatz="alt", grundsatz="alter Grundsatz")
    r = client.post(f"/aussage/{a.id}", data={
        "kernsatz": "Der Mensch macht Kultur.",
        "grundsatz": "Kultur ist der Akt, etwas Bedeutung zu geben.",
    })
    assert r.status_code in (302, 303)
    b = create_store(db).get_aussage(a.id)
    assert b.kernsatz == "Der Mensch macht Kultur."
    assert b.grundsatz == "Kultur ist der Akt, etwas Bedeutung zu geben."
    assert b.reifegrad == "überarbeitet"   # Korrektur der Person ist massgeblich


def test_loeschen_entfernt_aussage_und_kanten(client, db):
    store = create_store(db)
    a = Aussage("A", "demo"); b = Aussage("B", "demo")
    store.add_aussage(a); store.add_aussage(b)
    store.add_kante(Kante(a.id, b.id, "gehört-zu", "demo"))
    r = client.post(f"/aussage/{a.id}/loeschen")
    assert r.status_code in (302, 303)
    assert create_store(db).get_aussage(a.id) is None
    # Kante an A ist per Cascade mitgegangen
    assert create_store(db).list_kanten("demo") == []


def test_fremde_aussage_ist_geschuetzt(client, db):
    a = _seed(db, owner="jemand_anderes")
    assert client.post(f"/aussage/{a.id}/bestaetigen").status_code == 404
    assert client.get(f"/aussage/{a.id}/bearbeiten").status_code == 404
    assert client.post(f"/aussage/{a.id}/loeschen").status_code == 404
    assert create_store(db).get_aussage(a.id) is not None  # unangetastet
