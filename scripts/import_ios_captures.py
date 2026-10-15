#!/usr/bin/env python3
"""Import native XCTest captures as web-sized images (requires Pillow)."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from PIL import Image

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('xcresult', type=Path)
parser.add_argument('--mac-captures', type=Path, required=True,
                    help='Directory with ios-mac-overview-{en,zh}.png native sample renders')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
destination = root / 'images' / 'ios'
destination.mkdir(parents=True, exist_ok=True)
screens = ['home','devices','diagnostics','sessions','mac-guide','settings','theme-green','theme-purple','theme-dark']
expected = {f'ios-{screen}-{lang}.png' for screen in screens for lang in ['en','zh']}
manifest = {'capturedOn':'2026-10-15',
            'ios':'Release app, iPhone 17 Pro / iOS 27 simulator; real local HTTP, CONNECT and SOCKS5 test sessions; no interface compositing',
            'mac':'Companion build 27 native workspace, isolated sample data; not evidence of a live Mac-to-simulator connection',
            'conversion':'Resized preserving aspect ratio; WebP quality 90, method 6; app controls unchanged',
            'images':[]}

def convert(source):
    width = 1600 if 'mac-overview' in source.name else 960
    output = destination / source.with_suffix('.webp').name
    with Image.open(source) as image:
        image = image.convert('RGB')
        original_size = image.size
        image.thumbnail((width,10000), Image.Resampling.LANCZOS)
        image.save(output, 'WEBP', quality=90, method=6)
        size = image.size
    manifest['images'].append({'file':output.name,'width':size[0],'height':size[1],
        'originalWidth':original_size[0],'originalHeight':original_size[1],
        'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size})

found = set()
with tempfile.TemporaryDirectory(prefix='monoproxy-ios-homepage-') as directory:
    temporary = Path(directory)
    subprocess.run(['xcrun','xcresulttool','export','attachments','--path',str(args.xcresult.resolve()),
                    '--output-path',str(temporary)],check=True,stdout=subprocess.DEVNULL)
    for test in json.loads((temporary/'manifest.json').read_text()):
        for attachment in test['attachments']:
            name = attachment['suggestedHumanReadableName'].split('_0_')[0].removeprefix('website-') + '.png'
            if name in expected and attachment['exportedFileName'].endswith('.png'):
                source = temporary/attachment['exportedFileName']
                named = temporary/name
                named.write_bytes(source.read_bytes())
                convert(named)
                found.add(name)
    if found != expected:
        raise SystemExit(f'Missing native screenshots: {sorted(expected-found)}')
for lang in ['en','zh']:
    convert(args.mac_captures/f'ios-mac-overview-{lang}.png')
manifest['images'].sort(key=lambda item:item['file'])
(destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Imported {len(found)} native iOS screenshots and 2 Mac sample renders.')
print(f'Total WebP assets: {sum(item["bytes"] for item in manifest["images"])/1024/1024:.2f} MiB.')
