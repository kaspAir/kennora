"""Baut das eigenständige kennora-Benutzerhandbuch (docs/handbuch.html).

Bettet Screenshots (docs/bilder/) und die Schriften (app/static/fonts/) als
Base64 ein → eine einzige, offline lesbare und teilbare HTML-Datei im
kennora-Look. Aufruf:  python scripts/build_handbuch.py
"""
from __future__ import annotations

import base64
import os

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HIER)


def b64(pfad: str) -> str:
    with open(pfad, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def bild(name: str) -> str:
    return "data:image/png;base64," + b64(os.path.join(ROOT, "docs", "bilder", name))


def fontface(fam: str, gewicht: int, datei: str) -> str:
    d = "data:font/woff2;base64," + b64(os.path.join(ROOT, "app", "static", "fonts", datei))
    return (f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{gewicht};"
            f"font-display:swap;src:url({d}) format('woff2');}}")


FONTS = "".join([
    fontface("EB Garamond", 500, "ebgaramond-500.woff2"),
    fontface("EB Garamond", 600, "ebgaramond-600.woff2"),
    fontface("Hanken Grotesk", 400, "hankengrotesk-400.woff2"),
    fontface("Hanken Grotesk", 600, "hankengrotesk-600.woff2"),
    fontface("Hanken Grotesk", 700, "hankengrotesk-700.woff2"),
])

MARK = """<svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="4"
 stroke-linecap="round" aria-hidden="true"><circle cx="60" cy="60" r="46"/>
 <circle cx="60" cy="60" r="27"/><circle cx="60" cy="60" r="11"/>
 <path d="M 71.12 25.76 A 36 36 0 0 1 93.83 47.69"/></svg>"""

HTML = r"""<!doctype html><html lang="de"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>kennora — Benutzerhandbuch</title>
<style>
%%FONTS%%
:root{
  --marke:#4076B9; --marke-tief:#2C5591; --warm:#C79A6E; --tinte:#23262D;
  --papier:#F8F6F2; --dunkelgrund:#22232B; --leise:#6b7078; --linie:#e4e0d8;
  --font-display:"EB Garamond",Georgia,serif;
  --font-text:"Hanken Grotesk",system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;font-family:var(--font-text);color:var(--tinte);background:var(--papier);
  line-height:1.6;-webkit-font-smoothing:antialiased;}
.wrap{max-width:820px;margin:0 auto;padding:0 1.4rem 6rem;}
a{color:var(--marke);}
/* Titel */
.hero{text-align:center;padding:4.5rem 0 2.5rem;border-bottom:1px solid var(--linie);margin-bottom:3rem;}
.hero .mark{width:82px;height:82px;color:var(--marke);margin:0 auto 1rem;}
.hero .mark svg{width:100%;height:100%;display:block;}
.hero h1{font-family:var(--font-display);font-weight:500;font-size:3rem;margin:.2rem 0 0;}
.hero .sub{font-size:1.15rem;color:var(--leise);margin:.3rem 0 0;}
.hero .eb{font-size:.72rem;letter-spacing:.22em;text-transform:uppercase;color:var(--warm);
  font-weight:700;margin-bottom:.5rem;}
/* Inhalt */
h2{font-family:var(--font-display);font-weight:600;font-size:1.75rem;margin:3.2rem 0 .3rem;
  padding-top:1.2rem;border-top:1px solid var(--linie);}
h2:first-of-type{border-top:none;}
h3{font-family:var(--font-display);font-weight:500;font-size:1.28rem;margin:1.8rem 0 .3rem;}
h2 .n{color:var(--warm);font-size:1.1rem;margin-right:.5rem;vertical-align:.08em;}
p{margin:.7rem 0;}
strong{font-weight:700;}
figure{margin:1.6rem 0;}
figure img{width:100%;display:block;border:1px solid var(--linie);border-radius:12px;
  box-shadow:0 8px 30px rgba(35,38,45,.07);}
figcaption{color:var(--leise);font-size:.88rem;margin-top:.6rem;text-align:center;}
ul{padding-left:1.2rem;}
li{margin:.35rem 0;}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86em;
  background:#efece5;padding:.08em .35em;border-radius:4px;}
.lead{font-size:1.12rem;}
.callout{background:#fff;border:1px solid var(--linie);border-left:3px solid var(--marke);
  border-radius:10px;padding:1rem 1.2rem;margin:1.4rem 0;}
.rueck{background:rgba(199,154,110,.14);border-left:3px solid var(--warm);
  border-radius:10px;padding:1rem 1.2rem;margin:1.2rem 0;}
.rueck .frage{font-style:italic;color:var(--leise);margin-top:.5rem;}
.tag{font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;color:var(--leise);
  font-weight:700;}
/* Reifegrad-Legende */
.legende{width:100%;border-collapse:collapse;margin:1rem 0;}
.legende td{padding:.55rem .4rem;border-bottom:1px solid var(--linie);vertical-align:top;}
.legende td:first-child{width:2.4rem;font-size:1.15rem;text-align:center;}
.m-roh{color:var(--leise);} .m-best{color:var(--marke);} .m-bearb{color:var(--warm);}
/* zwei Sichten */
.zwei{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem;margin:1.2rem 0;}
.zwei .karte{background:#fff;border:1px solid var(--linie);border-radius:12px;padding:1.1rem 1.2rem;}
.zwei h4{margin:.1rem 0 .3rem;font-family:var(--font-display);font-weight:500;font-size:1.1rem;}
.pill{display:inline-block;font-size:.72rem;letter-spacing:.05em;text-transform:uppercase;
  color:var(--marke);border:1px solid var(--marke);border-radius:999px;padding:.05rem .5rem;
  margin:.15rem .2rem 0 0;}
/* Inhaltsverzeichnis */
.toc{background:#fff;border:1px solid var(--linie);border-radius:12px;padding:1.1rem 1.4rem;margin:0 0 2rem;}
.toc h2{border:none;padding:0;margin:0 0 .5rem;font-size:1.15rem;}
.toc ol{margin:0;padding-left:1.3rem;columns:2;column-gap:2rem;}
.toc a{text-decoration:none;}
.foot{margin-top:4rem;padding-top:1.4rem;border-top:1px solid var(--linie);
  color:var(--leise);font-size:.85rem;text-align:center;}
@media(max-width:620px){.zwei,.toc ol{grid-template-columns:1fr;columns:1;}
  .hero h1{font-size:2.3rem;}}
@media(prefers-color-scheme:dark){
  :root{--papier:#22232B;--tinte:#EDEAE3;--leise:#9aa0a8;--linie:#34363f;}
  body{background:var(--papier);color:var(--tinte);}
  .callout,.zwei .karte,.toc{background:#2a2c35;}
  code{background:#34363f;}
}
</style></head><body><div class="wrap">

<div class="hero">
  <div class="mark">%%MARK%%</div>
  <div class="eb">Benutzerhandbuch</div>
  <h1>kennora</h1>
  <p class="sub">Wissen entsteht im Gespräch.</p>
</div>

<nav class="toc">
  <h2>Inhalt</h2>
  <ol>
    <li><a href="#was">Was ist kennora?</a></li>
    <li><a href="#kurz">In drei Sätzen</a></li>
    <li><a href="#start">Die Startseite</a></li>
    <li><a href="#sitzung">Eine Sitzung: reden oder tippen</a></li>
    <li><a href="#mikrofon">Das Mikrofon (Diktat)</a></li>
    <li><a href="#ordnen">Wie kennora dein Wissen ordnet</a></li>
    <li><a href="#antwort">kennora antwortet dir</a></li>
    <li><a href="#kuratieren">Dein Wissen kuratieren</a></li>
    <li><a href="#sprachen">In jeder Sprache</a></li>
    <li><a href="#reset">Testdaten zurücksetzen</a></li>
    <li><a href="#tipps">Tipps</a></li>
  </ol>
</nav>

<h2 id="was"><span class="n">01</span>Was ist kennora?</h2>
<p class="lead">kennora ist ein Zuhörer. Du erzählst frei, was du weisst – kennora
strukturiert das Gesagte sauber, aber menschlich, legt es ab und baut über viele
Sitzungen hinweg darauf auf.</p>
<p>Aus dem, was du sagst, entsteht nach und nach ein <strong>Wissensgraph</strong>:
deine Gedanken als Knoten, ihre Zusammenhänge als Verbindungen. Du siehst ihn auf
zwei Arten – als aufgeräumten <strong>Baum</strong> (wie ein Inhaltsverzeichnis)
und als assoziatives <strong>Netz</strong> (wo Dinge über Themen hinweg
zusammenklingen).</p>
<div class="callout"><span class="tag">Grundhaltung</span>
<p style="margin:.4rem 0 0"><strong>Der Mensch führt, nicht die KI.</strong> kennora
hört zu, ordnet im Hintergrund und hält sich mit Fragen stark zurück. Es lenkt dich
nicht – du erzählst, kennora bewahrt.</p></div>

<h2 id="kurz"><span class="n">02</span>In drei Sätzen</h2>
<ul>
  <li><strong>Reden oder tippen</strong> – in jeder Sprache, auch Schweizerdeutsch,
  auch gemischt. Kein Formular.</li>
  <li>kennora macht daraus <strong>Aussagen</strong>, erkennt den <strong>Grundsatz</strong>
  dahinter und ordnet alles in einen wachsenden Baum.</li>
  <li>Du <strong>bestätigst, überarbeitest oder löschst</strong> – dein Wissen bleibt
  deins.</li>
</ul>

<h2 id="start"><span class="n">03</span>Die Startseite</h2>
<p>Die Startseite ist bewusst leer und ruhig. Ein Klick auf <strong>Sprechen</strong>
bringt dich in eine Sitzung.</p>
<figure><img src="%%IMG_START%%" alt="kennora Startseite">
<figcaption>Die Startseite – das Zeichen, der Name, und der Weg hinein.</figcaption></figure>

<h2 id="sitzung"><span class="n">04</span>Eine Sitzung: reden oder tippen</h2>
<p>Hier passiert alles. Oben stellt kennora eine offene Einladung
(„Erzähl mir, woran du gerade arbeitest."). Du kannst <strong>ins Textfeld tippen</strong>
oder auf <strong>🎤 Sprechen</strong> gehen. Mit <strong>Ablegen</strong> übergibst du
den Beitrag – kennora ordnet ihn ein und der Baum darunter wächst.</p>
<figure><img src="%%IMG_SITZUNG%%" alt="Die Sitzungsseite von kennora">
<figcaption>Die Sitzung: oben sprechen/schreiben, unten dein Wissen als Baum und die
Verbindungen im Netz.</figcaption></figure>
<p>Wichtig: Du musst nichts in einem Zug fertig erzählen und nichts vollständig
sagen. Wissen darf wachsen – beim nächsten Mal knüpft kennora an das Gesagte an.</p>

<h2 id="mikrofon"><span class="n">05</span>Das Mikrofon (Diktat)</h2>
<p>Klick auf <strong>🎤 Sprechen</strong> und rede einfach los. Über das kleine
Auswahlfeld daneben wählst du dein <strong>Mikrofon</strong> – aufgenommen wird nur
dieses, nie das System- oder Meetingaudio. Der erkannte Text erscheint im Feld;
du liest gegen und legst selbst ab. So bleibst du in der Schleife.</p>
<ul>
  <li><strong>Jede Sprache:</strong> kennora erkennt die gesprochene Sprache
  automatisch – auch Schweizerdeutsch.</li>
  <li><strong>Sichere Verbindung nötig:</strong> Browser geben das Mikrofon nur über
  <code>https://</code> frei. Auf einer unsicheren (<code>http</code>) Adresse ist der
  Knopf deaktiviert und kennora sagt es dir.</li>
</ul>

<h2 id="ordnen"><span class="n">06</span>Wie kennora dein Wissen ordnet</h2>
<p>Jeder Gedanke wird zu einer <strong>Aussage</strong>. Eine Aussage hat mehrere
Ebenen:</p>
<ul>
  <li><strong>Kernsatz</strong> – sauber formuliert, in <em>deiner</em> Sprache.</li>
  <li><strong>Originalton</strong> – deine wörtlichen Worte, bleiben erhalten (deine
  Stimme geht nicht verloren).</li>
  <li><strong>Grundsatz</strong> – das Prinzip dahinter (z. B. <em>„Sorgfalt vor
  Tempo."</em>). Er wird in <span class="m-bearb">Warmton</span> angezeigt.</li>
</ul>

<h3>Reifegrad – wie sicher ist eine Aussage?</h3>
<p>Vor jeder Aussage steht ein kleines Zeichen. Es zeigt, wie „fest" der Gedanke ist:</p>
<table class="legende">
  <tr><td class="m-roh">○</td><td><strong>hingeworfen</strong> – frisch von kennora
  erfasst, noch nicht von dir geprüft (leicht abgeblendet).</td></tr>
  <tr><td class="m-best">✓</td><td><strong>bestätigt</strong> – du hast genickt, der
  Gedanke stimmt so.</td></tr>
  <tr><td class="m-bearb">✎</td><td><strong>überarbeitet</strong> – du hast ihn selbst
  richtiggestellt; deine Fassung gilt.</td></tr>
</table>

<h3>Zwei Sichten auf dasselbe Wissen</h3>
<div class="zwei">
  <div class="karte"><h4>🌳 Baum</h4>
  <p>Ein aufgeräumtes Gerüst aus Themen (z. B. <em>Schreinerei</em>, <em>Weitergabe</em>),
  darunter deine konkreten Aussagen. Übergabetauglich, wie ein Inhaltsverzeichnis.</p></div>
  <div class="karte"><h4>🕸️ Netz</h4>
  <p>Die nicht-hierarchischen Verbindungen quer über die Themen. Hier zeigt kennora,
  was zusammenklingt – auch über Sprachgrenzen hinweg.</p></div>
</div>
<p>Verbindungstypen, die im Netz auftauchen:</p>
<p><span class="pill">gehört-zu</span><span class="pill">führt-zu</span>
<span class="pill">widerspricht</span><span class="pill">reimt-sich-auf</span>
<span class="pill">unterscheidet-sich-durch</span></p>
<p><em>reimt-sich-auf</em> ist die seltene, überraschende Verbindung – zwei Gedanken,
die dasselbe Prinzip teilen, obwohl sie aus ganz verschiedenen Ecken kommen. Genau
diese Funken sind der Kern von kennora.</p>

<h2 id="antwort"><span class="n">07</span>kennora antwortet dir</h2>
<p>Nach jedem Ablegen spiegelt kennora kurz und warm zurück, was angekommen ist und
wo etwas gewachsen ist:</p>
<div class="rueck"><span class="tag">Beispiel einer Rückgabe</span>
<p style="margin:.4rem 0 0">Angekommen ist deine Sorgfalt im Handwerk – und dass sie
für dich mit dem Weitergeben zusammenhängt. Dein Bereich <em>Schreinerei</em> nimmt
Form an.</p></div>
<p><strong>Und die Fragen?</strong> kennora fragt <strong>selten</strong> – nie nach
jedem Beitrag. Nur wenn eine echte Lücke offen bleibt, kommt höchstens eine
zurückhaltende Frage. Das ist Absicht: Du führst das Gespräch, nicht kennora.</p>

<h2 id="kuratieren"><span class="n">08</span>Dein Wissen kuratieren</h2>
<p>Neben jeder Aussage im Baum findest du drei Aktionen:</p>
<ul>
  <li><strong>✓ Bestätigen</strong> – dein Nicken. Die Aussage wird <em>bestätigt</em>.</li>
  <li><strong>✎ Überarbeiten</strong> – öffnet eine Seite, auf der du Kernsatz und
  Grundsatz korrigierst. Dein <em>Originalton bleibt erhalten</em>, und deine Fassung
  wird die massgebliche.</li>
  <li><strong>🗑 Löschen</strong> – entfernt die Aussage (mit Rückfrage).</li>
</ul>
<figure><img src="%%IMG_BEARBEITEN%%" alt="Eine Aussage überarbeiten">
<figcaption>Überarbeiten: du stellst richtig, was kennora falsch verstanden hat –
der Originalton bleibt als Referenz sichtbar.</figcaption></figure>
<div class="callout"><p style="margin:0">Gerade das Überarbeiten ist wichtig: kennora
kann eine Nuance verdrehen (etwa Ursache und Wirkung). Beim Gegenlesen fängst du das –
und deine Korrektur zählt.</p></div>

<h2 id="sprachen"><span class="n">09</span>In jeder Sprache</h2>
<p>Rede, wie dir der Schnabel gewachsen ist – Hochdeutsch, Schweizerdeutsch,
Französisch, Englisch, auch gemischt. kennora antwortet in <em>deiner</em> Sprache und
formuliert den Kernsatz in derselben Sprache, in der du gesprochen hast.</p>
<p>Das Besondere: Verbindungen entstehen <strong>über Sprachgrenzen hinweg</strong> –
ein französischer Gedanke kann sich auf einen deutschen „reimen", weil beide dasselbe
Prinzip teilen. Bei Deutsch schreibt kennora immer in <strong>Schweizer
Rechtschreibung</strong> („ss" statt „ß").</p>

<h2 id="reset"><span class="n">10</span>Testdaten zurücksetzen</h2>
<p>Zum Ausprobieren gibt es auf der Entwicklungs-Umgebung den roten Knopf
<strong>„Testdaten zurücksetzen"</strong>. Er löscht alle Aussagen und gibt dir ein
sauberes Blatt. Diese Funktion existiert bewusst <em>nur auf dev</em> – in der
richtigen Nutzung ist sie nicht vorhanden.</p>

<h2 id="tipps"><span class="n">11</span>Tipps</h2>
<ul>
  <li><strong>Einfach erzählen.</strong> Nicht auf Vollständigkeit oder schöne Sätze
  achten – kennora glättet für dich.</li>
  <li><strong>Wachsen lassen.</strong> Mehrere kurze Sitzungen sind besser als eine
  perfekte. kennora knüpft immer an.</li>
  <li><strong>Gegenlesen.</strong> Überflieg die Rückgabe und den Baum; wo etwas nicht
  stimmt, ein Klick auf ✎ und richtigstellen.</li>
  <li><strong>Grundsätze pflegen.</strong> Die Prinzipien (Warmton) sind das Herz –
  je klarer sie sind, desto bessere Verbindungen findet kennora.</li>
</ul>

<div class="foot">
  <p>kennora — Wissen entsteht im Gespräch.</p>
</div>

</div></body></html>"""


def main():
    html = (HTML
            .replace("%%FONTS%%", FONTS)
            .replace("%%MARK%%", MARK)
            .replace("%%IMG_START%%", bild("startseite.png"))
            .replace("%%IMG_SITZUNG%%", bild("sitzung.png"))
            .replace("%%IMG_BEARBEITEN%%", bild("bearbeiten.png")))
    ziel = os.path.join(ROOT, "docs", "handbuch.html")
    with open(ziel, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Handbuch geschrieben: {os.path.normpath(ziel)} ({len(html)//1024} KB)")


if __name__ == "__main__":
    main()
