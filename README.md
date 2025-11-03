# slogger

> The slog blogger

A scrappy static site generator focused on quick writing, plaintext files, and minimal dependencies.

Inspired by WNOADIARWB's [slog of thoughts](https://wnoadiarwb.us).

## Usage

This project is under active development, so expect some bugs when using it.

Create a `config.py` that defines the following variables:

```python
SITE_NAME="example.com"
SITE_URL="https://example.com"
SITE_DESCRIPTION="This is my slogger site"
BUILD_DIR="build"
MD_DIR="posts"
ASSETS_DIR="public"
COPYRIGHT_NAME="example.com"
```

Create a file called `index.md`. Example:

```markdown
This is my slogger site.
```