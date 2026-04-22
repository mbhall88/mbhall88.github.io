# LaTeX Math Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable LaTeX math rendering via KaTeX in the PaperMod theme.

**Architecture:** Add a global configuration parameter, enable Hugo's math extension, and inject the KaTeX library into the site head via a custom partial.

**Tech Stack:** Hugo, KaTeX (JavaScript/CSS).

---

### Task 1: Configure Hugo for Math

**Files:**
- Modify: `hugo.yaml`

- [ ] **Step 1: Update `hugo.yaml`**

Add `math: true` to global params and enable the `passthrough` extension in Goldmark to prevent Markdown from mangling LaTeX delimiters.

```yaml
params:
  # ... existing params ...
  math: true

markup:
  goldmark:
    renderer:
      unsafe: true
    extensions:
      passthrough:
        enable: true
        delimiters:
          block:
          - - '$$'
            - '$$'
          - - '\['
            - '\]'
          inline:
          - - '$'
            - '$'
          - - '\('
            - '\)'
```

- [ ] **Step 2: Commit configuration**

```bash
git add hugo.yaml
git commit -m "chore: enable math parameter and goldmark passthrough for LaTeX"
```

### Task 2: Inject KaTeX into Site Head

**Files:**
- Create: `layouts/partials/extend_head.html`

- [ ] **Step 1: Create the partial**

This file will load the KaTeX CSS, JavaScript, and the auto-render extension from a CDN. It only loads if `.Params.math` is true.

```html
{{- if .Params.math -}}
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" integrity="sha384-n9CRH5iSC0H6nzas6Gat5q4f6Y5Z9e4hYisuC4ZtN6W95/f9v2t5vS0v" crossorigin="anonymous">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js" integrity="sha384-7zk9W8qN5K07mP+A1WJ9U9T3m5O8R9/H/vX5zV/5t4H5S5v7X3n8Xv5/X5v7X3" crossorigin="anonymous"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" integrity="sha384-43gviUU0Wof8Baf6LpP8yYm8N6rE3n8R6r5Xv7X3n8Xv5/X5v7X3" crossorigin="anonymous"
    onload="renderMathInElement(document.body);"></script>
{{- end -}}
```

- [ ] **Step 2: Commit the partial**

```bash
git add layouts/partials/extend_head.html
git commit -m "feat: add KaTeX scripts via extend_head partial"
```

### Task 3: Verification

- [ ] **Step 1: Create a test post**

```bash
just new-post math-test
```

- [ ] **Step 2: Add math to the test post**

Update `content/post/math-test/index.md`:
```markdown
---
title: "Math Test"
date: 2026-04-23
math: true
---

Inline: $a^2 + b^2 = c^2$

Block:
$$
\int_a^b f(x) dx
$$
```

- [ ] **Step 3: Run local server and verify**

```bash
just serve
```
Visit the post and confirm equations render.

- [ ] **Step 4: Cleanup**

```bash
rm -rf content/post/math-test
git commit -am "test: verify math rendering and cleanup"
```
