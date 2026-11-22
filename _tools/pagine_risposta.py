#!/usr/bin/env python3
"""Pagine-risposta del sito APE: UNA pagina HTML per ogni puntata pubblicata («APE spiegata a puntate»).
Testi SOLO dai file ape_spot_giornalieri/out/post/GNN_*.md (sezione «LinkedIn e altri»). Niente FAQPage
(Google ha ritirato i risultati FAQ il 07/05/2026): JSON-LD Article + VideoObject + BreadcrumbList.
Fa anche: elenco «Le risposte» in attualita.html (_contenuti e pagina costruita), blocco nella home,
voci in sitemap.xml, H1 con nome per esteso in home/progetto/patto. Idempotente. NON fa commit né push.
Uso:  python3 _tools/pagine_risposta.py            tutte le puntate pubblicate (video presente sul sito)
      python3 _tools/pagine_risposta.py 18 24 26   solo quelle (prove)
Chiamato da sito_spot.py (dopo ogni nuova puntata) e da costruisci.py (a fine build)."""
import datetime, glob, html, json, os, re, subprocess, sys

QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
POST = os.path.expanduser('~/Desktop/ARCHIVIO GENERALE/LAVORI/ape_spot_giornalieri/out/post/')
SITO = 'https://www.assembleapopolareecumenica.it/'
NOME = 'Assemblea Popolare Ecumenica'
MESI = {m: i for i, m in enumerate(['', 'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto',
                                    'settembre', 'ottobre', 'novembre', 'dicembre'])}
e = lambda t: html.escape(t, quote=True)
ej = lambda t: json.dumps(t, ensure_ascii=False).replace('</', '<\\/')


def leggi_puntata(path):
    s = open(path, encoding='utf-8').read()
    m = re.match(r'# Giorno (\d+) · (.+)', s)
    g, titolo = int(m.group(1)), m.group(2).strip()
    slug = re.match(r'G\d+_(.+)\.md', os.path.basename(path)).group(1)
    sez = re.search(r'## LinkedIn e altri[^\n]*\n(.*?)(?=\n## )', s, re.S).group(1).strip()
    par = []
    for p in re.split(r'\n\s*\n', sez):
        p = p.strip()
        if not p or p.startswith('APE spiegata a puntate') or p.startswith('Aderisci alla Rete APE'):
            if p.startswith('Aderisci alla Rete APE'):
                break          # da qui in poi sono i link dei social
            continue
        p = re.sub(r'Scrivila nei commenti, oppure scrivi', 'Scrivi', p)
        p = re.sub(r'Scrivilo nei commenti, oppure scrivi', 'Scrivi', p)
        if re.search(r'nei commenti', p):
            continue
        p = (p.replace('diventa co-fondatore ed entra nell\'Albo dei co-fondatori', 'diventa uno dei Costruttori del Progetto APE ed entra nell\'Albo dei Costruttori')
              .replace('co-fondatore della Rete APE', 'uno dei Costruttori del Progetto APE')
              .replace('co-fondatori', 'Costruttori del Progetto APE').replace('co-fondatore', 'uno dei Costruttori del Progetto APE'))
        par.append(p)
    assert par, f'G{g}: nessun testo estratto'
    return {'g': g, 'slug': slug, 'titolo': titolo, 'par': par}


def data_da_attualita(slug):
    a = open(QUI + 'attualita.html', encoding='utf-8').read()
    m = re.search(r'id="%s">\s*<p class="at-data">(\d+) (\w+) (\d{4})' % re.escape(slug), a)
    assert m, f'{slug}: data non trovata in attualita.html'
    return datetime.date(int(m.group(3)), MESI[m.group(2)], int(m.group(1))).isoformat()


def durata(mp4):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp4],
                         capture_output=True, text=True).stdout.strip()
    return f'PT{round(float(out))}S' if out else None


def pubblicate():
    P = []
    for f in sorted(glob.glob(POST + 'G[0-9][0-9]_*.md')):
        d = leggi_puntata(f)
        if os.path.exists(f'{QUI}video/ape-spot-{d["g"]:02d}-{d["slug"]}-h264.mp4'):
            P.append(d)
    return P


def linka(t):
    t = e(t)
    t = re.sub(r'([\w.]+@[\w.]+\.it)', r'<a href="mailto:\1">\1</a>', t)
    return t.replace('www.assembleapopolareecumenica.it', '<a href="./">www.assembleapopolareecumenica.it</a>')


def breve(t, n=155):
    if len(t) <= n:
        return t
    return t[:n].rsplit(' ', 1)[0].rstrip(',;:') + '…'


