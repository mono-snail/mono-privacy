#!/usr/bin/env python3
"""Render crawlable localized homepages using only the Python standard library.

Edit index.html and the existing catalogs, then run this script. Locale folders
are generated output. Set site_url in seo.config.json after choosing a domain.
"""
import argparse
from html import escape, unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
LANGS = {'en': ('en','en','en_US',''), 'zh': ('zh-CN','zh-Hans','zh_CN','zh/'),
         'zh-Hant': ('zh-Hant','zh-Hant','zh_TW','zh-hant/'), 'ja': ('ja','ja','ja_JP','ja/'), 'ko': ('ko','ko','ko_KR','ko/')}


def plain(value):
    return unescape(re.sub(r'<[^>]*>', ' ', value)).strip()


class Localize(HTMLParser):
    def __init__(self, source, copy, language, kind):
        super().__init__(convert_charrefs=False)
        self.source, self.copy, self.language, self.kind = source, copy, language, kind
        self.prefix = '' if language == 'en' else '../'
        self.lines = [0]
        for line in source.splitlines(keepends=True): self.lines.append(self.lines[-1] + len(line))
        self.stack, self.edits = [], []
        self.feed(source)

    def position(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def local_url(self, value):
        if not value or value.startswith(('#','/','?')) or urlsplit(value).scheme: return value
        return self.prefix + value

    def start(self, tag, attributes, closed=False):
        start = self.position()
        raw = self.get_starttag_text()
        original = dict(attributes)
        attrs = dict(original)
        if tag == 'html':
            attrs.update(lang=LANGS[self.language][0], **{'data-page-language':self.language, 'data-asset-prefix':self.prefix})
        for attr in ('content', 'alt', 'aria-label'):
            key = attrs.get('data-i18n-' + attr)
            if key: attrs[attr] = plain(self.copy[key])
        href_key = 'data-href-' + self.language.lower()
        if 'data-href-en' in attrs: attrs['href'] = attrs.get(href_key, attrs['data-href-en'])
        if tag == 'img':
            image_lang = 'zh' if self.language.startswith('zh') else 'en'
            if attrs.get('data-screen'):
                attrs['src'] = f"images/ios/ios-{attrs['data-screen']}-{image_lang}.webp"
            elif attrs.get('data-image-' + image_lang):
                attrs['src'] = attrs['data-image-' + image_lang]
        if attrs.get('data-language'):
            selected = attrs['data-language'] == self.language
            if selected: attrs['aria-current'] = 'page'
            else: attrs.pop('aria-current', None)
        if tag == 'option' and attrs.get('value') in LANGS:
            if attrs['value'] == self.language: attrs['selected'] = None
            else: attrs.pop('selected', None)
        for attr, value in list(attrs.items()):
            if attr in ('href','src','poster') or attr.startswith(('data-image-','data-href-')):
                attrs[attr] = self.local_url(value)
        if attrs != original:
            content = ''.join(' ' + key + ('' if value is None else '="' + escape(value, quote=True) + '"') for key,value in attrs.items())
            self.edits.append((start, start + len(raw), '<' + tag + content + ('/>' if closed else '>')))
        if tag not in VOID and not closed: self.stack.append((tag, start + len(raw), attrs.get('data-i18n')))

    def handle_starttag(self, tag, attrs): self.start(tag, attrs)
    def handle_startendtag(self, tag, attrs): self.start(tag, attrs, True)
    def handle_endtag(self, tag):
        for index in range(len(self.stack)-1, -1, -1):
            if self.stack[index][0] == tag:
                _, begin, key = self.stack[index]
                del self.stack[index:]
                if key:
                    value = self.copy[key]
                    self.edits.append((begin, self.position(), value if self.kind == 'mac' else escape(value)))
                break

    def render(self):
        parts, cursor = [], 0
        for begin, end, text in sorted(self.edits, key=lambda item: (item[0], -item[1])):
            if begin < cursor: continue  # A translated parent replaces its descendants.
            parts.extend((self.source[cursor:begin], text)); cursor = end
        return ''.join(parts) + self.source[cursor:]


def render_metadata(source, config, copy, language, base):
    title, description = plain(copy[config['title_key']]), plain(copy[config['description_key']])
    # Replace old social/canonical/structured data, preserving non-SEO head tags.
    head, body = source.split('</head>', 1)
    head = re.sub(r'\s*<!-- SEO:START -->.*?<!-- SEO:END -->', '', head, flags=re.S)
    head = re.sub(r'<script\b[^>]*type=[\"\']application/ld\+json[\"\'][^>]*>.*?</script>', '', head, flags=re.S|re.I)
    def keep_tag(match):
        tag = match.group()
        if re.search(r'(?:name|property)=[\"\'](?:description|robots|og:[^\"\']+|twitter:[^\"\']+)[\"\']', tag, re.I): return ''
        if re.search(r'rel=[\"\'](?:canonical|alternate)[\"\']', tag, re.I): return ''
        return tag
    head = re.sub(r'<(?:meta|link)\b[^>]*>', keep_tag, head, flags=re.I)
    head = re.sub(r'<title\b[^>]*>.*?</title>', '<title>' + escape(title) + '</title>', head, flags=re.S)
    route = LANGS[language][3]
    url = base + route if base else None
    image = (base or '') + config['social_image']
    tags = ['<!-- SEO:START -->', '<meta name="description" content="'+escape(description, quote=True)+'">',
            '<meta name="robots" content="index,follow,max-image-preview:large">']
    for key, value in {'og:title':title,'og:description':description,'og:type':'website','og:site_name':config['name'],
                       'og:locale':LANGS[language][2], 'og:image':image if base else '../'*bool(route)+image,
                       'og:image:alt':description,'twitter:card':'summary_large_image','twitter:title':title,
                       'twitter:description':description,'twitter:image':image if base else '../'*bool(route)+image}.items():
        tags.append('<meta '+('property' if key.startswith('og:') else 'name')+'="'+key+'" content="'+escape(value, quote=True)+'">')
    if url:
        tags.extend(['<link rel="canonical" href="'+url+'">','<meta property="og:url" content="'+url+'">'])
        for lang in config['languages']:
            tags.append('<link rel="alternate" hreflang="'+LANGS[lang][1]+'" href="'+base+LANGS[lang][3]+'">')
        tags.append('<link rel="alternate" hreflang="x-default" href="'+base+'">')
    app = dict(config['application'], name=config['name'], description=description)
    page = {'@type':'WebPage','name':title,'description':description,'inLanguage':LANGS[language][0]}
    if url: app['url'] = url; page['url'] = url
    app['@type'] = 'SoftwareApplication'
    graph = {'@context':'https://schema.org','@graph':[page, app]}
    # FAQ text remains visible in HTML; no unsupported ratings, prices or rich-result promises.
    tags.append('<script type="application/ld+json">'+json.dumps(graph,ensure_ascii=False).replace('</','<\\/')+'</script>')
    tags.append('<!-- SEO:END -->')
    return head + '\n' + '\n'.join(tags) + '\n</head>' + body


def generate(site_url=None):
    config = json.loads((ROOT/'seo.config.json').read_text())
    base = site_url or config.get('site_url')
    if base:
        parts = urlsplit(base)
        if parts.scheme != 'https' or not parts.netloc or parts.query or parts.fragment or parts.username or parts.password:
            raise SystemExit('site_url must be an absolute HTTPS site URL without query, fragment or credentials')
        base = base.rstrip('/') + '/'
    source = (ROOT/'index.html').read_text()
    if config['kind'] == 'ios':
        catalog = json.loads(source.split('const translations = ',1)[1].split('  const languageSelect = ',1)[0].strip().removesuffix(';'))
    else:
        catalog = json.loads((ROOT/'i18n.js').read_text().split('=',1)[1].strip().rstrip(';'))
        additions = json.loads((ROOT/'ios-i18n.js').read_text().split('=',1)[1].strip().rstrip(';'))
        for lang in catalog: catalog[lang].update(additions[lang])
    for language in config['languages']:
        page = Localize(source, catalog[language], language, config['kind']).render()
        page = render_metadata(page,config,catalog[language],language,base)
        target = ROOT / LANGS[language][3] / 'index.html'
        target.parent.mkdir(exist_ok=True)
        target.write_text(page.rstrip() + "\n")
    if base:
        ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'; xhtml = 'http://www.w3.org/1999/xhtml'
        ET.register_namespace('', ns); ET.register_namespace('xhtml', xhtml)
        path = ROOT/'sitemap.xml'
        tree = ET.parse(path) if path.exists() else ET.ElementTree(ET.Element('{'+ns+'}urlset'))
        root = tree.getroot()
        locale_urls = {base+LANGS[lang][3] for lang in config['languages']}
        for node in list(root):
            if node.findtext('{'+ns+'}loc') in locale_urls: root.remove(node)
        for language in config['languages']:
            node = ET.SubElement(root,'{'+ns+'}url'); ET.SubElement(node,'{'+ns+'}loc').text = base+LANGS[language][3]
            for alternate in config['languages']:
                ET.SubElement(node,'{'+xhtml+'}link',rel='alternate',hreflang=LANGS[alternate][1],href=base+LANGS[alternate][3])
            ET.SubElement(node,'{'+xhtml+'}link',rel='alternate',hreflang='x-default',href=base)
        ET.indent(tree,space='  '); tree.write(path,encoding='UTF-8',xml_declaration=True)
    elif config['kind'] == 'mac':
        (ROOT/'sitemap.xml').unlink(missing_ok=True)
    (ROOT/'robots.txt').write_text('User-agent: *\nAllow: /\n'+ ('\nSitemap: '+base+'sitemap.xml\n' if base else ''))
    print(f"Generated {len(config['languages'])} static languages. " + ('Canonical/hreflang/sitemap: '+base if base else 'Domain pending: absolute canonical, hreflang and sitemap deliberately omitted.'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site-url', help='Override seo.config.json site_url for a release build')
    generate(parser.parse_args().site_url)
