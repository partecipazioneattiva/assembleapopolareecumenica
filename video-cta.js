/* Pulsanti reali sotto ogni video e a fine video (16/10/2026).
   Un solo file, identico sul sito APE e su quello di PA. Non tocca i video con data-cta="off". */
(function () {
  if (window.__videoCta) return; window.__videoCta = 1;
  var h = location.hostname, p = location.pathname.split('/').pop() || 'index.html';
  var sulleApe = /assembleapopolareecumenica/.test(h);
  var paApe = !sulleApe && /^(ape|video-ape-tocca-a-noi)\.html$/.test(p);
  var CHAT = 'https://chat.whatsapp.com/Kglv6h9DNnV5L3INuDhs7t';
  var FORM_PA = 'https://docs.google.com/forms/d/e/1FAIpQLSdUJHaPB9o6gA7TXHNLNgsKcftZjwCsjepZ3r_C9TH2ODsr3A/viewform';
  var cta;
  if (sulleApe || paApe) {
    cta = { ape: 1, url: sulleApe ? 'rete.html#aderisci' : 'rete-ape.html#aderisci', et: 'Firma il Patto e diventa co-fondatore',
            sotto: 'Diventa co-fondatore della Rete APE', nota: 'Adesione gratuita, alla pari. Si firma il Patto e si conferma via email.', ext: 0 };
  } else {
    cta = { ape: 0, url: FORM_PA, et: 'Iscriviti a Partecipazione Attiva', sotto: 'Iscriviti a Partecipazione Attiva', nota: 'L’iscrizione è gratuita.', ext: 1 };
  }
  var st = document.createElement('style');
  st.textContent =
    '.vc-w{position:relative;display:block}.vc-w video{display:block;width:100%;margin:0!important}' +
    '.vc-f{position:absolute;left:0;top:0;width:100%;height:calc(100% - 44px);z-index:2;background:#0e2a3f;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:10px;box-sizing:border-box;text-align:center;color:#fff;font-family:Montserrat,system-ui,sans-serif;overflow:hidden}' +
    '.vc-f[hidden]{display:none}.vc-f img{height:26%;width:auto;max-width:40%;background:#fff;border-radius:50%}' +
    '.vc-f b{font-size:clamp(.8em,2.6vw,1.05em)}.vc-f em{font-style:normal;color:#e7c25a;font-size:clamp(.75em,2.3vw,.95em)}' +
    '.vc-f a,.vc-b a{display:block;border-radius:30px;color:#fff!important;font-weight:800;text-decoration:none;text-align:center;transition:transform .15s,filter .15s}' +
    '.vc-f a{width:min(92%,340px);padding:9px 8px;font-size:clamp(.72em,2.4vw,.9em)}' +
    '.vc-f a:hover,.vc-f a:focus-visible,.vc-b a:hover,.vc-b a:focus-visible{transform:scale(1.04);filter:brightness(1.12);outline:3px solid #fff;outline-offset:2px}' +
    '.vc-j{background:#d6781e}.vc-wa{background:#25a244}.vc-f small{font-size:clamp(.58em,1.8vw,.68em);color:#b9cbe0;line-height:1.35}' +
    '.vc-b{text-align:center;margin:12px 0 6px;font-family:Montserrat,system-ui,sans-serif}.vc-b a{max-width:440px;margin:8px auto 4px;padding:14px 18px;background:#17507a}.vc-b a.vc-wa{background:#1f8a3b}' +
    '.vc-b span{display:block;font-size:.8em;opacity:.8;max-width:440px;margin:0 auto}';
  document.head.appendChild(st);
  function a(cl, href, t, ext) {
    var e = document.createElement('a'); e.className = cl; e.href = href; e.textContent = t;
    if (ext) { e.target = '_blank'; e.rel = 'noopener'; } return e;
  }
  function blocco(box, href, t, nota, cl, ext) {
    var d = document.createElement('div'); d.className = 'vc-b';
    d.appendChild(a(cl || '', href, t, ext));
    var s = document.createElement('span'); s.textContent = nota; d.appendChild(s); box.appendChild(d);
  }
  var tutti = document.querySelectorAll('video');
  for (var i = 0; i < tutti.length; i++) (function (v) {
    if (v.getAttribute('data-cta') === 'off' || v.closest('.vc-w')) return;
    var w = document.createElement('div'), cs = getComputedStyle(v);
    w.className = 'vc-w'; w.style.maxWidth = cs.maxWidth !== 'none' ? cs.maxWidth : '';
    w.style.margin = cs.marginTop + ' auto ' + cs.marginBottom;
    v.parentNode.insertBefore(w, v); w.appendChild(v);
    var f = document.createElement('div'); f.className = 'vc-f'; f.hidden = true;
    if (cta.ape) {
      var im = document.createElement('img'); im.src = (sulleApe ? '' : '') + 'images/ape-logo-v2.svg'; im.alt = ''; f.appendChild(im);
      var b = document.createElement('b'); b.textContent = 'Assemblea Popolare Ecumenica'; f.appendChild(b);
      var em = document.createElement('em'); em.textContent = 'Dopo il voto, si continua.'; f.appendChild(em);
    } else {
      var b2 = document.createElement('b'); b2.textContent = 'Partecipazione Attiva'; f.appendChild(b2);
    }
    f.appendChild(a('vc-j', cta.url, cta.et, cta.ext));
    if (cta.ape) {
      f.appendChild(a('vc-wa', CHAT, 'Entra nella chat WhatsApp', 1));
      var sm = document.createElement('small'); sm.innerHTML = 'In chat il tuo numero è visibile agli altri partecipanti;<br>l’ingresso viene approvato dagli amministratori.'; f.appendChild(sm);
    }
    w.appendChild(f);
    v.addEventListener('ended', function () { f.hidden = false; });
    v.addEventListener('play', function () { f.hidden = true; });
    v.addEventListener('seeking', function () { if (v.duration && v.currentTime < v.duration - 1) f.hidden = true; });
    var box = document.createElement('div');
    blocco(box, cta.url, cta.sotto + ' →', cta.nota, '', cta.ext);
    if (cta.ape) blocco(box, CHAT, 'Entra nella chat WhatsApp →', 'In chat il tuo numero di telefono è visibile agli altri partecipanti; l’ingresso lo approvano gli amministratori.', 'vc-wa', 1);
    w.parentNode.insertBefore(box, w.nextSibling);
  })(tutti[i]);
})();
