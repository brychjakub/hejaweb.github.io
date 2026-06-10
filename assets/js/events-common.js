(function () {
  const API_BASE = 'https://hejaboys.pythonanywhere.com/api';
  const PUBLIC_EVENTS_API = `${API_BASE}/akce?public=true`;

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

  function publicUpcomingEvents(events, now = new Date()) {
    return events
      .filter((event) => isPublicEvent(event) && toEventDayEnd(event) >= now)
      .sort((a, b) => toEventDate(a) - toEventDate(b));
  }

  function splitPublicEvents(events, now = new Date()) {
    const current = [];
    const past = [];

    events.filter(isPublicEvent).forEach((event) => {
      if (toEventDayEnd(event) >= now) current.push(event);
      else past.push(event);
    });

    current.sort((a, b) => toEventDate(a) - toEventDate(b));
    past.sort((a, b) => toEventDate(b) - toEventDate(a));

    return { current, past };
  }

  function renderDescription(description, options = {}) {
    if (!description) return '';

    const {
      className = 'event-description',
      prefix = '<br/>',
      linkStyle = ''
    } = options;

    return `${prefix}<span class="${escapeHtml(className)}">${parseLinks(description, { linkStyle })}</span>`;
  }

  function renderEventSummary(event, options = {}) {
    const {
      timePrefix = ' v ',
      locationPrefix = ', ',
      descriptionPrefix = '<br/>',
      ctaHref = '',
      ctaText = '',
      ctaSuffix = ''
    } = options;

    const time = event.cas ? `${timePrefix}${escapeHtml(event.cas)}` : '';
    const location = event.misto ? `${locationPrefix}${escapeHtml(event.misto)}` : '';
    const description = renderDescription(event.popis, { prefix: descriptionPrefix });
    const cta = ctaHref && ctaText ? `<br/><a href="${escapeHtml(ctaHref)}">${escapeHtml(ctaText)}</a>${escapeHtml(ctaSuffix)}` : '';

    return `
      <strong>${escapeHtml(event.nazev)}</strong><br/>
      ${formatDate(event.datum)}${time}${location}${description}${cta}
    `;
  }

  window.HejaEvents = {
    API_BASE,
    PUBLIC_EVENTS_API,
    isPublicEvent,
    toEventDate,
    toEventDayEnd,
    formatDate,
    escapeHtml,
    parseLinks,
    publicUpcomingEvents,
    splitPublicEvents,
    renderDescription,
    renderEventSummary
  };
})();
