"""Aus gesprochenem Text Aussagen, Grundsätze und Kantenvorschläge gewinnen.

Kernhaltung (siehe Styleguide/Konzept):
- Der Mensch spricht in BELIEBIGER Sprache/Mundart. kennora passt sich an –
  der Kernsatz entsteht in DERSELBEN Sprache, nie umgekehrt.
- Der Grundsatz (das abstrahierte Prinzip) ist First-Class – daran hängt später
  die Verbindungssuche.
- Struktur wächst ADDITIV: an bestehende Aussagen anknüpfen statt umbauen.
- Sehr zurückhaltend: höchstens EINE Zwischenfrage, seltene Verbindungs-Angebote.
- Alles landet zunächst als «hingeworfen»/«vorgeschlagen»; Bestätigung später.
"""
from __future__ import annotations

from ..graph import Aussage, Kante, KANTEN_TYPEN
from ..graph.store import GraphStore

# --- Structured-Output-Schema (garantiert schema-konform) --------------------
# Bewusst ohne null-Typen: fehlende Werte kommen als "" (robuster bei
# structured outputs). Der Code deutet "" als «nicht vorhanden».
_STR = {"type": "string"}
EXTRAKT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["sprache", "aussagen", "kanten", "rueckgabe", "zwischenfrage"],
    "properties": {
        "sprache": _STR,  # erkannte Sprache des Gesagten, z. B. "de-CH", "fr"
        "aussagen": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["temp_id", "kernsatz", "originalton", "grundsatz", "anschluss_an"],
                "properties": {
                    "temp_id": _STR,          # lokale Referenz für Kanten dieses Aufrufs
                    "kernsatz": _STR,         # sauber, in der GESPROCHENEN Sprache
                    "originalton": _STR,      # wörtlicher Ausschnitt
                    "grundsatz": _STR,        # Prinzip dahinter, "" wenn keins
                    "anschluss_an": _STR,     # id einer BESTEHENDEN Aussage (Oberbegriff) oder ""
                },
            },
        },
        "kanten": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["von", "nach", "typ", "begruendung"],
                "properties": {
                    "von": _STR,   # temp_id ODER bestehende Aussage-id
                    "nach": _STR,
                    "typ": {"type": "string", "enum": list(KANTEN_TYPEN)},
                    "begruendung": _STR,
                },
            },
        },
        "rueckgabe": _STR,       # kurze Spiegelung an die Person, in ihrer Sprache
        "zwischenfrage": _STR,   # höchstens EINE, oder "" wenn keine nötig
    },
}

_SYSTEM = """Du bist kennora – ein Zuhörer, kein Moderator. Menschen sprechen dir \
frei ihr Wissen zu, in beliebiger Sprache oder Mundart (auch gemischt). Deine \
Aufgabe ist, das Gesagte still zu strukturieren.

Grundsätze:
- ANTWORTE UND FORMULIERE IN DER SPRACHE, IN DER GESPROCHEN WURDE. Erkenne sie \
und gib sie in `sprache` an. Übersetze NICHT.
- Zerlege das Gesagte in einzelne, für sich stehende AUSSAGEN. Der `kernsatz` ist \
sauber und menschlich – aber in der gesprochenen Sprache. Der `originalton` ist \
ein wörtlicher Ausschnitt. Erfinde nichts dazu.
- Ziehe wo möglich den `grundsatz` heraus: das allgemeine Prinzip hinter einer \
Aussage (z. B. «Man lernt nur, wenn man selbst handeln darf»). Sonst "".
- BEWAHRE RICHTUNG UND ABSICHT der Person. Dreh Ursache und Wirkung NICHT um. \
Beispiel: «Der Mensch macht Kultur, Kultur ist der Akt, etwas Bedeutung zu geben» \
darf NICHT zu «Kultur ist relevant, wenn sie dem Menschen Bedeutung gibt» werden – \
das ist die plausibel klingende Umkehrung, aber nicht das Gemeinte. Kernsatz und \
Grundsatz müssen die Denkrichtung des Sprechers treffen.
- BAUE EIN THEMATISCHES GERÜST (wie ein Inhaltsverzeichnis): Erkenne die wenigen, \
breiten Themen/Bereiche, über die jemand spricht (z. B. «Kultur», «Technik», \
«Anthropologie»), und lege dafür kurze Bereichs-Aussagen an, unter die du die \
konkreten Aussagen hängst. Wenige, stabile Bereiche – nicht für jeden Satz einen \
neuen. So wird der Baum lesbar und übergabetauglich.
- Wachse ADDITIV: Bestehende Bereiche/Aussagen aus der Kontextliste WIEDERVERWENDEN \
(via `anschluss_an` = deren id), nie duplizieren, bestehende Struktur nicht umbauen. \
An in DIESEM Aufruf neu angelegte Bereiche hängst du Aussagen per gehört-zu-Kante \
(temp_id → temp_id des Bereichs).
- Kanten sparsam und nur wenn echt: gehört-zu (Hierarchie), widerspricht (nur wenn \
es einer bestehenden Aussage widerspricht – als Verständnisfrage behandeln, nicht \
als Korrektur), führt-zu (Ursache→Folge), reimt-sich-auf (SELTEN: nur eine wirklich \
nicht-offensichtliche Verbindung), unterscheidet-sich-durch.
- `zwischenfrage`: höchstens EINE, und nur bei echter Lücke in einer Kausalkette, \
einem Widerspruch, oder einer ertragreichen Gabelung. Im Zweifel "". Nie ein \
Formular, nie Pflichtfelder.
- `rueckgabe`: ein bis zwei warme Sätze, die zeigen, was angekommen ist und wo \
etwas gewachsen ist – in der gesprochenen Sprache."""


