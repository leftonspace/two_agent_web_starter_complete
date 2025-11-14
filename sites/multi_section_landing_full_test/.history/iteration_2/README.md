# LoopPilot — Landing Page

A modern, accessible, mobile‑first landing page for the fictional SaaS product "LoopPilot".

Contents
- index.html — semantic HTML structure with all sections
- css/styles.css — responsive, themed styles (light/dark, reduced motion)
- js/scripts.js — small progressive enhancement (smooth scroll with sticky offset, FAQ, form hints, nav aria-current)
- assets/icons/*.svg — lightweight SVG icons

How to run
- Open index.html in any modern browser. No build step required.
- Optional: serve via a simple static server for local testing (e.g., npx serve ., Python: python3 -m http.server).

Design notes
- Color tokens (light):
  - --bg: #ffffff, --surface: #ffffff, --elev: #ffffff
  - --text: #0b1220, --muted: #5b6476, --border: #e7e9ee
  - --brand (accent): #2563eb
  - --brand-strong (buttons): #2563eb (hover: #1d4ed8)
  - --on-brand: #ffffff
- Color tokens (dark):
  - --bg: #0b0c0f, --surface: #0f1116, --elev: #131722
  - --text: #e7eef8, --muted: #a7b0c0, --border: #273046
  - --brand (accent): #8ab4ff for links/outlines on dark backgrounds
  - --brand-strong (buttons): #2b63d9 (hover: #1f4fb7) to keep button text contrast AA with white
  - --on-brand: #ffffff
- Typography: system UI font stack for zero CLS, fluid sizes via clamp().
- Spacing scale: 4px baseline via CSS vars (e.g., --space-4 = 16px).
- Breakpoints: 42rem (~672px) and 64rem (~1024px). Mobile‑first layout flows to multi‑column beyond these widths.
- Buttons: visible focus outlines (2px) using brand-strong color.
- Navigation: all links are font-weight 600; the active link adds only color/underline to avoid width changes and prevent CLS.

Accessibility
- Semantic landmarks: header, nav, main, section, footer.
- Skip link provided; main has tabindex="-1" so it can receive focus. JS ensures instant focus on skip.
- Headings use a consistent hierarchy (single H1, then H2/H3). Hero headline includes the brand name "LoopPilot".
- FAQ accordion uses real buttons with aria-expanded, aria-controls, and region roles. Operable with Enter/Space. Arrow Up/Down and Home/End move focus between questions (roving focus).
- Sticky header offset handled in JS for precise scrolling to section headings; sections also have CSS scroll-margin as a fallback. A CSS variable (--header-offset) is updated on resize to further reduce hidden-anchored content under the sticky header.
- Form shows live status messages in an aria-live polite region and marks invalid fields with aria-invalid and aria-describedby pointing to the message while still relying on native HTML5 validation (we call reportValidity on submit when invalid).
- Pricing accessibility: the "Most popular" plan is visually highlighted and is also announced via the plan heading (visually-hidden suffix) and an aria-label on the plan card.
- Navigation enhancement: as you scroll, the link to the section currently in view is marked with aria-current="location". If the current item is the Contact button-styled link, we also show a visible border.

Performance
- No webfonts; system fonts prevent FOIT/FOUT and reduce CLS.
- SVG icons have fixed width/height in markup to reserve space; non-hero icons are lazy-loaded.
- CSS is separate and loaded once; JS is deferred and minimal.
- Respects prefers-reduced-motion in both CSS and JS.
- Meta theme-color provided for both light and dark schemes to improve mobile browser UI theming.
- Cross-browser fallbacks added where color-mix() is used (fallback properties precede color-mix declarations).

Cross‑browser & responsive QA notes (latest Chrome, Firefox, Safari, Edge)
- Sticky navigation verified; links smoothly scroll to sections with offset. Users opening links in new tabs/windows (Ctrl/Cmd-click, middle-click) are not intercepted by JS.
- Skip link immediately focuses the main region without animation to avoid repeated navigation for screen readers.
- Feature, pricing, testimonial grids reflow 1 → 2/3 columns at 42rem and 64rem breakpoints.
- FAQ accordion keyboard behavior: Enter/Space toggles; Up/Down/Home/End move between questions.
- Form validation: HTML5 required/type enforced; JS adds friendly messages and aria-invalid/aria-describedby, and uses reportValidity to show native tooltips.
- color-mix() has safe fallbacks (border/background/placeholder). Where unsupported, UI gracefully falls back to solid colors/borders.
- iOS Safari text-size zoom mitigated with -webkit-text-size-adjust: 100%.

Known limitations
- Contact form has no backend submission. For demo, valid submissions are intercepted and a success message is shown; browser native validation still enforces required fields.
- Navigation doesn’t include a collapsible mobile menu. Links may wrap on narrow screens; header height adapts automatically and anchor offset is computed dynamically by JS.

License
- Icons are simple custom SVGs for demo purposes.
