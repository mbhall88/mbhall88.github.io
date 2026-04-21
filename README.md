# mbhall88.github.io

Bioinformatics blog and portfolio for Michael Hall.

## Workflows

### 1. Adding a new post
Use the `Justfile` to scaffold a new post bundle:
```bash
just new-post my-exciting-research
```
This creates `content/post/my-exciting-research/index.md`. You can place scripts, data, and images directly in that folder.

### 2. Local Development
```bash
just serve
```
Visit `localhost:1313`.

### 3. Publications & Data Sync
```bash
just sync-all
```
This updates `data/github_stats.json` and scaffolds `content/publication/`.

### 4. CI/CD & Automation
- **GitHub Actions:** Automatically builds and deploys to GitHub Pages on every push to `main`.
- **Zenodo DOI:** A custom GitHub Action (work in progress) handles zipping post bundles and minting DOIs on Zenodo to make your research citeable.

### 5. Analytics & Comments
- **Analytics:** Powered by [GoatCounter](https://mbhall88.goatcounter.com). Dashboard is public.
- **Comments:** Powered by [giscus](https://giscus.app) via GitHub Discussions.

## Structure
- `content/post/`: Individual blog posts as page bundles.
- `content/publication/`: Research publications.
- `scripts/`: Python scripts for data sync and Zenodo automation.
- `Justfile`: Task runner for local development.
