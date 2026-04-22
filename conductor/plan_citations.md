# Citation & Footnotes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a build-time DOI citation system that accepts multiple DOIs, enforces formatted academic styles (defaulting to Nature), explicitly appends a hyperlinked DOI, changes standard footnotes to use letters via CSS, and documents the entire process.

**Architecture:** A Hugo shortcode using `resources.GetRemote` to hit the CrossRef API with content negotiation, storing results in a page `.Scratch` variable. The `single.html` layout renders the references list. CSS counters are used to mask footnote numbers and replace them with letters.

**Tech Stack:** Hugo Go Templates, CSS.

---

### Task 1: Update Hugo Configuration

**Files:**
- Modify: `hugo.yaml`

- [ ] **Step 1: Update `hugo.yaml`**
Add `citationStyle: "nature"` under `params`.

```yaml
params:
  # ... existing params ...
  citationStyle: "nature"
```

- [ ] **Step 2: Commit configuration**
```bash
git add hugo.yaml
git commit -m "chore: add default citation style parameter"
```

### Task 2: Custom CSS for Lettered Footnotes

**Files:**
- Create: `assets/css/extended/footnotes.css`

- [ ] **Step 1: Create the CSS file**
PaperMod automatically includes any `.css` file inside `assets/css/extended/`. We will use CSS counters to hide the standard numeric footnote markers and replace them with lowercase letters.

```css
.post-single {
    counter-reset: footnote;
}
.footnote-ref a {
    visibility: hidden;
    position: relative;
    display: inline-block;
    width: 1em; /* Allocate space for the letter */
}
.footnote-ref a::after {
    visibility: visible;
    counter-increment: footnote;
    content: "[" counter(footnote, lower-alpha) "]";
    position: absolute;
    left: 0;
    color: var(--primary);
    text-decoration: none;
}
.footnote-ref a:hover::after {
    text-decoration: underline;
}
.footnotes ol {
    list-style-type: lower-alpha;
}
```

- [ ] **Step 2: Commit CSS**
```bash
git add assets/css/extended/footnotes.css
git commit -m "feat: convert standard footnotes to use letters via CSS"
```

### Task 3: Create the `cite` Shortcode

**Files:**
- Create: `layouts/shortcodes/cite.html`

- [ ] **Step 1: Create the shortcode**
The shortcode loops through its arguments (DOIs), queries CrossRef with the user's preferred style, strips any leading numbers returned by the API, appends the explicit DOI link, and stores the citation in a `.Scratch` array. It then renders a clickable bracketed list (e.g. `[1, 2]`).

```go
{{- $style := site.Params.citationStyle | default "nature" -}}
{{- $opts := dict "headers" (dict "Accept" (printf "text/x-bibliography; style=%s" $style)) -}}

{{- $citations := .Page.Scratch.Get "citations" | default slice -}}
{{- $indexes := slice -}}

{{- range .Params -}}
  {{- $doi := . -}}
  {{- $url := printf "https://doi.org/%s" $doi -}}
  {{- $res := resources.GetRemote $url $opts -}}
  
  {{- if $res -}}
    {{- $formatted := $res.Content -}}
    {{- /* Strip leading digits and dots/spaces that some CSL styles add */ -}}
    {{- $clean := replaceRE "^\\d+\\.\\s*" "" $formatted -}}
    {{- $clean = replaceRE "\n" "" $clean -}}
    {{- $fullCitation := printf "%s <a href=\"https://doi.org/%s\" target=\"_blank\">[doi:%s]</a>" $clean $doi $doi -}}
    
    {{- $idx := -1 -}}
    {{- range $i, $c := $citations -}}
      {{- if eq $c $fullCitation -}}{{- $idx = $i -}}{{- end -}}
    {{- end -}}
    
    {{- if eq $idx -1 -}}
      {{- $citations = $citations | append $fullCitation -}}
      {{- $idx = sub (len $citations) 1 -}}
    {{- end -}}
    
    {{- $indexes = $indexes | append (add $idx 1) -}}
  {{- else -}}
    {{- errorf "Failed to fetch citation for DOI: %s" $doi -}}
  {{- end -}}
{{- end -}}

{{- .Page.Scratch.Set "citations" $citations -}}

{{- /* Render the citation link */ -}}
[<a href="#references" class="citation-link">{{ delimit $indexes ", " }}</a>]
```

- [ ] **Step 2: Commit the shortcode**
```bash
git add layouts/shortcodes/cite.html
git commit -m "feat: add cite shortcode for automated DOI bibliography"
```

### Task 4: Render References at the Bottom of Posts

**Files:**
- Modify: `layouts/_default/single.html`

- [ ] **Step 1: Inject the references list**
Modify `layouts/_default/single.html` to output the `.Scratch` citations list right below the content, before the post footer. Add it right after `{{- partial "citation.html" . -}}`.

```go
    {{- /* Custom Injection: References List */ -}}
    {{- $citations := .Scratch.Get "citations" -}}
    {{- if $citations -}}
    <div class="references-container" style="margin-top: 3rem; padding: 1.5rem; background: var(--code-bg); border-radius: 8px; border: 1px solid var(--tertiary);">
        <h3 id="references">References</h3>
        <ol class="references-list" style="font-size: 0.9em; padding-left: 1.5rem; margin-top: 1rem;">
            {{- range $citations -}}
            <li style="margin-bottom: 0.8rem; line-height: 1.4;">{{ . | safeHTML }}</li>
            {{- end -}}
        </ol>
    </div>
    {{- end -}}
```

- [ ] **Step 2: Commit the layout**
```bash
git add layouts/_default/single.html
git commit -m "feat: render automated bibliography section in single post layout"
```

### Task 5: Document the Workflow

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README.md**
Add a new section explaining how to use citations and footnotes.

```markdown
### 6. Citations & Footnotes
You can automatically generate academic bibliographies using DOIs. 
Simply place the `cite` shortcode anywhere in your Markdown:
`This claim is supported by recent findings {{< cite "10.1038/s41586-021-03616-x" >}}.`

For multiple citations in one spot, pass multiple DOIs separated by spaces:
`{{< cite "10.123/a" "10.456/b" >}}`

This will generate numbered links in the text (e.g., `[1, 2]`) and automatically build a "References" section at the bottom of the post in the **Nature** citation style (with a hyperlinked DOI enforced). You can change the global citation style by editing `citationStyle` in `hugo.yaml`.

**Footnotes:** Standard markdown footnotes (e.g., `[^1]`) will automatically be styled as lowercase letters (e.g., `[a]`) to cleanly separate them from your numbered DOI citations.
```

- [ ] **Step 2: Commit README**
```bash
git add README.md
git commit -m "docs: document DOI citation and footnote workflows"
```
