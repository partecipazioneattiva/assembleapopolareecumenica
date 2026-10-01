#!/usr/bin/env python3
"""Costruisce il sito assembleapopolareecumenica.it DALLE pagine APE del sito di
Partecipazione Attiva (30/09/2026).

Una sola fonte dei testi: `ape.html` e `rete-ape.html` nel repository di PA. Qui si
prende il loro contenuto (tutto cio' che sta dentro <main>), gli si mette intorno
l'intestazione e il pie' di pagina dell'APE, e si riscrivono i collegamenti:
  - le pagine APE puntano fra loro (index.html, rete.html);
  - le altre pagine del movimento diventano indirizzi interi di partecipazione-attiva.it;
  - immagini, documenti, fogli di stile e caratteri si COPIANO qui.
Quando cambia una pagina APE sul sito di PA, si rilancia questo e si pubblica.

    python3 _tools/costruisci.py             # rigenera tutto (sito visibile su github.io)
    python3 _tools/costruisci.py --dominio   # idem + file CNAME: SOLO quando i DNS di Aruba puntano a GitHub
"""
import html
import os
import re
import shutil
import sys
import datetime

QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
PA = os.path.dirname(QUI.rstrip('/')) + '/partecipazioneattiva/'
SITO = 'https://www.assembleapopolareecumenica.it/'
SITO_PA = 'https://partecipazione-attiva.it/'

PAGINE = {
    # uscita: (sorgente in PA, titolo, immagine di anteprima — fatta da _tools/immagini.py)
    'index.html': ('ape.html', 'APE — Assemblea Popolare Ecumenica', 'images/ape-anteprima.jpg'),
    'rete.html': ('rete-ape.html', 'Rete APE — aderisci | Assemblea Popolare Ecumenica',
                  'images/rete-ape-anteprima.jpg'),
}
DESCRIZIONI = {'index.html': 'APE, Assemblea Popolare Ecumenica: un&#x27;assemblea permanente di cittadini sorteggiati che obbliga le istituzioni a rispondere. Un progetto aperto a tutti.'}
VOLTO = 'images/angelo-nicotra-volto.webp'

# Fernando, 01/10/2026: «anche sul sito APE va scritto almeno il perche' della sua nascita».
# Testo SOLO del sito APE (non esiste su PA), in voce neutra: non il «noi» del movimento.
PERCHE_SITO = (
    '<div class="pa-box" id="perche"><h3>Perch&eacute; questo sito</h3>'
    '<p><strong>&laquo;Ecumenica&raquo; vuol dire aperta a tutti, senza distinzioni.</strong> '
    'L&rsquo;APE non &egrave; un partito e non appartiene a nessuno: chiede a ogni cittadino di '
    'partecipare con lo stesso peso degli altri. Per questo ha una casa sua, neutra, senza simboli '
    'n&eacute; bandiere: <strong>un&rsquo;unione d&rsquo;intenti, non di simboli o ideologie</strong>.</p>'
    '<p>Qui chiunque &mdash; un cittadino, un comitato, un&rsquo;associazione, un movimento o un '
    'partito &mdash; pu&ograve; conoscere la proposta e <a href="rete.html">aderire alla Rete APE</a> '
    'alla pari. L&rsquo;ha ideata Angelo Nicotra; Partecipazione Attiva l&rsquo;ha fatta propria ed '
    '&egrave; tra i promotori della Rete.</p></div>\n')     # solo il viso: i ritratti di PA sono manifesti col marchio

