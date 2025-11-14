# Hello Kevin — Landing Page

How to view
- Download these files and open index.html in any modern browser (Chrome, Firefox, Safari, Edge).

What you get
- Exact text "Hello Kevin" inside an <h1>, centered horizontally and vertically.
- Responsive headline via clamp(); minimum 32px on small screens, scales up on larger viewports.
- Clean, modern design with neutral background, ample whitespace, and high contrast.
- Light/Dark theme support (respects prefers-color-scheme).
- Accessible and semantic: <html lang="en">, <main>, <h1>, and viewport meta.
- No JavaScript or web fonts; fast to load and no build step required.

Testing checklist
- Content: The page shows exactly "Hello Kevin" (case and spacing exact).
- Centering: Text remains centered both vertically and horizontally at 320px, 375px, 768px, 1024px, 1440px.
- Responsiveness: Headline is large and scales between small and large screens.
- Contrast: Meets WCAG AA (>= 4.5:1) in both light and dark themes.
- No overflow: No horizontal scrolling at common breakpoints.
- Cross-browser: Renders correctly in Chrome, Firefox, Safari, and Edge.

Notes
- The layout uses modern viewport units with fallbacks (vh, dvh, svh) to keep the headline centered without jumpiness on mobile address bars.
- To customize the text, edit the <h1> content in index.html.
