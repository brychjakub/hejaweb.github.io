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

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadFooter);
  } else {
    loadFooter();
  }
})();
