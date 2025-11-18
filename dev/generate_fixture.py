#!/usr/bin/env python3
# dev/generate_fixture.py
"""
Generate a test fixture site for testing the orchestrator.

Creates a minimal static website under sites/fixtures/ with:
- Simple HTML pages
- Basic CSS styles
- Minimal JavaScript
- No AI calls needed - fully deterministic

Useful for testing the system without API costs.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """Generate test fixture site."""
    print("\n" + "=" * 70)
    print("  DEV TOOL: Generate Test Fixture")
    print("=" * 70 + "\n")

    # Create fixtures directory
    project_root = Path(__file__).resolve().parent.parent
    fixtures_dir = project_root / "sites" / "fixtures"

    if fixtures_dir.exists():
        response = input(f"⚠️  {fixtures_dir} already exists. Overwrite? [y/N]: ").strip().lower()
        if response not in ("y", "yes"):
            print("❌ Cancelled.")
            return

        # Clean existing
        import shutil

        shutil.rmtree(fixtures_dir)

    fixtures_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Creating fixture site at: {fixtures_dir}\n")

    # Create HTML files
    print("   Creating index.html...")
    (fixtures_dir / "index.html").write_text(
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fixture Site - Home</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>Test Fixture Website</h1>
        <nav>
            <a href="index.html">Home</a>
            <a href="about.html">About</a>
            <a href="contact.html">Contact</a>
        </nav>
    </header>

    <main>
        <h2>Welcome</h2>
        <p>This is a test fixture site for the multi-agent orchestrator.</p>
        <p>It contains simple static HTML, CSS, and JavaScript for testing purposes.</p>

        <div class="features">
            <div class="feature">
                <h3>Feature 1</h3>
                <p>Simple static content</p>
            </div>
            <div class="feature">
                <h3>Feature 2</h3>
                <p>No external dependencies</p>
            </div>
            <div class="feature">
                <h3>Feature 3</h3>
                <p>Fully deterministic</p>
            </div>
        </div>

        <button onclick="greet()">Click Me</button>
        <div id="output"></div>
    </main>

    <footer>
        <p>&copy; 2025 Test Fixture Site</p>
    </footer>

    <script src="app.js"></script>
</body>
</html>
""",
        encoding="utf-8",
    )

    print("   Creating about.html...")
    (fixtures_dir / "about.html").write_text(
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fixture Site - About</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>About This Fixture</h1>
        <nav>
            <a href="index.html">Home</a>
            <a href="about.html">About</a>
            <a href="contact.html">Contact</a>
        </nav>
    </header>

    <main>
        <h2>About</h2>
        <p>This fixture site is used for testing the multi-agent orchestrator system.</p>
        <p>It provides a simple, predictable codebase for development and testing.</p>

        <h3>Purpose</h3>
        <ul>
            <li>Test orchestrator functionality</li>
            <li>Validate safety checks</li>
            <li>Profile performance</li>
            <li>Debug agent behavior</li>
        </ul>
    </main>

    <footer>
        <p>&copy; 2025 Test Fixture Site</p>
    </footer>
</body>
</html>
""",
        encoding="utf-8",
    )

    print("   Creating contact.html...")
    (fixtures_dir / "contact.html").write_text(
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fixture Site - Contact</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>Contact</h1>
        <nav>
            <a href="index.html">Home</a>
            <a href="about.html">About</a>
            <a href="contact.html">Contact</a>
        </nav>
    </header>

    <main>
        <h2>Contact Information</h2>
        <p>This is a test fixture - no real contact information.</p>

        <form id="contact-form">
            <label for="name">Name:</label>
            <input type="text" id="name" name="name" required>

            <label for="email">Email:</label>
            <input type="email" id="email" name="email" required>

            <label for="message">Message:</label>
            <textarea id="message" name="message" rows="4" required></textarea>

            <button type="submit">Send</button>
        </form>
        <div id="form-result"></div>
    </main>

    <footer>
        <p>&copy; 2025 Test Fixture Site</p>
    </footer>

    <script src="app.js"></script>
</body>
</html>
""",
        encoding="utf-8",
    )

    # Create CSS
    print("   Creating styles.css...")
    (fixtures_dir / "styles.css").write_text(
        """/* styles.css - Fixture site styles */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    background: #f4f4f4;
}

header {
    background: #2c3e50;
    color: white;
    padding: 1rem 2rem;
}

header h1 {
    margin-bottom: 0.5rem;
}

nav {
    display: flex;
    gap: 1rem;
}

nav a {
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    transition: background 0.3s;
}

nav a:hover {
    background: rgba(255, 255, 255, 0.1);
}

main {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 2rem;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

h2 {
    margin-bottom: 1rem;
    color: #2c3e50;
}

h3 {
    margin-top: 1rem;
    margin-bottom: 0.5rem;
    color: #34495e;
}

p {
    margin-bottom: 1rem;
}

.features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    margin: 2rem 0;
}

.feature {
    padding: 1rem;
    background: #ecf0f1;
    border-radius: 4px;
}

button {
    background: #3498db;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    margin-top: 1rem;
}

button:hover {
    background: #2980b9;
}

#output, #form-result {
    margin-top: 1rem;
    padding: 1rem;
    background: #e8f5e9;
    border-radius: 4px;
    display: none;
}

form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    max-width: 500px;
    margin-top: 1rem;
}

label {
    font-weight: bold;
}

input, textarea {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-family: inherit;
}

footer {
    text-align: center;
    padding: 2rem;
    color: #7f8c8d;
}

ul {
    margin-left: 2rem;
    margin-bottom: 1rem;
}
""",
        encoding="utf-8",
    )

    # Create JavaScript
    print("   Creating app.js...")
    (fixtures_dir / "app.js").write_text(
        """// app.js - Fixture site JavaScript

// Simple greeting function
function greet() {
    const output = document.getElementById('output');
    output.textContent = 'Hello from the test fixture!';
    output.style.display = 'block';

    setTimeout(() => {
        output.style.display = 'none';
    }, 3000);
}

// Handle contact form (if present)
const contactForm = document.getElementById('contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const result = document.getElementById('form-result');
        result.textContent = 'Form submission simulated (not sent anywhere)';
        result.style.display = 'block';

        setTimeout(() => {
            result.style.display = 'none';
            contactForm.reset();
        }, 3000);
    });
}

// Console log for testing
console.log('Fixture site JavaScript loaded successfully');
""",
        encoding="utf-8",
    )

    # Create README
    print("   Creating README.md...")
    (fixtures_dir / "README.md").write_text(
        """# Test Fixture Site

This is a test fixture site for the multi-agent orchestrator system.

## Contents

- `index.html` - Home page
- `about.html` - About page
- `contact.html` - Contact page with form
- `styles.css` - Styling
- `app.js` - Simple JavaScript

## Purpose

This fixture provides a simple, predictable codebase for:
- Testing orchestrator functionality without AI costs
- Validating safety checks
- Profiling performance
- Debugging agent behavior

All content is static and deterministic.
""",
        encoding="utf-8",
    )

    print(f"\n✅ Fixture site created successfully!")
    print(f"   Location: {fixtures_dir}")
    print(f"   Files created:")
    print(f"      - index.html")
    print(f"      - about.html")
    print(f"      - contact.html")
    print(f"      - styles.css")
    print(f"      - app.js")
    print(f"      - README.md")
    print(f"\n💡 To use this fixture:")
    print(f"   1. Update agent/project_config.json:")
    print(f'      "project_subdir": "fixtures"')
    print(f"   2. Set a simple task to test with")
    print(f"   3. Run: python dev/run_once.py\n")


if __name__ == "__main__":
    main()
