serve:
    hugo server -D

build:
    hugo --minify

new-post TITLE:
    hugo new --kind post post/{{TITLE}}/index.md

sync-github:
    python3 scripts/sync_data.py --github
