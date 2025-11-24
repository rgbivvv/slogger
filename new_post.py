#!venv/bin/python
import logging
from pathlib import Path
from datetime import datetime, timezone
import subprocess
import argparse
import re
import unicodedata

logger = logging.getLogger(__name__)

def open_file_in_vim(fname: str, dest_path: Path):
	subprocess.run(['vim', str(dest_path / fname)])

def slugify(text: str) -> str:
	# Normalize to ASCII
	text = unicodedata.normalize("NFKD", text)
	text = text.encode("ascii", "ignore").decode("ascii")
    
	sep = '_'
	text = text.lower() # Lowercase
	text = re.sub(r"[^a-z0-9]+", sep, text) # Replace non-alphanumeric with separator
	text = text.strip(sep) # Remove unnecessary whitespace
	text = re.sub(rf"{sep}+", sep, text) # Get rid of multiple separators

	return text

def main():
	POSTS_DIR = Path('posts')
	parser = argparse.ArgumentParser()
	parser.add_argument('-t', '--title', help='The title of the new post. Make sure to put this in quotes')
	args = parser.parse_args()

	epoch = int(datetime.now(timezone.utc).timestamp())
	date = datetime.fromtimestamp(epoch).strftime('%Y%m%d')

	fname = slugify(f'{date}_{epoch}{'' if args.title is None else ' ' + args.title}') + '.md'
	logger.info(f'fname: {fname}')

	open_file_in_vim(fname, POSTS_DIR)
	# subprocess.run(['./main.py']) # Commented out because this is weird and hacky for now

if __name__ == '__main__':
	logging.basicConfig(
        	level=logging.INFO,
        	format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
	)
	main()