CSS = '''<style>
.rp-hero{background:linear-gradient(120deg,#0e2a40 0%,#17507a 100%);color:#fff;text-align:center;padding:34px 20px 30px}
.rp-hero p{margin:0 0 8px;font-family:Montserrat,system-ui,sans-serif;font-size:.9em;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:#cfe3f2}
.rp-hero h1{font-family:Merriweather,Georgia,serif;font-size:1.9em;line-height:1.3;margin:0 auto;max-width:760px;color:#fff}
.rp-wrap{max-width:760px;margin:0 auto;padding:30px 20px 10px;font-family:Merriweather,Georgia,serif;font-size:1.06em;line-height:1.8;color:#222}
.rp-wrap a{color:#17507a}
.rp-mig{font-family:Montserrat,system-ui,sans-serif;font-size:.88em;margin:0 0 16px}
.rp-data{font-family:Montserrat,system-ui,sans-serif;font-weight:700;color:#17507a;font-size:.92em;letter-spacing:.03em;text-transform:uppercase;margin:0 0 6px}
.rp-fonte{font-size:.86em;color:#4a5a66}
.rp-cta{display:block;max-width:440px;margin:22px auto;text-align:center;background:#17507a;color:#fff!important;font-family:Montserrat,system-ui,sans-serif;font-weight:800;padding:16px 22px;border-radius:14px;text-decoration:none}
.rp-box{background:#f2f7fb;border:2px solid #9cc3e0;border-radius:16px;padding:16px 22px;margin:26px 0;font-family:Montserrat,system-ui,sans-serif;font-size:.95em;line-height:1.6}
.rp-box p{margin:0 0 8px}.rp-box ul{margin:0;padding-left:20px}
.rp-pn{display:flex;flex-wrap:wrap;justify-content:space-between;gap:10px;margin:26px 0;font-family:Montserrat,system-ui,sans-serif;font-size:.92em}
</style>'''


def costruisci_pagina(d, tutte, cb):
    g, slug, titolo, par = d['g'], d['slug'], d['titolo'], d['par']
    N = f'ape-spot-{g:02d}-{slug}'
    url = f'{SITO}{slug}.html'
    data = data_da_attualita(slug)
    dur = durata(f'{QUI}video/{N}-h264.mp4')
    titolo_pag = f'{titolo} | {NOME}'
    desc = breve(' '.join(par[:2]))
    img = f'{SITO}images/{N}-copertina.webp'
    ind = next(i for i, x in enumerate(tutte) if x['g'] == g)
    prev_, next_ = (tutte[ind - 1] if ind else None), (tutte[ind + 1] if ind + 1 < len(tutte) else None)
    ld = json.dumps([
        {'@context': 'https://schema.org', '@type': 'Article', 'headline': titolo, 'description': desc, 'inLanguage': 'it',
         'datePublished': data, 'dateModified': datetime.date.today().isoformat(), 'mainEntityOfPage': url, 'image': [img],
         'author': {'@type': 'Organization', 'name': f'APE — {NOME}', 'url': SITO},
         'publisher': {'@type': 'Organization', 'name': f'APE — {NOME}', 'url': SITO},
         'isPartOf': {'@type': 'WebSite', 'name': f'APE — {NOME}', 'url': SITO}},
        dict({'@context': 'https://schema.org', '@type': 'VideoObject', 'name': titolo, 'description': desc, 'inLanguage': 'it',
              'thumbnailUrl': [img], 'uploadDate': data, 'contentUrl': f'{SITO}video/{N}-h264.mp4', 'url': url},
             **({'duration': dur} if dur else {})),
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'APE', 'item': SITO},
            {'@type': 'ListItem', 'position': 2, 'name': 'Attualità', 'item': f'{SITO}attualita.html'},
            {'@type': 'ListItem', 'position': 3, 'name': titolo, 'item': url}]}], ensure_ascii=False).replace('</', '<\\/')
    corpo = f'''<section class="rp-hero"><p>Assemblea Popolare Ecumenica (APE) &middot; puntata {g}</p><h1>{e(titolo)}</h1></section>
<div class="rp-wrap">
<p class="rp-mig"><a href="./">APE</a> &rsaquo; <a href="attualita.html">Attualit&agrave;</a> &rsaquo; {e(titolo)}</p>
<p class="rp-data">{data[8:].lstrip('0')} {[k for k, v in MESI.items() if v == int(data[5:7])][0]} {data[:4]}</p>
<p><strong>{linka(par[0])}</strong></p>
<div style="position:relative;max-width:380px;margin:14px auto 6px"><video controls preload="none" playsinline poster="images/{N}-poster.webp" width="540" height="960" style="display:block;width:100%;max-width:380px;height:auto;border-radius:10px;margin:0;background:#0b1a2e" aria-label="{e(titolo)}. Puntata {g} del Progetto APE"><source src="video/{N}.mp4" type='video/mp4; codecs="hvc1"'><source src="video/{N}-h264.mp4" type="video/mp4">Il tuo browser non riproduce il video.</video></div>
<p class="rp-fonte" style="margin-top:6px">Puntata {g} di &laquo;APE spiegata a puntate&raquo;. Video con voce di sintesi e immagini generate con l&rsquo;intelligenza artificiale.</p>
{''.join(f'<p>{linka(p)}</p>' + chr(10) for p in par[1:])}<div class="rp-box"><p><strong>Per approfondire</strong></p><ul>
<li><a href="progetto.html">Il progetto APE per intero</a>: il testo ufficiale della proposta</li>
<li><a href="patto.html">Il Patto fondativo della Rete APE</a></li>
<li><a href="attualita.html#risposte">Tutte le risposte dell&rsquo;APE, puntata per puntata</a></li></ul></div>
<a class="rp-cta" href="rete.html#aderisci">Aderisci alla Rete APE (gratis)</a>
<nav class="rp-pn" aria-label="Altre puntate"><span>{f'&larr; <a href="{prev_["slug"]}.html">{e(prev_["titolo"])}</a>' if prev_ else ''}</span><span>{f'<a href="{next_["slug"]}.html">{e(next_["titolo"])}</a> &rarr;' if next_ else ''}</span></nav>
</div>'''
    head = f'''<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(titolo_pag)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="APE — {NOME}">
<meta property="og:title" content="{e(titolo_pag)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="1600">
<meta property="og:image:height" content="900">
<meta property="og:image:alt" content="{e(titolo)} — APE, {NOME}">
<meta property="og:locale" content="it_IT">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(titolo_pag)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{img}">
<script>if(location.protocol==='http:'&&/assembleapopolareecumenica\\.it$/.test(location.hostname))location.replace('https://'+location.host+location.pathname+location.search+location.hash)</script><link rel="icon" href="favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="192x192" href="images/favicon-192.png"><link rel="apple-touch-icon" href="images/apple-touch-icon.png"><script src="video-cta.js" defer></script>
<link href="fonts/caratteri.css" rel="stylesheet">
<link rel="stylesheet" href="css/ape-leggibilita.css">
<link rel="stylesheet" href="css/ape-base.css">
<style>{cb.neutro(cb.STILE)}</style>
{CSS}
<script type="application/ld+json">{ld}</script>
</head>
<body>
{cb.testa(slug + '.html', 'attualita.html')}
<main id="contenuto">
{corpo}
</main>
{cb.PIEDE}
</body>
</html>
'''
    open(f'{QUI}{slug}.html', 'w', encoding='utf-8').write(head)
    return f'{slug}.html'


