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
    'index.html': ('ape.html', 'Tra un voto e l’altro, chi ti ascolta? | APE — Assemblea Popolare Ecumenica', 'images/ape-anteprima-domanda.jpg'),
    'rete.html': ('rete-ape.html', 'Rete APE — aderisci | Assemblea Popolare Ecumenica',
                  'images/rete-ape-anteprima.jpg'),
}
DESCRIZIONI = {'index.html': 'Oggi una richiesta dei cittadini si può ignorare a costo zero. L&#x27;APE, Assemblea Popolare Ecumenica, propone cittadini sorteggiati e istituzioni obbligate a rispondere. Capirla in 6 minuti.'}
VOLTO = 'images/angelo-nicotra-volto.webp'

# Fernando, 01/10/2026: «anche sul sito APE va scritto almeno il perche' della sua nascita».
# Testo SOLO del sito APE (non esiste su PA), in voce neutra: non il «noi» del movimento.
PERCHE_SITO = (
    '<div class="pa-box" id="perche"><h3>Un&rsquo;idea che appartiene a chi la firma</h3>'
    '<p>Ogni progetto nasce da qualcuno, ma vive solo se diventa di tutti. L&rsquo;APE &egrave; nata come proposta: '
    'da oggi &egrave; di chi la fa propria. <strong>&laquo;Ecumenica&raquo; vuol dire aperta a tutti, senza distinzioni</strong>: '
    'per questo ha una casa sua, neutra, senza simboli n&eacute; bandiere. Un&rsquo;unione d&rsquo;intenti, non di simboli o ideologie.</p>'
    '<p>La Rete APE non si eredita: si fonda insieme. Chi aderisce firma il <a href="patto.html">Patto fondativo</a> ed entra '
    'nell&rsquo;<a href="albo.html">Albo dei co-fondatori</a>, in ordine alfabetico, senza primi e senza ultimi: pu&ograve; dire '
    '&laquo;questo progetto &egrave; anche mio, l&rsquo;ho fondato anch&rsquo;io&raquo;. Il testo resta aperto: ogni co-fondatore '
    'pu&ograve; proporre miglioramenti, e si decide con peso paritario.</p>'
    '<p style="margin:0"><a href="patto.html"><strong>Non aderisci a un progetto: lo fondi &rarr;</strong></a></p></div>\n')

# Fernando, 01/10/2026: anche sul sito APE il video «E dopo il voto?» (6 minuti, il piu' breve):
# va per primo, subito dopo «Perche' questo sito». youtube-nocookie come nel resto dei siti.
VIDEO_DOPO_IL_VOTO = (
    '<div class="pa-box" id="video"><h3>L&rsquo;APE in sei minuti</h3>'
    # 02/10/2026 Fernando (schermata): YouTube mette in testa al video il canale «Partecipazione Attiva» e non si toglie.
    # Il filmato sta sul sito APE (stesso video di YouTube 5Z9MGRmQo04, H.264 720p): nessun marchio di nessuno.
    '<video controls preload="none" playsinline poster="images/ape-dopo-il-voto-copertina.webp" '
    'style="width:100%;height:auto;border-radius:10px;margin:6px 0 12px;background:#0b1a2e" '
    'aria-label="E dopo il voto? La proposta APE spiegata: che cos&rsquo;&egrave; e come funziona">'
    '<source src="video/ape-dopo-il-voto.mp4" type="video/mp4">Il tuo browser non riproduce il video.</video>'
    '<p style="margin:0">Cittadini sorteggiati, istituzioni obbligate a rispondere, referendum senza quorum, '
    'e i punti deboli che la proposta stessa riconosce.</p></div>\n'
    # lo spot «Tocca a noi» rifatto senza il logo di PA (stesso filmato, fascia in alto coperta: resta il riquadro APE)
    '<div class="pa-box" id="spot"><h3>Tocca a noi</h3>'
    '<video controls preload="none" playsinline poster="images/ape-tocca-a-noi-copertina.webp" '
    'style="display:block;width:100%;max-width:420px;height:auto;margin:6px auto 12px;border-radius:10px;background:#0b1a2e" '
    'aria-label="Tocca a noi: lo spot della Rete APE"><source src="video/ape-tocca-a-noi.mp4" type="video/mp4">'
    'Il tuo browser non riproduce il video.</video>'
    '<p style="margin:0">Da troppo tempo nessuno ascolta una voce. La tua. Per cambiare le cose non serve un salvatore. '
    'Non arriver&agrave;. Serviamo noi, tutti, alla pari. Possiamo essere i leader di noi stessi. Tocca a noi.</p></div>\n')

VIDEO_PROGETTO = (
    '<h2>Il Progetto APE, spiegato per intero</h2>\n'
    '<p>In undici minuti, con i documenti sullo schermo: il problema dell&rsquo;astensione, le radici storiche del sorteggio, '
    'come funzionano le direttive vincolanti, le tre leggi costituzionali, i costi, le domande pi&ugrave; frequenti e i punti deboli '
    'dichiarati dalla proposta stessa. Per approfondire c&rsquo;&egrave; la sintesi del volume, qui sotto.</p>\n'
    '<video controls preload="none" playsinline poster="images/ape-progetto-spiegato-copertina.webp" '
    'style="width:100%;height:auto;border-radius:10px;margin:1.5em 0;background:#0b1a2e" '
    'aria-label="Il Progetto APE, spiegato per intero"><source src="video/ape-progetto-spiegato.mp4" type="video/mp4">'
    'Il tuo browser non riproduce il video.</video>\n\n')

