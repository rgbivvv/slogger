#!/usr/bin/bash
title="$*"
DEST_DIR="posts"
epoch=$(date +%s)        # Unix epoch
iso_date=$(date +%Y%m%d) # ISO 8601 date

if [ -n "$title" ]; then
    # Convert spaces to underscores
    slug="_${title// /_}"
else
    slug=""
fi

mkdir -p "$DEST_DIR"
file="$DEST_DIR/${iso_date}_${epoch}${slug}.md"

: > "$file" # Create the empty file
vim "$file" # and open it in vim
