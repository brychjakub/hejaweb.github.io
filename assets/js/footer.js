(function(){
  function replaceFooter(markup){
    var temp = document.createElement('div');
    temp.innerHTML = markup;
    var newFooter = temp.querySelector('footer#footer');
    if(!newFooter) return;
    var existing = document.querySelector('footer#footer');
    if (existing) {
      existing.replaceWith(newFooter);
    } else {
      var wrapper = document.getElementById('wrapper') || document.body;
      wrapper.appendChild(newFooter);
    }
  }

  function loadFooter(){
    fetch('footer.html', { cache: 'no-cache' })
      .then(function(r){ return r.text(); })
      .then(function(html){ replaceFooter(html); })
      .catch(function(){ /* silent fail */ });
  }

  // --- Google Analytics (gtag) auto-loader ---
  function getGAIdFromMeta(){
    var tag = document.querySelector('meta[name="ga-measurement-id"]');
    var id = tag && tag.getAttribute('content');
    return (id && id.trim()) || '';
  }

  function injectGA(id){
    if (!id || window.__gaLoaded) return;
    window.__gaLoaded = true;
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id);
    document.head.appendChild(s);

    window.dataLayer = window.dataLayer || [];
    function gtag(){ dataLayer.push(arguments); }
    window.gtag = gtag;
    gtag('js', new Date());
    gtag('config', id);
  }

  function tryLoadGAFromConfig(){
    if (window.__gaLoaded) return;
    fetch('assets/ga.json', { cache: 'no-cache' })
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(cfg){
        if (!cfg || !cfg.measurementId) return;
        var id = (cfg.measurementId || '').trim();
        if (id) injectGA(id);
      })
      .catch(function(){ /* silent fail */ });
  }

  function initGA(){
    var id = getGAIdFromMeta();
    if (id) {
      injectGA(id);
    } else {
      tryLoadGAFromConfig();
    }
  }

  function hasCookieConsent(){
    try {
      return localStorage.getItem('heja-cookie-consent') === 'ok';
    } catch (e) {
      return false;
    }
  }

  function saveCookieConsent(){
    try {
      localStorage.setItem('heja-cookie-consent', 'ok');
    } catch (e) {
      /* silent fail */
    }
  }

  function removeCookieNotice(notice){
    if (!notice) return;
    notice.className += ' is-hidden';
    setTimeout(function(){
      if (notice.parentNode) notice.parentNode.removeChild(notice);
    }, 220);
  }

  function showCookieNotice(){
    if (document.getElementById('cookie-notice')) return;

    var notice = document.createElement('div');
    notice.id = 'cookie-notice';
    notice.className = 'cookie-notice';
    notice.setAttribute('role', 'dialog');
    notice.setAttribute('aria-live', 'polite');
    notice.setAttribute('aria-label', 'Upozorneni na cookies');
    notice.innerHTML =
      '<div class="cookie-notice__text">' +
        '<strong>Cookies</strong>' +
        '<span>Pou&#382;&#237;v&#225;me cookies pro m&#283;&#345;en&#237; n&#225;v&#353;t&#283;vnosti pomoc&#237; Google Analytics.</span>' +
      '</div>' +
      '<button type="button" class="primary cookie-notice__button">OK</button>';

    var button = notice.querySelector('button');
    button.addEventListener('click', function(){
      saveCookieConsent();
      initGA();
      removeCookieNotice(notice);
    });

    document.body.appendChild(notice);
  }

  function initCookieConsent(){
    if (hasCookieConsent()) {
      initGA();
      return;
    }

    showCookieNotice();
  }

  function init(){
    loadFooter();
    initCookieConsent();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