# 02/10/2026 Fernando: «come possiamo migliorare il sito APE per suscitare almeno curiosità a leggere e a capire cos'è».
# La prima schermata (sul telefono: titolo, data e copertina a tutto schermo) non dava motivo di scorrere.
# Ora: una domanda, tre fatti, due porte (6 minuti di video, 2 minuti di lettura); poi l'esempio, poi le domande.
# Fatti dalla Sintesi del 26/09: 20 milioni di astenuti (p. 1), «ignorata a costo zero» e «conformarsi o motivare» (p. 3).
INGRESSO = (
    '<style>'
    '.ap-in{background:linear-gradient(160deg,#0b1f33 0%,#17507a 100%);color:#fff;padding:26px 16px 30px;text-align:center}'
    '.ap-in .k{font-family:Montserrat,system-ui,sans-serif;font-size:.78em;font-weight:700;letter-spacing:1.6px;text-transform:uppercase;color:#ffd75e;margin:0 0 14px}'
    '.ap-in h1{font-family:Merriweather,Georgia,serif;font-size:2.05em;line-height:1.25;margin:0 auto 18px;max-width:720px;color:#fff}'
    '.ap-tre{list-style:none;padding:0;margin:0 auto 20px;max-width:720px;display:grid;gap:8px;text-align:left}'
    '.ap-tre li{background:rgba(255,255,255,.09);border-left:4px solid #ffd75e;border-radius:10px;padding:9px 14px;'
    'font-family:Montserrat,system-ui,sans-serif;font-size:1.02em;line-height:1.45;color:#eef4f9}'
    '.ap-tre b{color:#fff;font-size:1.12em}'
    '.ap-porte{display:flex;flex-wrap:wrap;gap:12px;justify-content:center}'
    '.ap-porte a{font-family:Montserrat,system-ui,sans-serif;font-weight:800;text-decoration:none;border-radius:50px;padding:15px 24px;min-height:48px;'
    'display:inline-flex;align-items:center;gap:8px;font-size:1.02em}'
    '.ap-porte .p1{background:#ffd75e;color:#0b1f33}.ap-porte .p2{border:2px solid #fff;color:#fff}'
    '.ap-faq details{border:2px solid #9cc3e0;border-radius:12px;margin:10px 0;background:#fff}'
    '.ap-faq summary{cursor:pointer;font-family:Montserrat,system-ui,sans-serif;font-weight:800;color:#134a77;padding:14px 18px;min-height:48px;list-style:none}'
    '.ap-faq summary::-webkit-details-marker{display:none}'
    '.ap-faq summary::before{content:"+";display:inline-block;width:1.2em;color:#2981c9}'
    '.ap-faq details[open] summary::before{content:"−"}'
    '.ap-faq details p{margin:0;padding:0 18px 16px}'
    '.ap-libro{display:block;max-width:220px;margin:6px auto 8px;border-radius:10px;box-shadow:0 8px 22px rgba(0,0,0,.15)}'
    '.ap-oggi{font-family:Montserrat,system-ui,sans-serif;font-size:.92em;color:#d6e6f3;margin:16px auto 0;max-width:640px;line-height:1.5}'
    '.ap-fig{max-width:720px;margin:0 auto 22px}.ap-fig img{display:block;width:100%;height:auto;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.35)}'
    '.ap-fig figcaption{font-family:Montserrat,system-ui,sans-serif;font-size:.95em;color:#eef4f9;margin-top:10px}.ap-fig figcaption b{display:block;font-weight:600}.ap-fig figcaption span{display:block;font-size:.75em;opacity:.75;margin-top:4px}'
    '.ap-oggi b{color:#ffd75e}.ap-oggi span,.ap-in .k span{display:block}'
    '.ap-passi{list-style:none;counter-reset:p;padding:0;margin:18px 0 6px}'
    '.ap-passi li{counter-increment:p;position:relative;padding:12px 14px 12px 58px;margin:0 0 22px;background:#fff;border:2px solid #9cc3e0;border-radius:12px;line-height:1.5}'
    '.ap-passi li::before{content:counter(p);position:absolute;left:12px;top:12px;width:32px;height:32px;border-radius:50%;background:#17507a;color:#fff;'
    'font-family:Montserrat,system-ui,sans-serif;font-weight:800;display:flex;align-items:center;justify-content:center}'
    '.ap-passi li:not(:last-child)::after{content:"↓";position:absolute;left:50%;bottom:-22px;transform:translateX(-50%);color:#2981c9;font-weight:900}'
    '.ap-passi b{font-family:Montserrat,system-ui,sans-serif;color:#0e2a40}'
    '.ap-noe{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:22px 0}'
    '.ap-noe div{border-radius:12px;padding:14px 16px;font-family:Montserrat,system-ui,sans-serif;font-size:.95em;line-height:1.7}'
    '.ap-noe .no{background:#f6eded;border:2px solid #d9b3b3}.ap-noe .si{background:#edf6ef;border:2px solid #a9d1b3}'
    '.ap-noe h3{margin:0 0 6px;font-size:1em}'
    '.ap-livelli{display:grid;gap:10px;margin:22px 0}'
    '.ap-livelli a{display:block;border:2px solid #2981c9;border-radius:12px;padding:12px 16px;text-decoration:none;color:#0e2a40;'
    'font-family:Montserrat,system-ui,sans-serif;line-height:1.45}'
    '.ap-livelli a b{display:block;color:#17507a}'
    '@media(max-width:600px){.ap-in h1{font-size:1.6em}.ap-porte a{width:100%;justify-content:center}.ap-noe{grid-template-columns:1fr}}'
    '</style>'
    '<section class="ap-in" aria-labelledby="ap-domanda">'
    '<p class="k"><span>APE &middot; Assemblea Popolare Ecumenica</span> <span>Proposta di riforma costituzionale</span></p>'
    '<h1 id="ap-domanda">Tra un voto e l&rsquo;altro,<br>chi ti ascolta?</h1>'
    '<ul class="ap-tre">'
    '<li><b>20&nbsp;milioni</b> di italiani non hanno votato alle ultime politiche.</li>'
    '<li>Oggi una richiesta dei cittadini si pu&ograve; <b>ignorare a&nbsp;costo&nbsp;zero</b>.</li>'
    '<li>Con l&rsquo;APE chi governa <b>deve&nbsp;rispondere</b>: s&igrave;, oppure un no motivato in&nbsp;pubblico.</li>'
    '</ul>'
    # 02/10/2026 Fernando: l'immagine «subito dopo le tre domande» — il cittadino parla, il consiglio ascolta.
    # Illustrazione generata con Meta AI (dichiarata: AI Act art. 50); file in LAVORI/ape_immagine_ascolto.
    '<figure class="ap-fig"><img src="images/ape-il-consiglio-ascolta.webp" '
    'srcset="images/ape-il-consiglio-ascolta-800.webp 800w, images/ape-il-consiglio-ascolta.webp 1600w" sizes="(max-width:760px) 100vw, 720px" '
    'width="1600" height="900" alt="Illustrazione: in una sala consiliare un cittadino parla al microfono; sindaca, presidente e consiglieri lo ascoltano, il pubblico &egrave; seduto di spalle">'
    '<figcaption><b>Con l&rsquo;APE, la voce dei cittadini arriva dove si&nbsp;decide.</b> <b>E chi governa deve&nbsp;rispondere.</b> <span>Illustrazione realizzata con l&rsquo;intelligenza artificiale.</span></figcaption></figure>'
    '<div class="ap-porte"><a class="p1" href="#video">&#9654; Capire in 6 minuti</a>'
    '<a class="p2" href="#in-breve">Leggere in 2 minuti</a></div>'
    # Fernando 02/10/2026: «andare a capo sempre a frasi compiute» — una frase per riga
    '<p class="ap-oggi"><span><b>Oggi l&rsquo;APE &egrave; una proposta</b>:</span> <span>per esistere serve una&nbsp;riforma della&nbsp;Costituzione.</span> '
    '<span>La&nbsp;<b>Rete&nbsp;APE</b> &egrave; chi&nbsp;la&nbsp;sostiene gi&agrave;&nbsp;adesso.</span></p>'
    '</section>\n')