def _graph_kontext(store: GraphStore, owner_id: str) -> str:
    """Bestehende Aussagen (id, Kernsatz, Grundsatz) als Kontext für Anknüpfung."""
    zeilen = []
    for a in store.list_aussagen(owner_id):
        g = f"  · Grundsatz: {a.grundsatz}" if a.grundsatz else ""
        zeilen.append(f"[{a.id}] {a.kernsatz}{g}")
    if not zeilen:
        return "(noch keine Aussagen – dies ist der Anfang.)"
    return "\n".join(zeilen)


def _llm_extract(transkript: str, kontext: str) -> dict:
    from .. import llm

    prompt = (
        "Bereits erfasste Aussagen dieser Person (zum Anknüpfen, id in eckigen "
        f"Klammern):\n{kontext}\n\n"
        f"Neu gesprochen:\n\"\"\"\n{transkript}\n\"\"\"\n\n"
        "Strukturiere NUR das neu Gesprochene. Knüpfe wo sinnvoll an bestehende "
        "Aussagen an (anschluss_an / Kanten mit bestehenden ids)."
    )
    return llm.strukturiert(_SYSTEM, prompt, EXTRAKT_SCHEMA)


def ingest(store: GraphStore, owner_id: str, sitzung: str, transkript: str,
           *, mandant_id=None, llm=None) -> dict:
    """Verarbeitet einen gesprochenen Beitrag additiv in den Graphen.

    `llm` ist eine Funktion (transkript, kontext) -> dict; per Vorgabe der echte
    Claude-Aufruf, in Tests ein Stub. Rückgabe: was entstand + Rückgabe/Frage.
    """
    transkript = (transkript or "").strip()
    if not transkript:
        return {"aussagen": [], "kanten": [], "rueckgabe": "", "zwischenfrage": "", "sprache": ""}

    kontext = _graph_kontext(store, owner_id)
    daten = (llm or _llm_extract)(transkript, kontext)
    return _anwenden(store, owner_id, sitzung, mandant_id, daten)


def _anwenden(store, owner_id, sitzung, mandant_id, daten: dict) -> dict:
    sprache = (daten.get("sprache") or "").strip()
    temp_zu_id = {}
    neue_aussagen = []

    for roh in daten.get("aussagen", []):
        kernsatz = (roh.get("kernsatz") or "").strip()
        if not kernsatz:
            continue
        a = Aussage(
            kernsatz=kernsatz,
            owner_id=owner_id,
            originalton=(roh.get("originalton") or "").strip() or None,
            grundsatz=(roh.get("grundsatz") or "").strip() or None,
            mandant_id=mandant_id,
            quelle_sitzung=sitzung,
            reifegrad="hingeworfen",
            attribute={"sprache": sprache} if sprache else {},
        )
        store.add_aussage(a)
        neue_aussagen.append(a)
        temp = (roh.get("temp_id") or "").strip()
        if temp:
            temp_zu_id[temp] = a.id
        # Anknüpfung an eine bestehende Aussage → gehört-zu-Kante (additiv).
        anschluss = (roh.get("anschluss_an") or "").strip()
        if anschluss and store.get_aussage(anschluss):
            store.add_kante(Kante(a.id, anschluss, "gehört-zu", owner_id,
                                  mandant_id=mandant_id, quelle_sitzung=sitzung,
                                  reifegrad="vorgeschlagen"))

    def _aufloesen(ref: str):
        ref = (ref or "").strip()
        if ref in temp_zu_id:
            return temp_zu_id[ref]
        return ref if store.get_aussage(ref) else None

    neue_kanten = []
    for roh in daten.get("kanten", []):
        von = _aufloesen(roh.get("von", ""))
        nach = _aufloesen(roh.get("nach", ""))
        typ = roh.get("typ", "")
        if not von or not nach or von == nach or typ not in KANTEN_TYPEN:
            continue
        k = Kante(von, nach, typ, owner_id, mandant_id=mandant_id,
                  quelle_sitzung=sitzung, reifegrad="vorgeschlagen",
                  begruendung=(roh.get("begruendung") or "").strip() or None)
        store.add_kante(k)
        neue_kanten.append(k)

    return {
        "sprache": sprache,
        "aussagen": neue_aussagen,
        "kanten": neue_kanten,
        "rueckgabe": (daten.get("rueckgabe") or "").strip(),
        "zwischenfrage": (daten.get("zwischenfrage") or "").strip(),
    }