def blocco_elenco(tutte, classe):
    li = ''.join(f'<li><a href="{x["slug"]}.html">{e(x["titolo"])}</a></li>' for x in tutte)
    return li


def sostituisci_blocco(testo, nome, nuovo, dopo):
    """Mette <!--nome-->nuovo<!--/nome--> (lo rifà se c'è già, altrimenti dopo la stringa `dopo`)."""
    a, b = f'<!--{nome}-->', f'<!--/{nome}-->'
    blocco = a + nuovo + b
    if a in testo:
        return re.sub(re.escape(a) + '.*?' + re.escape(b), lambda m: blocco, testo, flags=re.S)
    assert testo.count(dopo) >= 1, f'{nome}: ancora «{dopo}» non trovata'
    return testo.replace(dopo, dopo + '\n' + blocco, 1)


def main(numeri=None):
    sys.path.insert(0, QUI + '_tools')
    import costruisci as cb
    tutte = pubblicate()
    # se si indicano dei numeri si rifanno solo quelle pagine, ma elenchi, collegamenti e sitemap restano su TUTTE le pagine esistenti
    da_fare = [d for d in tutte if not numeri or d['g'] in numeri]
    assert da_fare, 'nessuna puntata da generare'
    tutte = [d for d in tutte if d in da_fare or os.path.exists(f'{QUI}{d["slug"]}.html')]
    files = [costruisci_pagina(d, tutte, cb) for d in da_fare]
    # elenco in Attualità: sorgente (_contenuti) e pagina già costruita
    elenco = ('<section class="at-voce" id="risposte"><h2>Le risposte dell&rsquo;APE, una per una</h2>'
              '<p>Ogni puntata di &laquo;APE spiegata a puntate&raquo; ha la sua pagina, con la risposta scritta e il video.</p><ul>'
              + blocco_elenco(tutte, '') + '</ul></section>')
    for rel in ('_contenuti/attualita.html', 'attualita.html'):
        p = QUI + rel
        s = open(p, encoding='utf-8').read()
        n = sostituisci_blocco(s, 'risposte', elenco, '<div class="at-wrap">')
        if n != s:
            open(p, 'w', encoding='utf-8').write(n)
    # home: collegamenti interni + H1 con il nome per esteso
    p = QUI + 'index.html'
    s = open(p, encoding='utf-8').read()
    box = ('<section class="ap-risposte" aria-label="Le risposte dell&rsquo;APE" style="max-width:960px;margin:28px auto;padding:0 20px">'
           '<h2 style="font-size:1.25em;margin:0 0 10px">Le risposte dell&rsquo;Assemblea Popolare Ecumenica</h2><ul style="columns:2;column-gap:28px;margin:0;padding-left:20px;line-height:1.7">'
           + blocco_elenco(tutte, '') + '</ul><p style="margin:12px 0 0"><a href="progetto.html">Leggi il progetto APE per intero</a> &middot; <a href="patto.html">Leggi il Patto fondativo</a> &middot; <a href="attualita.html">Tutte le novit&agrave;</a></p></section>')
    if '<!--risposte-->' in s:
        s = sostituisci_blocco(s, 'risposte', box, '')
    else:
        assert s.count('</main>') == 1
        s = s.replace('</main>', '<!--risposte-->' + box + '<!--/risposte--></main>', 1)
    sr = '<span style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap">Assemblea Popolare Ecumenica (APE): </span>'
    s = s.replace('<h1 id="ap-domanda">' + sr + 'Tra un voto e l&rsquo;altro,', '<h1 id="ap-domanda">Tra un voto e l&rsquo;altro,')   # niente testo nascosto: il nome sta nel kicker visibile
    s = s.replace('<span>APE &middot; Assemblea Popolare Ecumenica</span>', '<span>Assemblea Popolare Ecumenica (APE)</span>')
    org = json.dumps({'@context': 'https://schema.org', '@type': 'Organization', 'name': NOME, 'alternateName': 'APE', 'url': SITO,
                      'logo': SITO + 'images/favicon-512.png',
                      'sameAs': ['https://www.facebook.com/profile.php?id=61595012680370', 'https://t.me/assembleapopolareecumenica',
                                 'https://assembleapopolareecumenica.substack.com']}, ensure_ascii=False)
    blocco_org = '<!--org--><script type="application/ld+json">' + org + '</script><!--/org-->'
    if '<!--org-->' in s:
        s = re.sub(r'<!--org-->.*?<!--/org-->', lambda m: blocco_org, s, flags=re.S)
    else:
        s = s.replace('</head>', blocco_org + '\n</head>', 1)
    open(p, 'w', encoding='utf-8').write(s)
    for rel, vec, nuo in (('progetto.html', '<h1>Il progetto APE per intero</h1>', '<h1>Il progetto dell&rsquo;Assemblea Popolare Ecumenica (APE) per intero</h1>'),
                          ('patto.html', '<h1>Patto fondativo della Rete APE</h1>', '<h1>Patto fondativo della Rete APE &mdash; Assemblea Popolare Ecumenica</h1>'),
                          ('progetto.html', '<p class="sottotitolo">Il problema, il sorteggio,', '<p class="sottotitolo">Assemblea Popolare Ecumenica (APE): il problema, il sorteggio,'),
                          ('patto.html', '<p>Chi firma questo Patto non entra in un progetto altrui.', '<p>Chi firma questo Patto della Rete dell&rsquo;Assemblea Popolare Ecumenica (APE) non entra in un progetto altrui.')):
        t = open(QUI + rel, encoding='utf-8').read()
        if vec in t:
            open(QUI + rel, 'w', encoding='utf-8').write(t.replace(vec, nuo))
    # sitemap: aggiunge le pagine (senza toccare le altre voci)
    sm = open(QUI + 'sitemap.xml', encoding='utf-8').read()
    oggi = datetime.date.today().isoformat()
    for d in tutte:
        loc = f'{SITO}{d["slug"]}.html'
        riga = f'<url><loc>{loc}</loc><lastmod>{oggi}</lastmod></url>\n'
        if loc in sm:
            sm = re.sub(r'<url><loc>%s</loc>.*?</url>\n' % re.escape(loc), lambda m: riga, sm)
        else:
            sm = sm.replace('</urlset>', riga + '</urlset>')
    open(QUI + 'sitemap.xml', 'w', encoding='utf-8').write(sm)
    print('pagine:', ', '.join(files))
    return files


if __name__ == '__main__':
    main([int(x) for x in sys.argv[1:]] or None)
