#!/usr/bin/env python3
"""Le immagini proprie del sito APE (30/09/2026): nessun marchio dei promotori.

  images/angelo-nicotra-volto.webp   solo il viso, ritagliato dal ritratto dell'organigramma di PA
  images/ape-anteprima.jpg           scheda 1200x630 per Facebook/WhatsApp — pagina del progetto
  images/rete-ape-anteprima.jpg      idem — pagina della Rete

Si rilancia solo se cambia un titolo o il ritratto.   (interprete con PIL: envs/comfyui)
"""
import os
from PIL import Image, ImageDraw, ImageFont

QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
PA = os.path.dirname(QUI.rstrip('/')) + '/partecipazioneattiva/'
CAR = PA + '_tools/caratteri/'
os.makedirs(QUI + 'images', exist_ok=True)

# 1 · il viso: dal ritratto 500x750, quadrato su testa e spalle (niente scritte del manifesto)
r = Image.open(PA + 'images/organigramma/angelo-nicotra-finale.webp').convert('RGB')
r.crop((95, 78, 315, 298)).resize((300, 300), Image.LANCZOS).save(QUI + 'images/angelo-nicotra-volto.webp', quality=88)

INCH, CHIARO, MIELE = (14, 38, 58), (236, 243, 248), (255, 205, 60)


def scheda(nome, occhiello, titolo, righe):
    W, H = 1200, 630
    im = Image.new('RGB', (W, H), INCH)
    d = ImageDraw.Draw(im)
    for y in range(H):                                   # sfumatura verticale leggera
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * k) for a, b in zip((20, 52, 78), (10, 28, 44))))
    F = lambda peso, corpo: ImageFont.truetype(f'{CAR}montserrat-{peso}-latin.ttf', corpo)
    M = lambda corpo: ImageFont.truetype(f'{CAR}merriweather-700-latin.ttf', corpo)
    d.rectangle([80, 96, 92, 534], fill=MIELE)           # filo color miele: l'ape
    d.text((124, 92), occhiello, font=F(700, 34), fill=MIELE)
    d.text((118, 140), 'APE', font=F(900, 190), fill=(255, 255, 255))
    d.text((124, 352), titolo, font=M(50), fill=(255, 255, 255))
    y = 432
    for riga in righe:
        d.text((124, y), riga, font=F(400, 34), fill=CHIARO)
        y += 46
    d.text((124, 548), 'assembleapopolareecumenica.it', font=F(700, 30), fill=MIELE)
    im.save(QUI + nome, quality=90)
    im.resize((400, 210), Image.LANCZOS).save(QUI + '_tools/prova_' + os.path.basename(nome))


scheda('images/ape-anteprima.jpg', 'OLTRE LA DEMOCRAZIA DELEGATIVA', 'Assemblea Popolare Ecumenica',
       ['Un canale permanente di voce dei cittadini.', 'Aperto a tutti.'])
scheda('images/rete-ape-anteprima.jpg', 'RETE APE', 'Assemblea Popolare Ecumenica',
       ['Cittadini, associazioni, movimenti, comitati:', 'si aderisce con peso paritario.'])
print('immagini fatte')
