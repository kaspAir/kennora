# Kennora

**Wissen entsteht im Gespräch.** Kennora ermöglicht Wissensübertragung durch
Sprechen: Man redet frei (auch auf Schweizerdeutsch), das System strukturiert
das Gesagte sauber – aber menschlich –, legt es ab und baut über viele
Sitzungen hinweg darauf auf. Es stellt sehr zurückhaltend Zwischenfragen und
bietet selten, aber gezielt nicht-offensichtliche Verbindungen an.

Zwei Modi auf demselben Fundament:

- **Firmen-Modus** – Organisations-Mandant mit Mitarbeitenden-Accounts;
  zielgerichtete Übergabe von Wissen (Nachfolge, Onboarding).
- **Privat-Modus** – ein persönlicher Account mit personalisierter Oberfläche;
  offen und assoziativ, für alles, worüber man reden will.

## Architektur (im Aufbau)

Ein einziger **Wissensgraph** als Substrat: Knoten sind *Aussagen* (sauberer
Kernsatz + Originalton + Herkunft + Reifegrad), Kanten haben Typen
(*gehört-zu*, *widerspricht*, *führt-zu*, *reimt-sich-auf*). Daraus zwei
Sichten – ein aufgeräumter **Baum** (übergabetauglich) und ein **Netz**
(assoziativ). Die Struktur wächst additiv; umsortiert wird nur auf Vorschlag.

Dieses Repo enthält vorerst ein minimales, lauffähiges Gerüst (Startseite +
Health-Endpoint), auf dem die Domäne schrittweise entsteht.

## Lokal starten

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py            # http://127.0.0.1:5000
```

Tests:

```bash
pip install -r tests/requirements.txt
python -m pytest -q
```

## Deployment

Vier Umgebungen auf dem geteilten Infomaniak-Host, je Branch ein Jenkins-Job
(Pipeline script from SCM). Promotion streng sequenziell:

| Branch        | Umgebung | URL             | Port |
|---------------|----------|-----------------|------|
| `develop`     | dev      | dev.kennora.ch  | 8050 |
| `test`        | test     | test.kennora.ch | 8051 |
| `integration` | int      | int.kennora.ch  | 8052 |
| `main`        | prod     | kennora.ch      | 8053 |

Gunicorn bindet lokal auf den Stufen-Port; ein PHP-Reverse-Proxy
(`deploy/proxy.php` + `deploy/.htaccess`) reicht die Subdomain weiter. Ein
Watchdog-Cron (`deploy/keepalive.sh`) hält den Prozess am Leben. Details siehe
`Jenkinsfile`.
