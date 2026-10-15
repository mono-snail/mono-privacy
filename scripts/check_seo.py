#!/usr/bin/env python3
"""Validate the crawlable HTML, metadata, reciprocal locales and local links."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET
from seo import LANGS, plain

SOURCE = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--dist', action='store_true')
args = parser.parse_args()
root = SOURCE/'dist' if args.dist else SOURCE
config = json.loads((SOURCE/'seo.config.json').read_text())
base = config.get('site_url')
errors = []

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.language = ''; self.h1 = 0; self.title = ''; self.description = ''
        self.links = []; self.references = []; self.meta = {}; self.structured = []
        self.hidden = 0; self.in_title = False; self.in_h1 = False; self.h1_text = ''; self.ld = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html': self.language = a.get('lang')
        if tag == 'title': self.in_title = True
        if tag == 'h1': self.h1 += 1; self.in_h1 = True
        if tag == 'meta': self.meta[a.get('name') or a.get('property')] = a.get('content')
        if tag == 'link': self.links.append(a)
        for key,value in a.items():
            if key in ('href','src') or key.startswith('data-image-'): self.references.append(value)
        if tag == 'script' and a.get('type') == 'application/ld+json': self.ld = ''
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag == 'h1': self.in_h1 = False
        if tag == 'script' and self.ld is not None:
            self.structured.append(json.loads(self.ld)); self.ld = None
    def handle_data(self, data):
        if self.in_title: self.title += data
        if self.in_h1: self.h1_text += data
        if self.ld is not None: self.ld += data

for language in config['languages']:
    path = root/LANGS[language][3]/'index.html'
    page = Page(); page.feed(path.read_text())
    def check(condition, message):
        if not condition: errors.append(f'{language}: {message}')
    check(page.language == LANGS[language][0], 'wrong static document language')
    check(page.h1 == 1 and page.h1_text.strip(), 'expected one visible h1')
    check(10 <= len(page.title) <= 90, 'missing or excessive title')
    description = page.meta.get('description','')
    check(40 <= len(description) <= 200, 'missing or excessive description')
    for key in ('og:title','twitter:title'): check(page.meta.get(key) == page.title, key+' differs from title')
    for key in ('og:description','twitter:description'): check(page.meta.get(key) == description, key+' differs from description')
    canonicals = [link['href'] for link in page.links if link.get('rel') == 'canonical']
    alternates = {link.get('hreflang'):link.get('href') for link in page.links if link.get('rel') == 'alternate'}
    if base:
        check(canonicals == [base+LANGS[language][3]], 'canonical is not self-referencing')
        expected = {LANGS[lang][1]:base+LANGS[lang][3] for lang in config['languages']}
        expected['x-default'] = base
        check(alternates == expected, 'incomplete reciprocal hreflang')
    else:
        check(not canonicals and not alternates, 'unknown domain must not emit invented canonical/hreflang')
    check(len(page.structured) == 1, 'expected one structured data graph')
    graph = page.structured[0]['@graph']
    check({item['@type'] for item in graph} == {'WebPage','SoftwareApplication'}, 'unexpected structured data types')
    check(all(item['description'] == description for item in graph), 'schema differs from visible page metadata')
    for reference in page.references:
        url = urlsplit(reference or '')
        if url.scheme or url.netloc or not url.path: continue
        target = root/unquote(url.path.lstrip('/')) if url.path.startswith('/') else path.parent/unquote(url.path)
        if target.is_dir(): target /= 'index.html'
        check(target.is_file(), f'missing local URL: {reference}')
if base:
    sitemap = ET.parse(root/'sitemap.xml')
    urls = {node.text for node in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
    if not all(base+LANGS[lang][3] in urls for lang in config['languages']): errors.append('Missing language in sitemap')
    if 'Sitemap: '+base+'sitemap.xml' not in (root/'robots.txt').read_text(): errors.append('Missing sitemap discovery')
if errors: raise SystemExit('\n'.join(errors))
print(f"PASS: {len(config['languages'])} static languages, titles, social metadata, schema and links; domain " + (base or 'pending (no invented canonical)'))