# Fernando, 30/09/2026: «non è che PA non si può nominare» — PA si nomina (chi ha elaborato, chi
# propone, chi aderisce); quello che NON deve passare e' la proprieta' ESCLUSIVA. Dove la pagina di PA
# dice «di Partecipazione Attiva» NELLA CORNICE (titolo, qualifica, etichette), qui si riscrive.
# (vecchio, nuovo, quante volte deve comparire). Se il sorgente cambia, lo script si ferma.
RISCRITTURE = {
    'index.html': [
        ('La proposta di Partecipazione Attiva per un canale permanente di voce dei cittadini, oltre la democrazia delegativa.',
         'Un canale permanente di voce dei cittadini, oltre la democrazia delegativa. Aperto a tutti.', 1),
        ('<div class="ruolo">Presidente &mdash; Partecipazione Attiva</div>', '<div class="ruolo">Ideatore del Progetto APE &middot; Presidente di Partecipazione Attiva</div>', 1),
        ('<span class="badge-pa">Partecipazione Attiva</span>', '', 1),
        ('<p class="pa-lead">Con APE (Assemblea Popolare Ecumenica), Partecipazione Attiva lancia una nuova idea di Democrazia Partecipativa per rendere i cittadini parte attiva nella gestione politica del nostro Paese.</p>',
         '<p class="pa-lead">APE (Assemblea Popolare Ecumenica) è una nuova idea di Democrazia Partecipativa per rendere i cittadini parte attiva nella gestione politica del nostro Paese.</p>', 1),
        ('<p>È la proposta di legge più importante del movimento: una riforma costituzionale che non aggiunge un partito né un candidato, ma uno strumento permanente attraverso cui ogni cittadino può obbligare le istituzioni ad ascoltare e a rispondere. Elaborata da Angelo Nicotra, Presidente di Partecipazione Attiva, ed è oggi proposta ufficiale del movimento.</p>',
         '<p>È una riforma costituzionale che non aggiunge un partito né un candidato, ma uno strumento permanente attraverso cui ogni cittadino può obbligare le istituzioni ad ascoltare e a rispondere. L’ha elaborata Angelo Nicotra, Presidente di Partecipazione Attiva: il movimento l’ha fatta propria e la propone a tutti, senza esclusive.</p>', 1),
        ('alt="Angelo Nicotra Presidente Partecipazione Attiva" width="500" height="750"', 'alt="Angelo Nicotra" width="300" height="300"', 1),
        ('images/organigramma/angelo-nicotra-finale.webp', VOLTO, 1),
    ],
    'rete.html': [
        ('<span class="article-date">Presidente di Partecipazione Attiva</span>', '<span class="article-date">Ideatore del Progetto APE &middot; Presidente di Partecipazione Attiva</span>', 1),
        ('object-position:top center" width="1024" height="1536"', 'object-position:center" width="300" height="300"', 1),
        ('Leggi%20questo%20articolo%20di%20Partecipazione%20Attiva%3A%20', 'Rete%20APE%2C%20Assemblea%20Popolare%20Ecumenica%3A%20', None),
    ],
}
# pagine APE: come si chiamano qui
INTERNE = {'ape.html': './', 'rete-ape.html': 'rete.html'}
COPIA_FISSA = ['fonts', 'LOGO-PA.webp']
FOGLI = {'css/pa-leggibilita.css': 'css/ape-leggibilita.css', 'css/pa-base.css': 'css/ape-base.css'}

ICONA = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
         "%3Ctext y='.9em' font-size='90'%3E%F0%9F%90%9D%3C/text%3E%3C/svg%3E")

STILE = """
.ape-testa{background:#fff;border-bottom:3px solid #e8900a;position:sticky;top:0;z-index:50}
.ape-testa-in{max-width:1100px;margin:0 auto;padding:10px 16px;display:flex;flex-wrap:wrap;
  align-items:center;justify-content:space-between;gap:8px 18px}
.ape-marchio{display:flex;align-items:center;gap:10px;text-decoration:none;color:#3a2000}
.ape-marchio .ape-ape{font-size:2em;line-height:1}
.ape-marchio b{display:block;font-family:Montserrat,system-ui,sans-serif;font-weight:900;
  font-size:1.25em;letter-spacing:1px;color:#8a4e00}
.ape-marchio span span{display:block;font-family:Montserrat,system-ui,sans-serif;font-size:.72em;
  font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#5a4a3a}
.ape-voci{display:flex;flex-wrap:wrap;gap:6px 8px;font-family:Montserrat,system-ui,sans-serif}
.ape-voci a{text-decoration:none;color:#3a2000;font-weight:700;font-size:1em;padding:9px 14px;
  border-radius:50px;min-height:44px;display:inline-flex;align-items:center}
.ape-voci a:hover,.ape-voci a:focus{background:#fff1dc}
.ape-voci a[aria-current=page]{background:#8a4e00;color:#fff}
.ape-voci a.ape-fuori{border:2px solid #e8900a}
/* i pulsanti di PA hanno testo scuro su arancio: sul blu serve il bianco (pa11y: 4,39 -> a norma) */
main a.btn,main a.btn:visited,main a[href^="mailto:"][style*="background"]{background:#17507a!important;color:#fff!important}
.ape-salta{position:absolute;left:-9999px}
.ape-salta:focus{left:8px;top:8px;background:#fff;padding:10px 14px;z-index:99;border:2px solid #8a4e00}
.ape-piede{background:#3a2000;color:#fff;padding:34px 18px;text-align:center;
  font-family:Montserrat,system-ui,sans-serif;font-size:1em;line-height:1.7}
.ape-piede a{color:#ffd580;font-weight:700}
.ape-piede p{max-width:760px;margin:0 auto 10px}
.ape-piede .ape-piccolo{font-size:.9em;color:#f3e6d3}
@media(max-width:700px){.ape-testa{position:static}.ape-voci a{padding:8px 11px;font-size:.95em}}
"""


