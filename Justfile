serve:
    hugo server -D

build:
    hugo --minify

new-post TITLE:
    hugo new --kind post post/{{TITLE}}/index.md

publish TITLE:
    @git tag -a "publish/{{TITLE}}" -m "Publishing {{TITLE}} for DOI minting"
    @git push origin "publish/{{TITLE}}"
    @echo "Tag pushed! Check GitHub Actions to follow DOI minting progress."
