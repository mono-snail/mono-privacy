#!/usr/bin/env python3
"""Check local page links, homepage languages, and native screenshot assets."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

root = Path(__file__).resolve().parents[1]
errors = []

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path, self.ids, self.references, self.keys, self.screens = path, set(), [], set(), set()
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            if attrs['id'] in self.ids: errors.append(f'{self.path.name}: duplicate id {attrs["id"]}')
            self.ids.add(attrs['id'])
        for attribute in ['href','src']:
            if attrs.get(attribute): self.references.append(attrs[attribute])
        for attribute in ['data-i18n','data-i18n-alt']:
            if attrs.get(attribute): self.keys.add(attrs[attribute])
        if attrs.get('data-screen'): self.screens.add(attrs['data-screen'])

pages = {path:Page(path) for path in root.rglob('*.html') if '.git' not in path.parts}
for path, page in pages.items():
    for reference in page.references:
        url = urlsplit(reference)
        if url.scheme or url.netloc: continue
        target = root/unquote(url.path.lstrip('/')) if url.path.startswith('/') else path.parent/unquote(url.path)
        if not url.path: target = path
        if target.is_dir(): target = target/'index.html'
        target = target.resolve()
        if not target.exists(): errors.append(f'{path.name}: missing {reference}')
        elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
            errors.append(f'{path.name}: missing anchor {reference}')

source = (root/'index.html').read_text()
catalog = json.loads(source.split('const translations = ',1)[1].split('  const languageSelect = ',1)[0].strip().removesuffix(';'))
for language, copy in catalog.items():
    for key in pages[root/'index.html'].keys:
        if not copy.get(key): errors.append(f'{language}: missing translation {key}')
    if set(copy) != set(catalog['en']): errors.append(f'{language}: language keys differ')
assets = root/'images'/'ios'
manifest = json.loads((assets/'manifest.json').read_text())
for item in manifest['images']:
    path = assets/item['file']
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        errors.append(f'Capture hash mismatch: {item["file"]}')
for screen in pages[root/'index.html'].screens:
    for language in ['en','zh']:
        if not (assets/f'ios-{screen}-{language}.webp').exists(): errors.append(f'Missing {screen} {language} screenshot')
if errors: raise SystemExit('\n'.join(errors))
print(f'PASS: {len(pages)} pages, {len(catalog)} languages, {len(manifest["images"])} verified native screenshot assets.')
