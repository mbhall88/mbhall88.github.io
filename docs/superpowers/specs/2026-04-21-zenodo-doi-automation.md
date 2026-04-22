# Zenodo DOI Automation Specification

## Objective
Automate the process of minting a Digital Object Identifier (DOI) for technical bioinformatics blog posts using the Zenodo API. This ensures that every post, including its associated scripts, plots, and data, is formally citeable and archived for long-term reproducibility.

## Background & Motivation
Technical bioinformatics blog posts often contain reusable code and unique results. Michael Hall needs a streamlined way to:
1.  Provide a permanent citation for his research outputs.
2.  Ensure reproducibility by archiving the complete "Page Bundle" (Markdown + code + data).
3.  Reduce manual overhead when finalizing a post.

## Scope & Impact
- **Target:** All future posts in `content/post/`.
- **Trigger:** A specific Git tag (`publish/<post-name>`) pushed to the repository.
- **Artifacts:** A permanent DOI from Zenodo and a dynamic "Cite this post" section on the blog.
- **Privacy:** Requires a `ZENODO_TOKEN` stored as a GitHub Secret.

## Proposed Solution (Architecture)

### 1. Tag-Triggered Workflow
-   **Command:** `just publish <post-name>`
-   **Local Actions:** 
    - Verifies the post directory exists.
    - Creates a Git tag: `publish/<post-name>`.
    - Pushes the tag to GitHub.

### 2. GitHub Action (`.github/workflows/zenodo.yml`)
-   Triggers on `tags: ["publish/**"]`.
-   Steps:
    1.  **Extract Metadata:** Parse the post name from the tag.
    2.  **Zip Bundle:** Compress the entire folder `content/post/<post-name>/`.
    3.  **Zenodo Deposit:** 
        - Call `scripts/zenodo_doi.py`.
        - Create a new deposition.
        - Upload the zip file.
        - Set metadata (Title from frontmatter, Author, ORCID).
        - **Publish** the deposition to obtain a permanent DOI.
    4.  **Update Post:** Inject the DOI into the post's frontmatter (`doi: "..."`).
    5.  **Commit & Push:** Commit the updated `index.md` back to the `master` branch.

### 3. UI Integration (Hugo PaperMod)
-   **DOI Badge:** A standard Shields.io DOI badge will be displayed at the top of the post if the `doi` frontmatter field is present.
-   **Citation Section:** A new partial will be added to the bottom of posts:
    - **Standard Citation:** A string like `Hall, M. B. (Year). Title. mbhall88.github.io. DOI: ...`
    - **BibTeX:** A copyable code block containing a standard `@misc` entry.

## Data Flow
1.  `just publish my-new-analysis`
2.  `git push origin publish/my-new-analysis`
3.  GitHub Action starts -> Python script executes -> Zenodo API returns DOI.
4.  GitHub Action updates `content/post/my-new-analysis/index.md`.
5.  Site rebuilds with DOI badge and Citation section.

## Verification & Testing
-   **Local:** Test the `just publish` command to ensure correct tag creation.
-   **Zenodo Sandbox:** Use Zenodo's sandbox environment for initial testing of the API script to avoid minting "junk" DOIs.
-   **UI:** Verify that a manual DOI entry in frontmatter correctly renders the badge and citation block.
