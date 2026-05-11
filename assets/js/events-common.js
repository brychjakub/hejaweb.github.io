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

  function parseLinks(text, options = {}) {
    if (!text) return '';

    const {
      linkStyle = '',
      defaultLabel = 'Odkaz'
    } = options;

    const urlRegex = /(https?:\/\/[^\s]+)/g;

    return text.replace(urlRegex, (url) => {
      let safeLabel = defaultLabel;
      try {
        const parsed = new URL(url);
        safeLabel = parsed.hostname.replace(/^www\./, '') + (parsed.pathname && parsed.pathname !== '/' ? '/…' : '');
      } catch (_) {}

      const styleAttr = linkStyle ? ` style="${linkStyle}"` : '';
      return `<a href="${url}" target="_blank" rel="noopener noreferrer"${styleAttr}>${safeLabel}</a>`;
    });
  }

  window.HejaEvents = {
    isPublicEvent,
    toEventDate,
    toEventDayEnd,
    formatDate,
    parseLinks
  };
})();
