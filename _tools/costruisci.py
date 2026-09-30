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

    python3 _tools/costruisci.py          # rigenera tutto nella cartella del sito
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
    # uscita: (sorgente in PA, titolo, immagine di anteprima in PA)
    'index.html': ('ape.html', 'APE — Assemblea Popolare Ecumenica', 'images/ape-og.jpg'),
    'rete.html': ('rete-ape.html', 'Rete APE — aderisci | Assemblea Popolare Ecumenica',
                  'images/anteprime/rete-ape-anteprima.jpg'),
}
# pagine APE: come si chiamano qui
INTERNE = {'ape.html': './', 'rete-ape.html': 'rete.html'}
COPIA_FISSA = ['css/pa-base.css', 'css/pa-leggibilita.css', 'fonts', 'LOGO-PA.webp']

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
.ape-salta{position:absolute;left:-9999px}
.ape-salta:focus{left:8px;top:8px;background:#fff;padding:10px 14px;z-index:99;border:2px solid #8a4e00}
.ape-piede{background:#3a2000;color:#fff;padding:34px 18px;text-align:center;
  font-family:Montserrat,system-ui,sans-serif;font-size:1em;line-height:1.7}
.ape-piede a{color:#ffd580;font-weight:700}
.ape-piede p{max-width:760px;margin:0 auto 10px}
.ape-piede .ape-piccolo{font-size:.9em;color:#f3e6d3}
@media(max-width:700px){.ape-testa{position:static}.ape-voci a{padding:8px 11px;font-size:.95em}}
"""


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
    h += f'<a class="ape-fuori" href="{SITO_PA}" rel="noopener">Partecipazione Attiva &#8599;</a>'
    return ('<a class="ape-salta" href="#contenuto">Salta al contenuto</a>'
            '<header class="ape-testa"><div class="ape-testa-in">'
            '<a class="ape-marchio" href="./" aria-label="APE, Assemblea Popolare Ecumenica: pagina iniziale">'
            '<span class="ape-ape" aria-hidden="true">&#x1F41D;</span>'
            '<span><b>APE</b><span>Assemblea Popolare Ecumenica</span></span></a>'
            f'<nav class="ape-voci" aria-label="Menu principale">{h}</nav></div></header>')


PIEDE = (f'<footer class="ape-piede"><p><strong>APE &mdash; Assemblea Popolare Ecumenica</strong><br>'
         f'Progetto ideato da Angelo Nicotra.</p>'
         f'<p>Sito promosso e curato da <a href="{SITO_PA}">Partecipazione Attiva</a>, '
         f'movimento popolare dei cittadini italiani.</p>'
         f'<p class="ape-piccolo"><a href="mailto:partecipazioneattiva21@gmail.com">partecipazioneattiva21@gmail.com</a>'
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
    corpo = riscrivi_link(corpo, uscita, copiati)
    if uscita == 'index.html':
        # ancora per la voce «Documenti»: il primo riquadro di scarico
        if corpo.count('<div class="pa-dl">') < 1:
            stop('index: non trovo il riquadro dei documenti (.pa-dl)')
        corpo = corpo.replace('<div class="pa-dl">', '<div class="pa-dl" id="documenti">', 1)
    stili = ''.join(re.findall(r'<style>.*?</style>', h[:i], flags=re.S))
    m = re.search(r'name="?description"? content="([^"]*)"', h)
    if not m:
        stop(f'{sorgente}: manca la description')
    desc = m.group(1)
    copia(anteprima)
    copiati.add(anteprima)
    ld = ('{"@context":"https://schema.org","@type":"WebPage","name":%s,"url":"%s",'
          '"description":%s,"inLanguage":"it","isPartOf":{"@type":"WebSite","name":'
          '"APE — Assemblea Popolare Ecumenica","url":"%s"},"author":{"@type":"Person","name":"Angelo Nicotra"},'
          '"publisher":{"@type":"Organization","name":"Partecipazione Attiva","url":"%s"}}'
          % (json_s(titolo), mia, json_s(html.unescape(desc)), SITO, SITO_PA))
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
<link rel="stylesheet" href="css/pa-leggibilita.css">
<link rel="stylesheet" href="css/pa-base.css">
<style>{STILE}</style>
{stili}
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
    for uscita, (sorgente, titolo, anteprima) in PAGINE.items():
        pagina(uscita, sorgente, titolo, anteprima, copiati)
    oggi = datetime.date.today().isoformat()
    voci = ''.join(f'<url><loc>{SITO}{"" if p == "index.html" else p}</loc><lastmod>{oggi}</lastmod></url>\n'
                   for p in PAGINE)
    open(QUI + 'sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + voci + '</urlset>\n')
    open(QUI + 'robots.txt', 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITO}sitemap.xml\n')
    open(QUI + 'CNAME', 'w').write('www.assembleapopolareecumenica.it\n')
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
