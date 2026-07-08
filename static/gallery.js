// VARQ demo gallery — driven by manifest.json
let DATA = null;
let cur = { model: null, bit: null, speed: 1.5 };

const $ = (s, r = document) => r.querySelector(s);

async function init() {
  const res = await fetch('manifest.json');
  DATA = await res.json();
  cur.model = DATA.models[0].id;
  renderModelTabs();
  selectModel(cur.model);

  // playback speed buttons
  document.querySelectorAll('.speed-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      cur.speed = parseFloat(btn.dataset.speed);
      document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('#gallery video').forEach(v => { v.playbackRate = cur.speed; });
    });
  });

  // navbar scroll shadow + smooth scroll
  window.addEventListener('scroll', () => {
    $('.navbar').classList.toggle('scrolled', window.scrollY > 50);
  });
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const t = document.querySelector(a.getAttribute('href'));
      if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    });
  });
}

function model(id) { return DATA.models.find(m => m.id === id); }

function renderModelTabs() {
  const wrap = $('#model-tabs');
  wrap.innerHTML = '';
  DATA.models.forEach(m => {
    const b = document.createElement('button');
    b.className = 'pill' + (m.id === cur.model ? ' active' : '');
    b.textContent = m.label;
    b.onclick = () => selectModel(m.id);
    wrap.appendChild(b);
  });
}

function selectModel(id) {
  cur.model = id;
  const m = model(id);
  // keep bit if still available, else first
  cur.bit = m.bits.includes(cur.bit) ? cur.bit : m.bits[0];
  document.querySelectorAll('#model-tabs .pill').forEach(p =>
    p.classList.toggle('active', p.textContent === m.label));
  $('#model-task').textContent = m.task;
  renderBitTabs();
  $('#speed-control').style.display = m.type === 'video' ? 'flex' : 'none';
  renderGallery();
}

function renderBitTabs() {
  const m = model(cur.model);
  const wrap = $('#bit-tabs');
  wrap.innerHTML = '';
  m.bits.forEach(q => {
    const b = document.createElement('button');
    b.className = 'pill' + (q === cur.bit ? ' active' : '');
    b.textContent = m.bitLabels[q];
    b.onclick = () => { cur.bit = q; renderBitTabs(); renderGallery(); };
    wrap.appendChild(b);
  });
}

function renderGallery() {
  const m = model(cur.model);
  const samples = m.samples[cur.bit] || [];
  const g = $('#gallery');
  g.innerHTML = '';

  samples.forEach((s, i) => {
    const row = document.createElement('div');
    row.className = 'cmp-row';

    if (s.prompt) {
      const p = document.createElement('p');
      p.className = 'cmp-prompt';
      p.innerHTML = '&ldquo;' + escapeHtml(s.prompt) + '&rdquo;';
      row.appendChild(p);
    } else {
      const p = document.createElement('p');
      p.className = 'cmp-prompt cmp-prompt-plain';
      p.textContent = m.task + ' — sample ' + (i + 1);
      row.appendChild(p);
    }

    const grid = document.createElement('div');
    grid.className = 'cmp-grid cols-' + m.methods.length;

    m.methods.forEach(meth => {
      const src = s.media[meth];
      const isOurs = meth === 'VARQ';
      const cell = document.createElement('div');
      cell.className = 'cmp-cell' + (isOurs ? ' ours' : '');

      const h = document.createElement('h4');
      h.innerHTML = m.methodLabels[meth] + (isOurs ? ' <span class="badge">Ours</span>' : '');
      cell.appendChild(h);

      const media = document.createElement('div');
      media.className = 'media ' + m.type;
      if (src) {
        if (m.type === 'video') {
          const v = document.createElement('video');
          v.src = src; v.autoplay = true; v.loop = true; v.muted = true;
          v.playsInline = true; v.controls = true; v.preload = 'metadata';
          v.addEventListener('loadedmetadata', () => { v.playbackRate = cur.speed; });
          media.appendChild(v);
        } else {
          const img = document.createElement('img');
          img.src = src; img.loading = 'lazy'; img.alt = m.methodLabels[meth];
          media.appendChild(img);
        }
      } else {
        media.classList.add('missing');
        media.textContent = 'n/a';
      }
      cell.appendChild(media);
      grid.appendChild(cell);
    });

    row.appendChild(grid);

    if (s.caption) {
      const c = document.createElement('p');
      c.className = 'cmp-caption';
      c.innerHTML = s.caption;
      row.appendChild(c);
    }

    g.appendChild(row);
  });

  if (!samples.length) g.innerHTML = '<p class="model-task">No samples for this setting.</p>';
}

function escapeHtml(t) {
  const d = document.createElement('div'); d.textContent = t; return d.innerHTML;
}

function copyCode(button) {
  const code = button.closest('.code-block').querySelector('code');
  navigator.clipboard.writeText(code.textContent).then(() => {
    const o = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check"></i> Copied!';
    setTimeout(() => { button.innerHTML = o; }, 2000);
  });
}

document.addEventListener('DOMContentLoaded', init);
