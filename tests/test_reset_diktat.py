"""Reset (nur dev) und Diktat-Route (ohne echten STT-Aufruf)."""
import pytest

from app import create_app
from app.graph import Aussage, create_store


@pytest.fixture
def db(tmp_path, monkeypatch):
    pfad = str(tmp_path / "s.db")
    monkeypatch.setenv("KENNORA_DB", pfad)
    return pfad


@pytest.fixture
def client(db):
    return create_app().test_client()


def test_store_reset_loescht_nur_diese_person(db):
    store = create_store(db)
    store.add_aussage(Aussage("A von demo", "demo"))
    store.add_aussage(Aussage("B von anderer", "andere"))
    store.reset_owner("demo")
    assert store.list_aussagen("demo") == []
    assert len(store.list_aussagen("andere")) == 1  # fremde Daten unberührt


def test_reset_route_nur_auf_dev(client, db, monkeypatch):
    create_store(db).add_aussage(Aussage("Testdatum", "demo"))

    # Ohne APP_ENV=dev: Funktion existiert nicht.
    monkeypatch.delenv("APP_ENV", raising=False)
    assert client.post("/reset").status_code == 404
    assert len(create_store(db).list_aussagen("demo")) == 1  # nichts gelöscht

    # Mit APP_ENV=dev: setzt zurück und leitet weiter.
    monkeypatch.setenv("APP_ENV", "dev")
    r = client.post("/reset")
    assert r.status_code in (302, 303)
    assert create_store(db).list_aussagen("demo") == []


def test_reset_button_nur_auf_dev_sichtbar(client, monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    assert "Testdaten zurücksetzen" not in client.get("/sitzung").get_data(as_text=True)
    monkeypatch.setenv("APP_ENV", "dev")
    assert "Testdaten zurücksetzen" in client.get("/sitzung").get_data(as_text=True)


def test_mic_ui_nur_wenn_stt_konfiguriert(client, monkeypatch):
    monkeypatch.delenv("STT_API_KEY", raising=False)
    assert 'id="diktat-btn"' not in client.get("/sitzung").get_data(as_text=True)
    monkeypatch.setenv("STT_API_KEY", "test-key")
    assert 'id="diktat-btn"' in client.get("/sitzung").get_data(as_text=True)


def test_diktat_ohne_konfiguration_meldet_sauber(client, monkeypatch):
    monkeypatch.delenv("STT_API_KEY", raising=False)
    r = client.post("/diktat", json={"audio": "", "mime": "audio/webm"})
    assert r.status_code == 200
    assert r.get_json().get("error")