import colorsys

TINTA = 207 / 360          # blu inchiostro: l'APE non porta i colori di nessuno dei promotori


def neutro(testo):
    """Ruota verso il blu ogni colore «caldo» (arancio/bruno/crema di Partecipazione Attiva).
    Stessa luminosita', saturazione un po' piu' bassa: i contrasti restano quelli misurati."""
    def uno(m):
        x = m.group(1)
        if len(x) == 3:
            x = ''.join(c * 2 for c in x)
        r, g, b = (int(x[i:i + 2], 16) / 255 for i in (0, 2, 4))
        h, l, sat = colorsys.rgb_to_hls(r, g, b)
        if not (15 / 360 <= h <= 52 / 360 and sat > 0.2):
            return m.group(0)
        r, g, b = colorsys.hls_to_rgb(TINTA, l, sat * 0.72)
        return '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))
    testo = testo.replace('rgba(232,144,10,', 'rgba(42,111,152,')      # l'ombra arancio dei pulsanti
    return re.sub(r'(?<![&\w])#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-fA-F])', uno, testo)


def stop(m):
    print('⛔', m)
    sys.exit(1)


def copia(rel):
    """Copia un file (o una cartella) da PA a qui, stesso percorso."""
    da, a = PA + rel, QUI + rel
    if not os.path.exists(da):
        stop(f'manca nel sito di PA: {rel}')
    os.makedirs(os.path.dirname(a) or QUI, exist_ok=True)
    if os.path.isdir(da):
        shutil.copytree(da, a, dirs_exist_ok=True)
    else:
        shutil.copy2(da, a)


def riscrivi_link(pezzo, uscita, copiati):
    def uno(m):
        attr, q, url = m.group(1), m.group(2), m.group(3)
        u = html.unescape(url)
        if u.startswith(('http://', 'https://', 'mailto:', 'tel:', '#', 'data:')):
            return m.group(0)
        base, _, coda = u.partition('#')
        coda = '#' + coda if coda else ''
        if base in INTERNE:
            nuovo = INTERNE[base] + coda
        elif base.endswith('.html'):
            nuovo = SITO_PA + ('' if base == 'index.html' else base) + coda
        elif base.startswith('video/'):
            nuovo = SITO_PA + base            # i filmati restano dove sono: pesano
        elif os.path.exists(QUI + base) and not os.path.exists(PA + base):
            nuovo = base + coda               # immagine propria del sito APE (_tools/immagini.py)
        else:
            copia(base)
            copiati.add(base)
            nuovo = base + coda
        return f'{attr}={q}{nuovo}{q}'
    return re.sub(r'\b(href|src|poster)=(["\'])([^"\']+)\2', uno, pezzo)


def testa(uscita, attuale):
    voci = [('./', 'Il progetto', 'index.html'), ('rete.html', 'Rete APE', 'rete.html'),
            ('./#documenti', 'Documenti', None)]
    h = ''.join(f'<a href="{u}"{" aria-current=page" if attuale == f else ""}>{t}</a>'
                for u, t, f in voci)
    return ('<a class="ape-salta" href="#contenuto">Salta al contenuto</a>'
            '<header class="ape-testa"><div class="ape-testa-in">'
            '<a class="ape-marchio" href="./" aria-label="APE, Assemblea Popolare Ecumenica: pagina iniziale">'
            '<span class="ape-ape" aria-hidden="true">&#x1F41D;</span>'
            '<span><b>APE</b><span>Assemblea Popolare Ecumenica</span></span></a>'
            f'<nav class="ape-voci" aria-label="Menu principale">{h}</nav></div></header>')


