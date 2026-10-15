(() => {
  'use strict';
  const languageKey = () => ({'zh-CN':'zh','zh-Hant':'zh-Hant',ja:'ja',ko:'ko'}[document.documentElement.lang] || 'en');
  const copy = () => translations[languageKey()];
  const menuLabels = {en:'Open navigation',zh:'打开导航','zh-Hant':'開啟導覽',ja:'ナビゲーションを開く',ko:'탐색 열기'};
  const navigation = document.querySelector('#primary-links');
  const menu = document.querySelector('.nav-toggle');
  const closeMenu = () => {
    navigation.classList.remove('is-open');
    menu.setAttribute('aria-expanded','false');
  };
  menu.addEventListener('click', () => {
    const expanded = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded',String(expanded));
    navigation.classList.toggle('is-open', expanded);
  });
  navigation.addEventListener('click', event => { if (event.target.closest('a')) closeMenu(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') { closeMenu(); menu.focus(); } });

  const dialog = document.createElement('dialog');
  dialog.className = 'screenshot-dialog';
  dialog.setAttribute('aria-labelledby','screenshot-caption');
  const close = document.createElement('button');
  close.type = 'button'; close.className = 'screenshot-close'; close.textContent = '×';
  const figure = document.createElement('figure');
  const photo = document.createElement('img');
  const caption = document.createElement('figcaption'); caption.id = 'screenshot-caption';
  figure.append(photo,caption); dialog.append(close,figure); document.body.append(dialog);
  let activeImage = null;
  let opener = null;
  let previousOverflow = '';
  function updateLabels() {
    const t = copy();
    menu.setAttribute('aria-label',menuLabels[languageKey()]);
    close.setAttribute('aria-label',t['zoom.close']);
    document.querySelectorAll('[data-screen]').forEach(image => {
      const trigger = image.closest('.screenshot-trigger');
      if (trigger) trigger.setAttribute('aria-label',`${t['zoom.open']}: ${image.alt}`);
    });
    if (activeImage) {
      photo.src = activeImage.src; photo.alt = activeImage.alt;
      caption.textContent = activeImage.dataset.screen === 'mac-overview' ? t['mac.caption'] : t['zoom.caption'];
    }
  }
  document.querySelectorAll('[data-screen]').forEach(image => {
    const trigger = document.createElement('button');
    trigger.type = 'button'; trigger.className = 'screenshot-trigger';
    trigger.setAttribute('aria-haspopup','dialog');
    image.before(trigger); trigger.append(image);
    trigger.addEventListener('click', () => {
      activeImage = image; opener = trigger; updateLabels();
      previousOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden'; dialog.showModal(); close.focus();
    });
  });
  close.addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    const rect = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
  });
  dialog.addEventListener('close', () => {
    document.body.style.overflow = previousOverflow; activeImage = null;
    opener?.focus();
  });
  document.addEventListener('monoproxy-language', updateLabels);
  updateLabels();
})();