# L'esempio e' quello di «E dopo il voto?» (copione del 26/09), dichiarato inventato come nel video.
LIBRO = ('<p style="text-align:center;margin:30px 0 6px"><img class="ap-libro" src="images/ape-copertina.webp" '
         'alt="Copertina: APE, Assemblea Popolare Ecumenica, un canale permanente di voce dei cittadini" width="1368" height="1935" loading="lazy"></p>'
         '<p style="text-align:center;font-family:Montserrat,system-ui,sans-serif;font-size:.9em;color:#4a5a66;margin:0 0 26px">'
         'Il libro, di prossima pubblicazione. La sintesi si pu&ograve; gi&agrave; scaricare <a href="#documenti">qui sotto</a>.</p>\n')

IN_BREVE = (
    '<div class="pa-box" id="in-breve"><h3>L&rsquo;APE in cinque righe</h3>'
    '<p>Assemblee di <strong>cittadini comuni, estratti a sorte</strong>, in ogni Comune, in ogni Regione e a livello nazionale. '
    'Non fanno leggi e non governano: mandano <strong>direttive</strong> a Comuni, Regioni e Governo. '
    'Chi le riceve deve attuarle, oppure respingerle con un voto a maggioranza assoluta e una motivazione pubblica. '
    'Si paga abolendo il Senato. E se nessuno risponde, decidono i cittadini con un referendum.</p>'
    '<p style="margin:16px 0 0"><strong>Un esempio, inventato per capirci.</strong> Un gruppo di genitori chiede un attraversamento '
    'pedonale sicuro davanti alla scuola. Porta la proposta allo sportello del Comune, che la registra in modo pubblico. '
    'L&rsquo;assemblea del Comune la esamina e, se la approva, la trasforma in una direttiva. A quel punto il Comune ha due strade: '
    'la realizza, oppure la respinge votando a maggioranza assoluta e spiegando pubblicamente perch&eacute;. '
    '<strong>Far finta di niente non &egrave; pi&ugrave; possibile.</strong></p></div>\n')