PIEDE = (f'<footer class="ape-piede"><p><strong>APE &mdash; Assemblea Popolare Ecumenica</strong><br>'
         f'Un progetto aperto a tutti: cittadini, associazioni, movimenti, comitati, con peso paritario.</p>'
         f'<p>Ideato da Angelo Nicotra. Tra i promotori della <a href="rete.html">Rete APE</a>: '
         f'<a href="{SITO_PA}" rel="noopener">Partecipazione Attiva</a>.</p>'
         f'<p class="ape-piccolo"><a href="mailto:info@assembleapopolareecumenica.it">info@assembleapopolareecumenica.it</a>'
         f' &middot; <a href="{SITO_PA}privacy.html">Privacy</a> &middot; Questo sito non usa cookie di profilazione '
         f'n&eacute; tracciatori.</p><p class="ape-piccolo">&copy; {datetime.date.today().year}</p></footer>')


def pagina(uscita, sorgente, titolo, anteprima, copiati):
    h = open(PA + sorgente, encoding='utf-8').read()
    i, j = h.find('<main'), h.find('</main>')
    if i < 0 or j < 0:
        stop(f'{sorgente}: non trovo <main>')
    corpo = h[h.find('>', i) + 1:j]
    # via le briciole di pane del sito di PA
    corpo = re.sub(r'<nav[^>]*class="breadcrumb".*?</nav>', '', corpo, count=1, flags=re.S)
    # i pulsanti «condividi» puntano a QUESTA pagina (in rete-ape.html erano rimasti su un'altra)
    mia = SITO + ('' if uscita == 'index.html' else uscita)
    corpo = re.sub(r'(facebook\.com/sharer/sharer\.php\?u=)https://partecipazione-attiva\.it/[^"\'&\s]+',
                   lambda m: m.group(1) + mia, corpo)
    corpo = re.sub(r'(wa\.me/\?text=[^"\']*?)https://partecipazione-attiva\.it/[^"\'&\s]+',
                   lambda m: m.group(1) + mia, corpo)
    if uscita == 'rete.html':
        # dopo l'articolo la pagina di PA ha «Leggi anche» e «Unisciti a Partecipazione Attiva»: qui no
        k = corpo.rfind('</article>')
        if k < 0:
            stop('rete: non trovo la fine dell articolo')
        corpo = corpo[:k + len('</article>')]
    if uscita == 'index.html':
        aggancio = '<p class="pa-lead">Con APE (Assemblea Popolare Ecumenica), Partecipazione Attiva lancia'
        if corpo.count(aggancio) != 1:
            stop('index: non trovo dove mettere «Perche questo sito»')
        corpo = corpo.replace(aggancio, PERCHE_SITO + aggancio, 1)
    for vecchio, nuovo, quante in RISCRITTURE.get(uscita, []):
        c = corpo.count(vecchio)
        if (quante is not None and c != quante):
            stop(f'{uscita}: «{vecchio[:50]}…» compare {c} volte, ne aspettavo {quante}')
        corpo = corpo.replace(vecchio, nuovo)
    if uscita == 'rete.html':
        # il ritratto di PA e' un manifesto col marchio: in testa va il solo viso, nel testo si toglie
        tag = re.findall(r'<img[^>]*angelo-nicotra-rete-ape\.webp[^>]*>', corpo)
        if len(tag) != 2:
            stop(f'rete: aspettavo 2 ritratti di Nicotra, ne trovo {len(tag)}')
        corpo = corpo.replace(tag[0], tag[0].replace('images/angelo-nicotra-rete-ape.webp', VOLTO), 1)
        corpo = corpo.replace(tag[1], '', 1)
    corpo = neutro(riscrivi_link(corpo, uscita, copiati))
    if uscita == 'index.html':
        # ancora per la voce «Documenti»: il primo riquadro di scarico
        if corpo.count('<div class="pa-dl">') < 1:
            stop('index: non trovo il riquadro dei documenti (.pa-dl)')
        corpo = corpo.replace('<div class="pa-dl">', '<div class="pa-dl" id="documenti">', 1)
    stili = ''.join(re.findall(r'<style>.*?</style>', h[:i], flags=re.S))
    m = re.search(r'name="?description"? content="([^"]*)"', h)
    if not m:
        stop(f'{sorgente}: manca la description')
    desc = DESCRIZIONI.get(uscita, m.group(1))
    if not os.path.exists(QUI + anteprima):
        stop(f'manca {anteprima}: lancia prima  python3 _tools/immagini.py')
    ld = ('{"@context":"https://schema.org","@type":"WebPage","name":%s,"url":"%s",'
          '"description":%s,"inLanguage":"it","isPartOf":{"@type":"WebSite","name":'
          '"APE — Assemblea Popolare Ecumenica","url":"%s"},"author":{"@type":"Person","name":"Angelo Nicotra"}}'
          % (json_s(titolo), mia, json_s(html.unescape(desc)), SITO))
    doc = f'''<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{titolo}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{mia}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="APE — Assemblea Popolare Ecumenica">
<meta property="og:title" content="{titolo}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{mia}">
<meta property="og:image" content="{SITO}{anteprima}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{titolo}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{SITO}{anteprima}">
<link rel="icon" href="{ICONA}">
<link href="fonts/caratteri.css" rel="stylesheet">
<link rel="stylesheet" href="css/ape-leggibilita.css">
<link rel="stylesheet" href="css/ape-base.css">
<style>{neutro(STILE)}</style>
{neutro(stili)}
<script type="application/ld+json">{ld}</script>
</head>
<body>
{testa(uscita, uscita)}
<main id="contenuto">
{corpo}
</main>
{PIEDE}
</body>
</html>
'''
    open(QUI + uscita, 'w', encoding='utf-8').write(doc)
    print(f'  {uscita:12} da {sorgente:14} {len(doc) // 1024} KB')


