# LaTeX Math Rendering Specification

## Objective
Enable high-performance LaTeX math rendering across the blog using KaTeX. This will allow technical bioinformatics posts to display both inline and block equations clearly and efficiently.

## Background & Motivation
Bioinformatics posts often require mathematical notation (e.g., k-mer probabilities, alignment scores). The current PaperMod setup does not include a math engine by default, causing raw LaTeX strings like `$E=mc^2$` to be displayed instead of rendered equations.

## Scope & Impact
- **Target:** All pages where `math: true` is set in the frontmatter or globally.
- **Engine:** KaTeX (lightweight, fast, and server-side friendly).
- **Aesthetics:** Seamless integration with both Light and Dark themes.

## Proposed Solution (Architecture)

### 1. Configuration (`hugo.yaml`)
- Add a global `math: true` (or `false` if preferred to be opt-in) under `params`.
- Update the Markdown renderer (`goldmark`) settings to support math extensions.

### 2. Header Injection (`layouts/partials/extend_head.html`)
- Create or update the `extend_head.html` partial to include:
    - KaTeX CSS.
    - KaTeX JavaScript (with `defer` for performance).
    - An auto-render extension to detect and transform math delimiters on page load.

### 3. Supported Delimiters
- **Inline:** `$...$` and `\(...\)`
- **Block:** `$$...$$` and `\[...\]`

## Data Flow
1. Hugo renders the Markdown into HTML.
2. The browser loads the page and the KaTeX scripts.
3. The KaTeX auto-render script scans the DOM for math delimiters.
4. Mathematical notation is replaced with high-quality rendered symbols.

## Verification & Testing
- **Inline Test:** Verify that `$n = 123$` renders as a mathematical $n$.
- **Block Test:** Verify that `$$ \sum_{i=1}^n i $$` renders as a centered summation.
- **Theme Test:** Ensure equations remain readable when switching between Light and Dark modes.
