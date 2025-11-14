/* Navigation toggle + form validation */
(function () {
  const qs = (s, r = document) => r.querySelector(s);
  const qsa = (s, r = document) => Array.from(r.querySelectorAll(s));

  const navList = qs('.nav-list');
  const toggle = qs('.nav-toggle');
  const yearEl = qs('#year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  const mql = window.matchMedia('(max-width: 768px)');
  const isMobile = () => mql.matches;

  function setMenuA11y() {
    if (!navList) return;
    if (isMobile()) {
      const isOpen = navList.classList.contains('open');
      navList.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
    } else {
      navList.removeAttribute('aria-hidden');
    }
  }

  function closeMenu() {
    if (!navList) return;
    navList.classList.remove('open');
    if (toggle) {
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Open navigation menu');
    }
    setMenuA11y();
  }

  function openMenu() {
    if (!navList) return;
    navList.classList.add('open');
    if (toggle) {
      toggle.setAttribute('aria-expanded', 'true');
      toggle.setAttribute('aria-label', 'Close navigation menu');
    }
    setMenuA11y();
  }

  function initNav() {
    if (!(toggle && navList)) return;

    // Ensure initial accessible label/state
    toggle.setAttribute('aria-label', 'Open navigation menu');

    // Initial a11y state (especially on mobile)
    setMenuA11y();

    toggle.addEventListener('click', () => {
      const isOpen = navList.classList.contains('open');
      isOpen ? closeMenu() : openMenu();
    });

    // Close on outside click (only if clicking outside the menu or toggle)
    document.addEventListener('click', (e) => {
      if (!navList.classList.contains('open')) return;
      const target = e.target;
      const clickedInsideMenu = navList.contains(target);
      const clickedToggle = toggle.contains(target);
      if (!clickedInsideMenu && !clickedToggle) closeMenu();
    });

    // Close on ESC
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeMenu();
    });

    // Close when navigating via link (mobile)
    qsa('.nav-list a').forEach((a) => {
      a.addEventListener('click', () => closeMenu());
    });

    // Update a11y on viewport changes and ensure closed state on desktop
    if (typeof mql.addEventListener === 'function') {
      mql.addEventListener('change', () => {
        if (!isMobile()) {
          closeMenu();
          if (navList) navList.removeAttribute('aria-hidden');
        } else {
          setMenuA11y();
        }
      });
    } else if (typeof mql.addListener === 'function') {
      mql.addListener(() => {
        if (!isMobile()) {
          closeMenu();
          if (navList) navList.removeAttribute('aria-hidden');
        } else {
          setMenuA11y();
        }
      });
    }

    // Also close if resized beyond breakpoint via window resize (fallback)
    let lastW = window.innerWidth;
    window.addEventListener('resize', () => {
      const w = window.innerWidth;
      if (w !== lastW && w > 768) {
        closeMenu();
        if (navList) navList.removeAttribute('aria-hidden');
      }
      lastW = w;
    });
  }

  initNav();

  // Enhance aria-current based on path (in case of server differences)
  try {
    const path = location.pathname.split('/').pop() || 'index.html';
    qsa('.nav-list a').forEach((a) => {
      const href = a.getAttribute('href');
      if (href === path) {
        a.setAttribute('aria-current', 'page');
      } else {
        if (a.hasAttribute('aria-current')) a.removeAttribute('aria-current');
      }
    });
  } catch (e) {}

  // Contact form validation (only runs on contact page)
  const form = qs('#contact-form');
  if (form) {
    const nameInput = qs('#name', form);
    const emailInput = qs('#email', form);
    const messageInput = qs('#message', form);
    const statusEl = qs('#form-status', form.parentElement || form);

    function setError(input, message) {
      const id = input.getAttribute('id');
      const err = qs('#' + id + '-error');
      if (err) {
        err.textContent = message;
      }
      input.setAttribute('aria-invalid', 'true');
    }

    function clearError(input) {
      const id = input.getAttribute('id');
      const err = qs('#' + id + '-error');
      if (err) err.textContent = '';
      input.removeAttribute('aria-invalid');
    }

    function validateEmail(v) {
      // Simple email check
      return /^(^[^\s@]+)@([^\s@]+)\.([^\s@]{2,})$/.test(v);
    }

    function validate() {
      let ok = true;
      const invalid = [];
      // Name
      if (!nameInput.value.trim()) {
        setError(nameInput, 'Please enter your name.');
        ok = false;
        invalid.push(nameInput);
      } else {
        clearError(nameInput);
      }
      // Email
      if (!emailInput.value.trim()) {
        setError(emailInput, 'Please enter your email.');
        ok = false;
        invalid.push(emailInput);
      } else if (!validateEmail(emailInput.value.trim())) {
        setError(emailInput, 'Please enter a valid email address.');
        ok = false;
        invalid.push(emailInput);
      } else {
        clearError(emailInput);
      }
      // Message
      const msg = messageInput.value.trim();
      if (!msg) {
        setError(messageInput, 'Please enter a message.');
        ok = false;
        invalid.push(messageInput);
      } else if (msg.length < 10) {
        setError(messageInput, 'Message should be at least 10 characters.');
        ok = false;
        invalid.push(messageInput);
      } else {
        clearError(messageInput);
      }
      return { ok, firstInvalid: invalid[0] };
    }

    // Real-time clearing on input
    [nameInput, emailInput, messageInput].forEach((el) => {
      el.addEventListener('input', () => {
        clearError(el);
        if (statusEl) {
          statusEl.hidden = true;
          statusEl.textContent = '';
          statusEl.classList.remove('error', 'success');
        }
      });
    });

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const { ok, firstInvalid } = validate();
      if (!ok) {
        if (statusEl) {
          statusEl.hidden = false;
          statusEl.textContent = 'Please fix the errors below and try again.';
          statusEl.classList.remove('success');
          statusEl.classList.add('error');
        }
        if (firstInvalid && typeof firstInvalid.focus === 'function') {
          firstInvalid.focus();
        }
        return;
      }
      // Success state (no backend request)
      if (statusEl) {
        statusEl.hidden = false;
        statusEl.textContent = 'Thanks! Your message is ready to be sent (demo only).';
        statusEl.classList.remove('error');
        statusEl.classList.add('success');
      }
      form.reset();
      [nameInput, emailInput, messageInput].forEach((el) => clearError(el));
    });
  }
})();