def json_s(s):
    import json
    return json.dumps(s, ensure_ascii=False)


def main():
    if not os.path.isdir(PA):
        stop('non trovo il repository di Partecipazione Attiva accanto a questo')
    copiati = set()
    for rel in COPIA_FISSA:
        copia(rel)
    os.makedirs(QUI + 'css', exist_ok=True)
    for da, a in FOGLI.items():
        open(QUI + a, 'w', encoding='utf-8').write(neutro(open(PA + da, encoding='utf-8').read()))
    for uscita, (sorgente, titolo, anteprima) in PAGINE.items():
        pagina(uscita, sorgente, titolo, anteprima, copiati)
    oggi = datetime.date.today().isoformat()
    voci = ''.join(f'<url><loc>{SITO}{"" if p == "index.html" else p}</loc><lastmod>{oggi}</lastmod></url>\n'
                   for p in PAGINE)
    open(QUI + 'sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + voci + '</urlset>\n')
    open(QUI + 'robots.txt', 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITO}sitemap.xml\n')
    # Il file CNAME dice a GitHub Pages di servire il sito sul dominio. Finche' i DNS di Aruba non
    # puntano a GitHub, con il CNAME il sito sarebbe IRRAGGIUNGIBILE: si scrive solo con --dominio.
    if '--dominio' in sys.argv:
        open(QUI + 'CNAME', 'w').write('www.assembleapopolareecumenica.it\n')
    elif os.path.exists(QUI + 'CNAME'):
        os.remove(QUI + 'CNAME')
    open(QUI + '.nojekyll', 'w').write('')
    open(QUI + '404.html', 'w', encoding='utf-8').write(
        '<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" '
        'content="width=device-width, initial-scale=1.0"><title>Pagina non trovata | APE</title>'
        '<meta name="robots" content="noindex"></head><body style="font-family:system-ui;text-align:center;'
        'padding:60px 20px;font-size:1.2em"><h1>Pagina non trovata</h1><p><a href="/">Torna al Progetto APE</a>'
        '</p></body></html>')
    print(f'copiati {len(copiati)} file collegati: {sorted(copiati)}')


if __name__ == '__main__':
    main()
