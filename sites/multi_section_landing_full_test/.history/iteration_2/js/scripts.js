(() => {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Update year in footer
  const y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();

  const headerEl = document.querySelector('.site-header');
  function setHeaderOffsetVar() {
    const offset = headerEl ? headerEl.offsetHeight + 8 : 72; // 8px breathing room
    document.documentElement.style.setProperty('--header-offset', offset + 'px');
  }
  setHeaderOffsetVar();

  // Smooth scroll for internal links with sticky header offset
  function isInternalHashLink(a) {
    return a instanceof HTMLAnchorElement && a.getAttribute('href')?.startsWith('#') && a.getAttribute('href') !== '#';
  }

  function focusSection(target) {
    if (!target) return;
    const prevTabindex = target.getAttribute('tabindex');
    if (prevTabindex === null) target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
    if (prevTabindex === null) {
      const onBlur = () => { target.removeAttribute('tabindex'); target.removeEventListener('blur', onBlur); };
      target.addEventListener('blur', onBlur);
    }
  }

  function scrollToTarget(target, instant = false) {
    if (!target) return;
    const offset = headerEl ? headerEl.offsetHeight + 8 : 72;
    const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
    const doInstant = instant || prefersReduced;
    if (doInstant) {
      window.scrollTo(0, Math.max(0, top));
      focusSection(target);
    } else {
      window.scrollTo({ top: Math.max(0, top), left: 0, behavior: 'smooth' });
      setTimeout(() => focusSection(target), 200);
    }
  }

  document.addEventListener('click', (e) => {
    if (e.defaultPrevented) return;
    const link = e.target instanceof Element ? e.target.closest('a') : null;
    if (!link || !isInternalHashLink(link)) return;

    // Respect user intent to open in new tab/window or use middle/right click
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

    const id = link.getAttribute('href').slice(1);
    const target = document.getElementById(id);
    if (!target) return;

    // Special-case skip link: move focus instantly without smooth scrolling
    if (link.classList.contains('skip-link')) {
      e.preventDefault();
      scrollToTarget(target, true);
      return;
    }

    e.preventDefault();
    scrollToTarget(target);
  });

  // Adjust anchor position on initial load if URL has a hash
  if (location.hash && location.hash.length > 1) {
    const target = document.getElementById(location.hash.slice(1));
    if (target) {
      requestAnimationFrame(() => scrollToTarget(target, prefersReduced));
    }
  }

  // FAQ accordion (ARIA) + optional roving focus between questions
  const faqButtons = document.querySelectorAll('.faq-question');

  function togglePanel(btn) {
    const expanded = btn.getAttribute('aria-expanded') === 'true';
    const panelId = btn.getAttribute('aria-controls');
    const panel = panelId ? document.getElementById(panelId) : null;
    if (!panel) return;
    btn.setAttribute('aria-expanded', String(!expanded));
    panel.hidden = expanded; // show when not expanded
  }

  const btnList = Array.from(faqButtons);
  btnList.forEach((btn, index) => {
    btn.addEventListener('click', () => togglePanel(btn));

    btn.addEventListener('keydown', (e) => {
      const { key } = e;
      // Space toggles; Enter activates button natively
      if (key === ' ' || key === 'Spacebar') {
        e.preventDefault();
        togglePanel(btn);
        return;
      }
      // Roving focus across FAQ questions
      if (key === 'ArrowDown' || key === 'ArrowUp' || key === 'Home' || key === 'End') {
        e.preventDefault();
        let nextIndex = index;
        if (key === 'ArrowDown') nextIndex = (index + 1) % btnList.length;
        if (key === 'ArrowUp') nextIndex = (index - 1 + btnList.length) % btnList.length;
        if (key === 'Home') nextIndex = 0;
        if (key === 'End') nextIndex = btnList.length - 1;
        btnList[nextIndex]?.focus();
      }
    });
  });

  // Friendly client-side form messaging while relying on native validation
  const form = document.getElementById('contact-form');
  const hint = document.getElementById('form-hint');
  if (form) {
    function describeInvalidField(el) {
      if (!el || !hint) return;
      // Compose a friendly message using the label text if available
      const label = el.id ? form.querySelector(`label[for="${el.id}"]`) : null;
      const fieldName = label ? label.textContent?.replace('*', '').trim() : el.name || 'This field';
      hint.textContent = `${fieldName} needs attention. Please check and try again.`;
      el.setAttribute('aria-describedby', 'form-hint');
      el.setAttribute('aria-invalid', 'true');
    }

    form.addEventListener('invalid', (e) => {
      const el = e.target;
      if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
        describeInvalidField(el);
      }
    }, true);

    form.addEventListener('input', (e) => {
      const el = e.target;
      if (hint) hint.textContent = '';
      if ((el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement)) {
        if (el.checkValidity()) {
          el.removeAttribute('aria-invalid');
          if (el.getAttribute('aria-describedby') === 'form-hint') {
            el.removeAttribute('aria-describedby');
          }
          if (hint) hint.textContent = '';
        }
      }
    });

    form.addEventListener('submit', (e) => {
      const hp = form.querySelector('#website');
      if (hp && hp.value.trim() !== '') {
        e.preventDefault();
        if (hint) hint.textContent = 'Submission blocked. Please remove unexpected input and try again.';
        return;
      }

      if (!form.checkValidity()) {
        // Let browser enforce and display native messages
        e.preventDefault();
        if (hint) hint.textContent = 'Please fill in the required fields (Name, Email, Message).';
        form.reportValidity();
        // Focus the first invalid control for convenience
        const firstInvalid = form.querySelector(':invalid');
        if (firstInvalid) {
          if (firstInvalid instanceof HTMLInputElement || firstInvalid instanceof HTMLTextAreaElement) {
            describeInvalidField(firstInvalid);
            firstInvalid.focus();
          }
        }
      } else {
        // Demo only: prevent navigation and show success message
        e.preventDefault();
        if (hint) hint.textContent = 'Thanks! Your message was prepared for sending.';
      }
    });
  }

  // Accessibility enhancement: mark current section in navs with aria-current
  const navLinks = Array.from(document.querySelectorAll('nav a[href^="#"]'));
  const sections = ['hero', 'features', 'pricing', 'testimonials', 'faq', 'contact']
    .map(id => document.getElementById(id))
    .filter(Boolean);

  function setCurrent(id) {
    navLinks.forEach(a => {
      const hrefId = a.getAttribute('href')?.slice(1);
      if (hrefId === id) {
        a.setAttribute('aria-current', 'location');
      } else {
        a.removeAttribute('aria-current');
      }
    });
  }

  function updateCurrent() {
    const offset = headerEl ? headerEl.offsetHeight + 8 : 72;
    let currentId = sections[0]?.id || '';
    let currentTop = -Infinity;
    sections.forEach(sec => {
      const rect = sec.getBoundingClientRect();
      const top = rect.top - offset;
      if (top <= 1 && top > currentTop) {
        currentTop = top;
        currentId = sec.id;
      }
    });
    setCurrent(currentId);
  }

  let ticking = false;
  function onScrollOrResize() {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(() => { updateCurrent(); ticking = false; });
    }
  }

  updateCurrent();
  window.addEventListener('scroll', onScrollOrResize, { passive: true });
  window.addEventListener('resize', () => { setHeaderOffsetVar(); onScrollOrResize(); });
})();
