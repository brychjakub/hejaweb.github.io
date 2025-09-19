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

  function init(){
    loadFooter();
    initGA();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