# I passaggi sono quelli del «ciclo della direttiva» gia' sulla pagina (dal documento integrale v7.0), in breve.
COME_FUNZIONA = (
    '<h2 id="come-funziona">Come funziona, passo per passo</h2>'
    '<ol class="ap-passi">'
    '<li><b>Il cittadino</b> porta una proposta allo sportello del suo Comune, che la registra con ricevuta.</li>'
    '<li><b>L&rsquo;assemblea sorteggiata</b> la esamina in sedute pubbliche, ascoltando esperti e cittadini.</li>'
    '<li><b>Se la approva, diventa una direttiva</b>, pubblicata entro 24 ore.</li>'
    '<li><b>L&rsquo;istituzione deve rispondere</b>: la attua, oppure la respinge con un voto a maggioranza assoluta e una motivazione pubblica.</li>'
    '<li><b>Un organo indipendente verifica</b> che quello che &egrave; stato deciso venga fatto davvero.</li>'
    '<li><b>Se tutto si ferma</b> per 120 giorni, si pu&ograve; chiedere un referendum: decidono i cittadini.</li>'
    '</ol>'
    '<div class="ap-noe">'
    '<div class="no"><h3>L&rsquo;APE non &egrave;</h3>&#10007; un partito<br>&#10007; un governo<br>&#10007; un secondo Parlamento<br>&#10007; un organo che fa leggi</div>'
    '<div class="si"><h3>L&rsquo;APE &egrave;</h3>&#10003; cittadini sorteggiati<br>&#10003; partecipazione permanente<br>&#10003; obbligo di risposta<br>&#10003; controllo di quello che si fa</div>'
    '</div>\n')

# Tre livelli di lettura: chi ha pochi minuti, chi vuole capire, chi vuole verificare.
LIVELLI = (
    '<h2 id="approfondisci">Vuoi capire tutto?</h2>'
    '<div class="ap-livelli">'
    '<a href="#video"><b>&#9654; 6 minuti &middot; il video</b>Che cos&rsquo;&egrave;, com&rsquo;&egrave; fatta, come funziona.</a>'
    '<a href="documenti/APE_Sintesi_Pubblica.pdf" target="_blank" rel="noopener"><b>&#128196; 7 pagine &middot; la sintesi del volume</b>Il problema, le radici, le tre leggi, i costi, le domande e i punti deboli.</a>'
    '<a href="documenti/APE_Assemblea_Popolare_Ecumenica_v7.0.pdf" target="_blank" rel="noopener"><b>&#128209; 20 pagine &middot; il documento integrale</b>Le formule costituzionali, i costi voce per voce, le obiezioni e le risposte.</a>'
    '</div>\n')

