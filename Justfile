install:
    pnpm install
    hugo mod tidy

serve:
    hugo server -D

build:
    hugo --minify

new-post TITLE:
    hugo new --kind post post/{{TITLE}}

sync-pubs:
    python3 scripts/sync_data.py --pubs

sync-github:
    python3 scripts/sync_data.py --github

sync-all: sync-pubs sync-github
