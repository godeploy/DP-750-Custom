"""Point the lab guides at the place where GoDeploy hosts these files.

The guides tell students to import notebooks from {{FILES_BASE_URL}}/Allfiles/<file>.
Run this once with the base URL of your hosted copy (the folder that contains "Allfiles"):

    python set_files_url.py https://raw.githubusercontent.com/<your-org>/<your-repo>/main
"""
import pathlib, sys

if len(sys.argv) != 2:
    sys.exit(__doc__)
base = sys.argv[1].rstrip('/')
labs = pathlib.Path(__file__).parent / 'Instructions' / 'Labs'
for md in sorted(labs.glob('*.md')):
    text = md.read_text(encoding='utf-8')
    if '{{FILES_BASE_URL}}' in text:
        md.write_text(text.replace('{{FILES_BASE_URL}}', base), encoding='utf-8')
        print('updated', md.name)