# Risposte dalla Sintesi del 26/09 (pp. 2-6), con le parole di tutti i giorni.
FAQ = (
    '<div class="ap-faq" id="domande"><h2>Ma allora&hellip;?</h2>'
    '<details><summary>&Egrave; un partito?</summary><p>No. Non presenta candidati e non si vota. Anzi: chi &egrave; iscritto a un partito, '
    'o ha avuto cariche politiche nei due anni precedenti, non pu&ograve; essere sorteggiato.</p></details>'
    '<details><summary>Toglie potere al Parlamento?</summary><p>Non lo sostituisce e non fa leggi. Le direttive non obbligano a dire s&igrave;: '
    'obbligano a rispondere. Non vincolano il voto del singolo parlamentare, ma l&rsquo;indirizzo del Governo.</p></details>'
    '<details><summary>Chi ci entra?</summary><p>Cittadini estratti a sorte dalle liste elettorali, con un equilibrio di et&agrave;, '
    'genere e territorio: oltre 46.000 persone in pi&ugrave; di 6.500 assemblee. Nessuno &egrave; eletto.</p></details>'
    '<details><summary>Quanto costa?</summary><p>A regime 252 milioni l&rsquo;anno. Il Senato, che la riforma abolisce, ne costa oggi 541: '
    'il risparmio stimato con prudenza &egrave; di 250-260 milioni l&rsquo;anno. Sulla carta sarebbe 289, ma alcune spese del Senato, come immobili e pensioni gi&agrave; maturate, non spariscono.</p></details>'
    '<details><summary>E se il Governo non risponde?</summary><p>Se una direttiva resta ferma per 120 giorni, senza essere accolta e senza un rifiuto motivato, '
    'si pu&ograve; chiedere un referendum propositivo: lo chiedono due terzi dell&rsquo;assemblea nazionale oppure 500.000 cittadini. '
    'Vale senza quorum, e se passa il Governo ha 180 giorni per attuarla.</p></details>'
    '<details><summary>Chi viene sorteggiato perde il lavoro?</summary><p>&Egrave; uno dei punti deboli che la proposta stessa dichiara: '
    'chi viene sorteggiato non deve rimetterci stipendio o posto, e dovr&agrave; garantirlo la legge che attua la riforma.</p></details>'
    '<details><summary>&Egrave; gi&agrave; legge?</summary><p>No, &egrave; una proposta. Serve una riforma della Costituzione approvata dal Parlamento. '
    'La strada scelta &egrave; la legge di iniziativa popolare: servono 50.000 firme, l&rsquo;obiettivo &egrave; raccoglierne dieci volte tante.</p></details>'
    '</div>\n')

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
         '<p>È una riforma costituzionale che non aggiunge un partito né un candidato, ma uno strumento permanente attraverso cui ogni cittadino può obbligare le istituzioni ad ascoltare e a rispondere.</p>', 1),
        ('alt="Angelo Nicotra Presidente Partecipazione Attiva" width="500" height="750"', 'alt="Angelo Nicotra" width="300" height="300"', 1),
        ('images/organigramma/angelo-nicotra-finale.webp', VOLTO, 1),
        ('<h2>La Rete APE: una chiamata unitaria, non di Partecipazione Attiva</h2>', '<h2>La Rete APE: una chiamata unitaria</h2>', 1),
        # 02/10/2026: «gli studi mostrano» senza fonte, e «produce» uno specchio statistico, erano affermazioni assolute
        ('Non è apatia: gli studi mostrano che è rifiuto consapevole di un sistema percepito come distante e non più influenzabile.',
         'Le cause dell&rsquo;astensione sono molte e non si riducono a una sola. La proposta parte da una lettura precisa: non apatia, ma il rifiuto di un sistema percepito come distante e non più influenzabile.', 1),
        ('Il sorteggio, al contrario, produce uno specchio statistico della popolazione',
         'Il sorteggio, al contrario, con la stratificazione per età, genere e territorio prevista dal progetto, mira a uno specchio statistico della popolazione', 1),
        # 02/10/2026, revisione delle parole: niente conclusioni piu' grandi dei fatti
        ('la scelta più identitaria del progetto', 'una delle scelte fondamentali del progetto', 1),
        ('produce inevitabilmente ciò che si vuole tenere fuori', 'comporta ciò che il progetto vuole tenere fuori', 1),
        ('è già nel nostro ordinamento e funziona.', 'è già previsto nel nostro ordinamento.', 1),
        ('prova che la permanenza e il dovere di risposta funzionano.', 'un&rsquo;esperienza concreta di consiglio permanente e di obbligo di risposta.', 1),
        ('Va detto con chiarezza cosa la Convention Citoyenne francese dimostra e cosa no: non dimostra che il sorteggio non funziona — dimostra che il sorteggio senza obbligo di risposta e senza sbocco è teatro.',
         'Dalla Convention Citoyenne francese il progetto trae una lezione precisa: senza un obbligo di risposta e senza uno sbocco, il lavoro dei cittadini sorteggiati rischia di restare senza seguito.', 1),
        ('(risparmio teorico: 289 milioni)',
         '(sulla carta 289 milioni, cioè 541 meno 252: la stima prudente tiene conto delle spese che non spariscono con il Senato, come immobili, senatori a vita in carica e pensioni già maturate)', 1),
        ('alle tante piccole associazioni — come lo è Partecipazione Attiva — che da sole pesano poco e insieme possono incidere. Per questo Partecipazione Attiva ha aperto una rete che invita',
         'alle tante piccole associazioni che da sole pesano poco e insieme possono incidere. Per questo c’è una rete che invita', 1),
    ],
    'rete.html': [
        ('<span class="article-date">Presidente di Partecipazione Attiva</span>', '<span class="article-date">Ideatore del Progetto APE &middot; Presidente di Partecipazione Attiva</span>', 1),
        ('object-position:top center" width="1024" height="1536"', 'object-position:center" width="300" height="300"', 1),
        ('Leggi%20questo%20articolo%20di%20Partecipazione%20Attiva%3A%20', 'Rete%20APE%2C%20Assemblea%20Popolare%20Ecumenica%3A%20', None),
        (' elaborato da <strong>Angelo Nicotra</strong>, Presidente di Partecipazione Attiva.', '.', 1),
        (', elaborata da Angelo Nicotra, Presidente di Partecipazione Attiva.', '.', 1),
        ('<h2>I soggetti aderenti</h2>', '<h2>I co-fondatori</h2>', 1),
        # 02/10/2026, tono: la Rete parla come la proposta, non come un movimento contro qualcuno
        ('<p class="article-subtitle" style="font-size:1.35em;font-weight:700;font-style:italic;margin-bottom:10px">&#8220;Divide et impera&#8221;</p>', '', 1),
        ('Il potere si mantiene frammentando i cittadini. La Rete APE nasce per rovesciare questa logica &#8212; unire soggetti diversi su principi comuni, con peso paritario per tutti.',
         'Cittadini, associazioni, comitati e movimenti che sostengono insieme la proposta APE, con peso paritario per tutti.', 1),
        ('I risultati del &#8220;divide et impera&#8221; sono misurabili: alle', 'Il punto di partenza &#232; un dato: alle', 1),
        (' Una massa enorme che ha rinunciato a decidere il proprio futuro, consegnando deleghe in bianco a pochi politici, a prescindere dalla posizione ideologica.', '', 1),
        ('Non &#232; apatia. &#200; la conseguenza diretta di una frammentazione deliberata: associazioni, movimenti e comitati che non si parlano, che si ignorano o si combattono, incapaci di costruire una proposta comune. La Rete APE nasce per rompere questo schema.',
         'Le cause dell&#8217;astensione sono molte. Una, che la Rete prova ad affrontare, &#232; la dispersione: associazioni, movimenti e comitati che lavorano ciascuno per conto proprio, senza una proposta comune. La Rete APE offre un terreno condiviso. Non &#232; un partito n&#233; una coalizione elettorale: chi aderisce, partiti compresi, lo fa alla pari e senza simboli, e non ottiene alcun ruolo nelle future Assemblee, dove si entra solo per sorteggio.', 1),
    ],
}
# pagine APE: come si chiamano qui
INTERNE = {'ape.html': './', 'rete-ape.html': 'rete.html', 'patto.html': 'patto.html', 'albo.html': 'albo.html'}   # patto/albo: pagine proprie
COPIA_FISSA = ['fonts']
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
.ape-voci a.ape-aderisci{background:rgb(255,215,94);color:rgb(11,31,51)}
/* i pulsanti di PA hanno testo scuro su arancio: sul blu serve il bianco (pa11y: 4,39 -> a norma) */
main a.btn,main a.btn:visited,main a[href^="mailto:"][style*="background"]{background:#17507a!important;color:#fff!important}
h1,h2,h3,.sottotitolo,.article-subtitle,.ap-in p,.ap-hero p,.ape-piede p,summary{text-wrap:balance}
p,li{text-wrap:pretty}
.ape-salta{position:absolute;left:-9999px}
.ape-salta:focus{left:8px;top:8px;background:#fff;padding:10px 14px;z-index:99;border:2px solid #8a4e00}
.ape-piede{background:#3a2000;color:#fff;padding:34px 18px;text-align:center;
  font-family:Montserrat,system-ui,sans-serif;font-size:1em;line-height:1.7}
.ape-piede a{color:#ffd580;font-weight:700}
.ape-piede p{max-width:760px;margin:0 auto 10px}
.ape-piede .ape-piccolo{font-size:.9em;color:#f3e6d3}
@media(max-width:700px){.ape-testa{position:static}.ape-voci{flex-wrap:nowrap;overflow-x:auto;width:100%;scrollbar-width:none;-webkit-overflow-scrolling:touch}.ape-voci::-webkit-scrollbar{display:none}.ape-voci a{padding:8px 11px;font-size:.95em;white-space:nowrap;flex:0 0 auto}.ape-voci a.ape-aderisci{order:-1}}
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
        elif base.startswith('video/') and os.path.exists(QUI + base):
            nuovo = base + coda               # filmato proprio del sito APE (versione senza marchi)
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
    voci = [('./', 'Il progetto', 'index.html'), ('./#come-funziona', 'Come funziona', None), ('progetto.html', 'Nel dettaglio', 'progetto.html'),
            ('patto.html', 'Il Patto', 'patto.html'), ('rete.html', 'Rete APE', 'rete.html'),
            ('albo.html', 'Albo', 'albo.html'), ('attualita.html', 'Attualità', 'attualita.html'), ('./#documenti', 'Documenti', None)]
    h = ''.join(f'<a href="{u}"{" aria-current=page" if attuale == f else ""}>{t}</a>'
                for u, t, f in voci) + '<a class="ape-aderisci" href="rete.html#aderisci">Aderisci</a>'
    return ('<a class="ape-salta" href="#contenuto">Salta al contenuto</a>'
            '<header class="ape-testa"><div class="ape-testa-in">'
            '<a class="ape-marchio" href="./" aria-label="APE, Assemblea Popolare Ecumenica: pagina iniziale">'
            '<span class="ape-ape" aria-hidden="true">&#x1F41D;</span>'
            '<span><b>APE</b><span>Assemblea Popolare Ecumenica</span></span></a>'
            f'<nav class="ape-voci" aria-label="Menu principale">{h}</nav></div></header>')


PIEDE = (f'<footer class="ape-piede"><p><strong>APE &mdash; Assemblea Popolare Ecumenica</strong><br>'
         f'Un progetto aperto a tutti: cittadini, associazioni, movimenti, comitati, con peso paritario.</p>'
         f'<p>La proposta &egrave; pubblica e appartiene a chi la sottoscrive: chi firma il <a href="patto.html">Patto fondativo</a> '
         f'ne diventa co-fondatore, alla pari di tutti.</p>'
         f'<p class="ape-piccolo"><a href="progetto.html">Il progetto per intero</a> &middot; <a href="patto.html">Il Patto</a> &middot; '
         f'<a href="./#documenti">Documenti</a> &middot; <a href="rete.html#aderisci">Aderisci</a></p>'
         f'<p class="ape-piccolo">Contatti: <a href="mailto:info@assembleapopolareecumenica.it">info@assembleapopolareecumenica.it</a>'
         f' &middot; <a href="{SITO_PA}privacy.html">Privacy e informativa sull&rsquo;adesione</a> &middot; Questo sito non usa cookie di profilazione '
         f'n&eacute; tracciatori.</p><p class="ape-piccolo">Aggiornato il {datetime.date.today().strftime("%d/%m/%Y")} &middot; &copy; {datetime.date.today().year}</p></footer>')


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
        corpo = corpo.replace(aggancio, IN_BREVE + COME_FUNZIONA + VIDEO_DOPO_IL_VOTO + FAQ + LIVELLI + LIBRO + PERCHE_SITO + aggancio, 1)
        corpo, n = re.subn(r'<img class="pa-hero-img"[^>]*>\s*', '', corpo, count=1)
        if n != 1:
            stop('index: non trovo la copertina in testa')
    for vecchio, nuovo, quante in RISCRITTURE.get(uscita, []):
        c = corpo.count(vecchio)
        if (quante is not None and c != quante):
            stop(f'{uscita}: «{vecchio[:50]}…» compare {c} volte, ne aspettavo {quante}')
        corpo = corpo.replace(vecchio, nuovo)
    # 02/10/2026 (Patto fondativo): in apertura niente foto e qualifica dell'ideatore, «il progetto non ha padrone».
    # La riga sull'origine sta nel pie' di pagina.
    if uscita == 'index.html':   # dopo le riscritture (che toccano anche il sottotitolo del titolo di PA)
        corpo, n = re.subn(r'<div class="author-hero">.*?<div class="author-hero-info">.*?</div>\s*</div>\s*</div>', '', corpo, count=1, flags=re.S)
        if n != 1:
            stop('index: non trovo il riquadro dell autore da togliere')
        corpo, n = re.subn(r'<div class="article-hero">.*?<div class="article-meta">.*?</div>\s*</div>', '<!--INGRESSO-->', corpo, count=1, flags=re.S)
        if n != 1:
            stop('index: non trovo il titolo in testa da sostituire')
    if uscita == 'rete.html':
        corpo, n = re.subn(r'<div class="article-meta">\s*<img[^>]*>\s*<div>.*?</div>\s*</div>', '', corpo, count=1, flags=re.S)
        if n != 1:
            stop('rete: non trovo il riquadro dell autore da togliere')
    if uscita == 'rete.html':
        # il ritratto di PA e' un manifesto col marchio: in testa va il solo viso, nel testo si toglie
        tag = re.findall(r'<img[^>]*angelo-nicotra-rete-ape\.webp[^>]*>', corpo)
        if len(tag) != 1:     # quello in testa e' gia' andato via col riquadro dell'autore
            stop(f'rete: aspettavo 1 ritratto di Nicotra nel testo, ne trovo {len(tag)}')
        corpo = corpo.replace(tag[0], '', 1)
    # 02/10/2026 Fernando: «va tolto Nicotra e PA… rendilo veramente aperto e neutro».
    # Via i blocchi che portano il marchio di PA: lo spot «Tocca a noi» (logo PA in ogni fotogramma),
    # il video di PensAttivo (la mascotte del movimento), il riquadro «Primo soggetto aderente».
    # (L'Albo e' in ordine alfabetico, senza primi.) La privacy resta quella di PA: e' il titolare del trattamento.
    TAGLI = {'index.html': [r'<div class="pa-fig">\s*<video[^>]*>.*?ape-tocca-a-noi.*?</figcaption>\s*</div>\s*',
                            ],
             'rete.html': [r'<p[^>]*>&#127811; Primo soggetto aderente</p>\s*<div style="display:inline-flex.*?</div>\s*</div>\s*']}
    if uscita == 'index.html':
        # 02/10/2026 Fernando: «il video di PensAttivo trasformiamolo come E dopo il voto» — al suo posto la versione
        # con voce narrante e cartelli, senza personaggio ne' marchi (file del sito, H.264 720p).
        corpo, n = re.subn(r'<h2>PensAttivo racconta il Progetto APE</h2>.*?</iframe>\s*</div>\s*', VIDEO_PROGETTO, corpo, count=1, flags=re.S)
        if n != 1:
            stop('index: non trovo il video di PensAttivo da sostituire')
    for t in TAGLI.get(uscita, []):
        corpo, n = re.subn(t, '', corpo, count=1, flags=re.S)
        if n != 1:
            stop(f'{uscita}: non trovo il blocco da togliere «{t[:40]}»')
    corpo = neutro(riscrivi_link(corpo, uscita, copiati)).replace('<!--INGRESSO-->', INGRESSO)   # il giallo e' dell'APE: non si ruota
    # 02/10/2026 (Fernando, sulla copertina): la riga «Angelo Nicotra · Partecipazione Attiva» non va sul sito APE.
    # images/ape-copertina-neutra.webp e' la stessa copertina con quella riga coperta dallo sfondo (fatta una volta, a mano).
    corpo = corpo.replace('images/ape-copertina.webp', 'images/ape-copertina-neutra.webp')
    corpo = re.sub(r'alt="APE[^"]*Nicotra[^"]*"', 'alt="APE, Assemblea Popolare Ecumenica: un canale permanente di voce dei cittadini"', corpo)
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
    if uscita == 'index.html':
        # 02/10/2026: la home era lunga quasi 3.000 parole. La parte tecnica (dal problema al confronto col mondo)
        # va in progetto.html; in home resta un rimando con l'elenco dei capitoli.
        i0 = corpo.find("<h2>Il problema che l'APE vuole risolvere</h2>"); i1 = corpo.find('<h2>La Rete APE: una chiamata unitaria</h2>')
        k0 = corpo.find('<article class="article-wrap">'); k1 = corpo.find('</style>', k0)
        if min(i0, i1, k0, k1) < 0 or not (k1 < i0 < i1):
            stop('index: non trovo dove dividere la pagina')
        parte = corpo[i0:i1]
        capitoli = re.findall(r'<h2>(.*?)</h2>', parte)
        ancora = lambda t: 'cap-' + re.sub(r'[^a-z0-9]+', '-', html.unescape(t).lower().replace("'", ' ')).strip('-')[:40]
        for t in capitoli:
            parte = parte.replace(f'<h2>{t}</h2>', f'<h2 id="{ancora(t)}">{t}</h2>', 1)
        voci_cap = ''.join(f'<li><a href="progetto.html#{ancora(t)}">{t}</a></li>' for t in capitoli)
        rimando = ('<div class="pa-box" id="dettaglio"><h3>Il progetto per intero</h3>'
                   '<p style="margin:0 0 10px">Tutti i dettagli, capitolo per capitolo:</p>'
                   f'<ul style="margin:0 0 14px;padding-left:1.2em;line-height:1.9">{voci_cap}</ul>'
                   '<p style="margin:0"><a href="progetto.html"><strong>Leggi il progetto per intero &rarr;</strong></a></p></div>\n')
        corpo = corpo[:i0] + rimando + corpo[i1:]
        dettaglio = ('<div class="article-hero"><h1>Il progetto APE per intero</h1>'
                     '<p class="sottotitolo">Il problema, il sorteggio, i tre livelli, il ciclo della direttiva, le tre leggi, i costi, le difese e il confronto con il mondo.</p></div>\n'
                     '<article class="article-wrap">' + corpo[k0 + len('<article class="article-wrap">'):k1 + len('</style>')] + '\n'
                     '<p><a href="./">&larr; Torna alla pagina iniziale</a> &middot; <a href="./#come-funziona">Come funziona, in breve</a></p>\n'
                     + parte +
                     '<div class="pa-box"><h3>E adesso?</h3><p style="margin:0">Se la proposta ti convince, puoi diventarne co-fondatore firmando il '
                     '<a href="patto.html">Patto fondativo</a>: &egrave; gratuito e alla pari. <a href="rete.html#aderisci"><strong>Aderisci &rarr;</strong></a></p></div>\n'
                     '</article>\n')
        scrivi_pagina('progetto.html', 'Il progetto APE per intero | Assemblea Popolare Ecumenica',
                      'Il progetto APE nel dettaglio: il problema dell&#x27;astensione, il sorteggio, i tre livelli, il ciclo della direttiva, le tre leggi costituzionali, i costi e le difese.',
                      'images/ape-anteprima.jpg', dettaglio, stili, 'da ape.html (parte tecnica)')
    scrivi_pagina(uscita, titolo, desc, anteprima, corpo, stili, f'da {sorgente}')


def scrivi_pagina(uscita, titolo, desc, anteprima, corpo, stili, da):
    mia = SITO + ('' if uscita == 'index.html' else uscita)
    if not os.path.exists(QUI + anteprima):
        stop(f'manca {anteprima}: lancia prima  python3 _tools/immagini.py')
    ld = ('{"@context":"https://schema.org","@type":"WebPage","name":%s,"url":"%s",'
          '"description":%s,"inLanguage":"it","isPartOf":{"@type":"WebSite","name":'
          '"APE — Assemblea Popolare Ecumenica","url":"%s"}}'
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
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{'Tra un voto e l’altro, chi ti ascolta? APE, Assemblea Popolare Ecumenica: 20 milioni di italiani non votano più, oggi una richiesta dei cittadini si ignora a costo zero, con l’APE chi governa deve rispondere' if anteprima.endswith('domanda.jpg') else 'APE, Assemblea Popolare Ecumenica: un canale permanente di voce dei cittadini'}">
<meta property="og:locale" content="it_IT">
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
    print(f'  {uscita:12} {da:18} {len(doc) // 1024} KB')


# Pagine che esistono SOLO sul sito APE (02/10/2026): il contenuto sta in _contenuti/<nome>.html.
# (uscita: titolo, descrizione, anteprima)
PAGINE_PROPRIE = {
    'patto.html': ('Patto fondativo della Rete APE | Assemblea Popolare Ecumenica',
                   'Il Patto fondativo della Rete APE: sei principi, peso paritario, un Albo pubblico. Chi lo firma non entra in un progetto altrui: ne diventa co-fondatore.',
                   'images/rete-ape-anteprima.jpg'),
    'attualita.html': ('Attualità: le notizie lette con la domanda dell’APE | Assemblea Popolare Ecumenica',
                       'Le notizie del giorno lette con una sola domanda: dopo il voto, quanto contano i cittadini? Oggi: la discussione su chi conta di più nel centrosinistra.',
                       'images/ape-anteprima-domanda.jpg'),
    'albo.html': ('Albo dei co-fondatori della Rete APE',
                  'L&#x27;Albo dei co-fondatori della Rete APE: chi ha firmato il Patto fondativo, in ordine alfabetico, senza primi e senza ultimi.',
                  'images/rete-ape-anteprima.jpg'),
}


def pagina_propria(uscita, titolo, desc, anteprima):
    corpo = open(QUI + '_contenuti/' + uscita, encoding='utf-8').read()
    if '__ANON__' in corpo:
        # la chiave anon PUBBLICA di Supabase, la stessa gia' in chiaro in mappa.html di PA
        k = re.search(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', open(PA + 'mappa.html', encoding='utf-8').read())
        if not k:
            stop('non trovo la chiave anon in mappa.html')
        corpo = corpo.replace('__ANON__', k.group(0))
    scrivi_pagina(uscita, titolo, desc, anteprima, corpo, '', 'da _contenuti')


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
    for uscita, (titolo, desc, anteprima) in PAGINE_PROPRIE.items():
        pagina_propria(uscita, titolo, desc, anteprima)
    oggi = datetime.date.today().isoformat()
    voci = ''.join(f'<url><loc>{SITO}{"" if p == "index.html" else p}</loc><lastmod>{oggi}</lastmod></url>\n'
                   for p in list(PAGINE) + ['progetto.html'] + list(PAGINE_PROPRIE))
    open(QUI + 'sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + voci + '</urlset>\n')
    open(QUI + 'robots.txt', 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITO}sitemap.xml\n')
    # Il file CNAME dice a GitHub Pages di servire il sito sul dominio. Finche' i DNS di Aruba non
    # puntano a GitHub, con il CNAME il sito sarebbe IRRAGGIUNGIBILE: si scrive solo con --dominio.
    # 03/10/2026: il dominio e' collegato (commit ca2b879). Un costruisci.py lanciato senza --dominio cancellava il CNAME
    # e al push il sito sarebbe diventato irraggiungibile: ora il CNAME si scrive SEMPRE.
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
