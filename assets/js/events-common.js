(function () {
  function isPublicEvent(event) {
    return Number(event.public) === 1;
  }

  function toEventDate(event) {
    return new Date(`${event.datum}T${event.cas || '23:59'}`);
  }

  function toEventDayEnd(event) {
    return new Date(`${event.datum}T23:59:59`);
  }

  function formatDate(dateValue) {
    return new Date(`${dateValue}T00:00`).toLocaleDateString('cs-CZ');
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, (char) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[char]));
  }

  function parseLinks(text, options = {}) {
    if (!text) return '';

    const {
      linkStyle = '',
      defaultLabel = 'Odkaz'
    } = options;

    const urlRegex = /(https?:\/\/[^\s]+)/g;
    let html = '';
    let lastIndex = 0;
    let match;

    while ((match = urlRegex.exec(text)) !== null) {
      const url = match[0];
      html += escapeHtml(text.slice(lastIndex, match.index));

      let safeLabel = defaultLabel;
      try {
        const parsed = new URL(url);
        safeLabel = parsed.hostname.replace(/^www\./, '') + (parsed.pathname && parsed.pathname !== '/' ? '/…' : '');
      } catch (_) {}

      const styleAttr = linkStyle ? ` style="${escapeHtml(linkStyle)}"` : '';
      html += `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer"${styleAttr}>${escapeHtml(safeLabel)}</a>`;
      lastIndex = match.index + url.length;
    }

    html += escapeHtml(text.slice(lastIndex));
    return html;
  }

  window.HejaEvents = {
    isPublicEvent,
    toEventDate,
    toEventDayEnd,
    formatDate,
    parseLinks
  };
})();
