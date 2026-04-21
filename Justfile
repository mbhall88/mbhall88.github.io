serve:
    hugo server -D

build:
    hugo --minify

new-post TITLE:
    hugo new --kind post post/{{TITLE}}/index.md
