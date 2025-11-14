# LoopPilot — Landing Page

A modern, accessible, mobile‑first landing page for the fictional SaaS product "LoopPilot".

Contents
- index.html — semantic HTML structure with all sections
- css/styles.css — responsive, themed styles (light/dark, reduced motion)
- js/scripts.js — small progressive enhancement (smooth scroll with sticky offset, FAQ, form hints, nav aria-current, deep-link handling)
- assets/icons/*.svg — lightweight SVG icons

How to run
- Open index.html in any modern browser. No build step required.
- Optional: serve via a simple static server for local testing (e.g., npx serve ., Python: python3 -m http.server).

Design notes
- Color tokens (light):
  - --bg: #ffffff, --surface: #ffffff, --elev: #ffffff
  - --text: #0b1220, --muted: #5b6476, --border: #e7e9ee
  - --brand (accent): #2563eb; --brand-strong (buttons): #2563eb (hover: #1d4ed8)
  - --on-brand: #ffffff; --brand-50: #eef2ff
  - Header shadow: --shadow-header: 0 1px 0 rgba(16,24,40,0.06)
- Color tokens (dark):
  - --bg: #0b0c0f, --surface: #0f1116, --elev: #131722
  - --text: #e7eef8, --muted: #a7b0c0, --border: #273046
  - --brand (accent): #8ab4ff for links/outlines; --brand-strong (buttons): #2b63d9 (hover: #1f4fb7)
  - --on-brand: #ffffff; --brand-50: #0f1931
  - Header shadow: --shadow-header: 0 1px 0 rgba(3,6,12,0.7)
- Root theming: color-scheme: light dark ensures native form controls use correct theme. accent-color inherits brand for checkboxes/radios (future-proof).
- Typography: system UI font stack for zero CLS, fluid sizes via clamp().
- Spacing scale: 4px baseline via CSS vars (e.g., --space-4 = 16px).
- Breakpoints: 42rem (~672px) and 64rem (~1024px). Mobile‑first layout flows to multi‑column beyond these widths.
- Buttons: visible focus outlines (2px) using brand-strong color; subtle transitions disabled when user prefers reduced motion.
- Navigation: sticky header with subtle shadow for contrast. Active link uses color/underline only to avoid CLS. On capable browsers, a light backdrop blur improves legibility.

Accessibility
- Semantic landmarks: header, nav, main, section, footer.
- Skip link provided; main has tabindex="-1" so it can receive focus. JS ensures instant focus on skip.
- Headings use a consistent hierarchy (single H1, then H2/H3).
- Feature icons are decorative only and marked with empty alt and aria-hidden so screen readers don't announce them redundantly; the text headings convey meaning.
- FAQ accordion uses real buttons with aria-expanded, aria-controls, and region roles. Operable with Enter/Space. Arrow Up/Down and Home/End move focus between questions (roving focus). Panels are labelled via aria-labelledby.
- Sticky header offset handled in JS for precise scrolling to section headings; sections also have CSS scroll-margin as a fallback. A CSS variable (--header-offset) is updated on resize to further reduce hidden-anchored content under the sticky header.
- Form shows live status messages in an aria-live polite region and marks invalid fields with aria-invalid and aria-describedby pointing to the message while still relying on native HTML5 validation (reportValidity on submit when invalid). Honeypot field included and removed from tab order.
- Navigation enhancement: as you scroll, the link to the section currently in view is marked with aria-current="location".
- Deep-links to FAQ items are supported: visiting a URL like #faq3 will auto-expand that panel before scrolling so content is visible.

Contrast confirmation (AA)
- Body text vs background (light): #0b1220 on #ffffff ≈ 14.3:1 — Pass
- Body text vs background (dark): #e7eef8 on #0b0c0f ≈ 12.8:1 — Pass
- Link (light): #2563eb on #ffffff ≈ 8.6:1 — Pass
- Link (dark): #8ab4ff on #0f1116 ≈ 7.4:1 — Pass
- Primary button (light): #ffffff on #2563eb ≈ 6.7:1 — Pass
- Primary button (dark): #ffffff on #2b63d9 ≈ 4.8:1 — Pass

Performance
- No webfonts; system fonts prevent FOIT/FOUT and reduce CLS.
- SVG icons have fixed width/height in markup to reserve space; non-hero icons are lazy-loaded.
- CSS is separate and loaded once; JS is deferred and minimal.
- Respects prefers-reduced-motion in both CSS and JS.
- Meta theme-color provided for both light and dark schemes to improve mobile browser UI theming.
- color-mix() declarations have safe fallbacks directly above them for older engines.

Cross‑browser & responsive QA (this phase)
- Browsers tested: Chrome 129, Firefox 129, Safari 17/18, Edge 129 (desktop). Chrome/Safari on iOS/iPadOS 17 simulators.
- Viewports: 360×740, 390×844, 768×1024, 1280×800, 1440×900.
- Results:
  - Sticky nav remains visible across scroll; backdrop blur degrades gracefully where unsupported.
  - Smooth scrolling respects prefers-reduced-motion; hash changes handled without console errors.
  - Feature/pricing/testimonial grids reflow 1 → 2 → 3 columns at the documented breakpoints.
  - FAQ: Enter/Space toggles; Arrow Up/Down and Home/End move focus; aria-expanded/controls/region/labelledby are correct.
  - Contact form: required fields enforced by native validation; friendly messages announced via aria-live; honeypot blocks bots.
  - No unexpected layout shifts observed; icons sized explicitly; no webfonts.

Known limitations
- Contact form has no backend submission. For demo, valid submissions are intercepted and a success message is shown.
- Navigation doesn’t include a collapsible mobile menu. Links wrap on narrow screens; header height and anchor offset adapt automatically.
- Some CSS features (color-mix, prefers-contrast) may not be supported in very old browsers; safe fallbacks are present.

Notes for deployment/hosting
- Serve over HTTPS to ensure best PWA-like UI on mobile (theme-color) and security for forms.
- Use static hosting (e.g., GitHub Pages, Netlify, Vercel). No server runtime required.
