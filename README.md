# mbhall88.github.io

Bioinformatics blog and portfolio for Michael Hall. Built with [Hugo](https://gohugo.io/) and the [PaperMod](https://github.com/adityatelange/hugo-PaperMod) theme.

## Workflows

### 1. Adding a new post
Use the `Justfile` to scaffold a new post bundle:
```bash
just new-post my-exciting-research
```
This creates a new folder `content/post/my-exciting-research/index.md`. You can place images, scripts, and data files directly in that folder (Page Bundles).

### 2. Local Development
```bash
just serve
```
Visit `http://localhost:1313`.

### 3. Dynamic Stats & Metrics
- **Software Impact:** The homepage automatically fetches live download counts for **Rasusa** from Crates.io, Bioconda, and GitHub Releases.
- **GitHub Stats:** Real-time stars, followers, and primary language (weighted by stars) are fetched directly from the GitHub API on page load.
- **View Counts:** Individual posts display live view counts via [GoatCounter](https://mbhall88.goatcounter.com).

### 4. CI/CD & Automation
- **GitHub Actions:** Automatically builds and deploys to GitHub Pages on every push to the `master` branch.
- **Zenodo DOI Automation:** When a post is finalized, run `just publish <post-title>`. This creates a git tag that triggers a GitHub Action to:
  1. Zip the complete post folder (including scripts and data).
  2. Upload the bundle to Zenodo and formally publish it.
  3. Commit the resulting DOI back to your post's frontmatter.
- **Commenting:** Powered by [giscus](https://giscus.app) via GitHub Discussions.

### 5. Citations & Footnotes
You can automatically generate academic bibliographies using DOIs. 
Simply place the `cite` shortcode anywhere in your Markdown:
`This claim is supported by recent findings {{< cite "10.1038/s41586-021-03616-x" >}}.`

For multiple citations in one spot, pass multiple DOIs separated by spaces:
`{{< cite "10.123/a" "10.456/b" >}}`

This will generate numbered links in the text (e.g., `[1, 2]`) and automatically build a "References" section at the bottom of the post in the **Nature** citation style (with a hyperlinked DOI enforced). You can change the global citation style by editing `citationStyle` in `hugo.yaml`.

**Footnotes:** Standard markdown footnotes (e.g., `[^1]`) will automatically be styled as lowercase letters (e.g., `[a]`) to cleanly separate them from your numbered DOI citations.

## Configuration
To enable **Zenodo DOI automation**, you must:
1. Generate a Personal Access Token on [Zenodo](https://zenodo.org/account/settings/applications/).
2. Add it as a repository secret named `ZENODO_TOKEN` in your GitHub repository settings.

- `content/post/`: Individual blog posts as page bundles.
- `layouts/`: Custom overrides for the PaperMod theme (homepage stats, view counts).
- `static/`: Static assets like your CV (`cv.pdf`).
- `Justfile`: Task runner for local development.
