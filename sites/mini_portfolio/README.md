# Modern Portfolio

A clean, modern, and accessible three-page portfolio with a responsive navigation bar, light/dark theme, and a contact form with front-end validation.

Features
- Three pages with shared layout and styles: Home, Projects, Contact
- Responsive top navigation with hamburger menu on small screens
- Light/dark theme via CSS prefers-color-scheme
- Accessible structure: landmarks, skip link, labels, live regions, visible focus states
- Contact form with inline validation and success message (no backend)

File structure
- index.html — Home with hero intro
- projects.html — Projects grid (three cards)
- contact.html — Contact form (name, email, message)
- style.css — Design tokens, layout, components, responsive styles, dark mode
- script.js — Hamburger menu toggle, close on outside click/ESC, contact form validation
- README.md — This guide

Quick start (local)
1. Download all files into the same folder.
2. Open index.html in your browser (double-click or drag into a browser window). No server is required.

How to test
- Navigation links
  - From any page, use the top nav to move between Home, Projects, and Contact. The current page is indicated for assistive tech via aria-current.
- Responsive navigation
  - Resize the browser below ~768px to reveal the hamburger.
  - Click the hamburger to open/close. Click outside the menu or press ESC to close. Choosing a menu item also closes it.
  - The button updates aria-expanded and its accessible name between "Open navigation menu" and "Close navigation menu".
- Keyboard behavior
  - Press Tab to focus the Skip to content link, then the nav toggle (on small screens), nav links, and page content in logical order.
  - Use Enter/Space to activate the hamburger and links. Visible focus outlines are provided.
- Theme switching
  - The site follows your system theme via prefers-color-scheme. Switch your OS/browser between light and dark mode (or emulate in dev tools) to observe style changes.
- Contact form validation
  - On the Contact page, try submitting with empty fields or an invalid email (e.g., test@). Inline error messages appear under fields.
  - When all fields are valid (message ≥ 10 characters), a success message appears and the form resets. No network request is made.

Accessibility and quality checklist
- HTML: <!DOCTYPE html>, <html lang="en">, descriptive <title>, and responsive <meta viewport> are present.
- Landmarks: header, nav, main, footer; skip link for keyboard users.
- ARIA: hamburger button includes aria-controls and aria-expanded; menu visibility is reflected with aria-hidden on small screens; form status uses a polite live region.
- Contrast: text and interactive elements target WCAG AA in light and dark modes.
- Interaction: no keyboard traps; ESC/outside click close the mobile menu; visible focus styles.
- Layout: responsive grid/cards and no horizontal scrolling at 360px, 768px, 1366px.

Customization
- Open style.css and adjust design tokens in :root to update the theme globally.
  - Colors: --bg, --surface, --text, --muted, --primary, --link, --border
  - Radii: --radius-sm, --radius, --radius-lg
  - Spacing: --space-* scale
  - Shadows: --shadow-1, --shadow-2
  - Layout width: --max-width
- The dark theme overrides live under @media (prefers-color-scheme: dark).

Notes
- JavaScript is required for the mobile navigation toggle and form validation.
- The menu highlight (aria-current) is set per page in HTML and also enhanced by script.js based on the current URL.
- Project card "Learn more" links scroll to each card's in-page anchor.

Browser support
- Built for modern evergreen browsers (Chrome, Edge, Firefox, Safari). Graceful fallbacks are included where newer CSS features (e.g., color-mix) are used.
