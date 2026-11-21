"""Read-only Markdown local target/fragment audit; Python standard library only."""
from pathlib import Path
import re
import json
import sys
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', '.venv', '__pycache__', 'node_modules', 'release'}

def body(text):
    return re.sub(r'^\s*(```|~~~).*?^\s*\1\s*$', '', text, flags=re.M | re.S)

def slug(text):
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'[`*_~]', '', text).strip().lower()
    text = re.sub(r'[^\w\-\s\u0080-\uffff]', '', text)
    return re.sub(r'\s', '-', text)

def anchors(path):
    text = body(path.read_text(encoding='utf-8-sig'))
    out = set(re.findall(r'(?:id|name)=[\"\']([^\"\']+)', text))
    counts = {}
    for title in re.findall(r'^\s{0,3}#{1,6}\s+(.+?)\s*#*$', text, flags=re.M):
        base = slug(title)
        n = counts.get(base, 0)
        counts[base] = n + 1
        out.add(base + ('-' + str(n) if n else ''))
    return out

def check(root=ROOT):
    errors, exclusions, checked = [], [], 0
    pages = sorted(p for p in root.rglob('*.md') if not any(s in SKIP for s in p.relative_to(root).parts))
    for page in pages:
        text = body(page.read_text(encoding='utf-8-sig'))
        refs = {k.strip().lower(): v for k, v in re.findall(r'^\s*\[([^\]]+)\]:\s*(<[^>]+>|\S+)', text, flags=re.M)}
        links = re.findall(r'!?\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[\"\'][^\n]*?[\"\'])?\s*\)', text)
        for label, key in re.findall(r'!?\[([^\]]+)\]\[([^\]]*)\]', text):
            key = (key or label).strip().lower()
            if key not in refs:
                errors.append({'page': str(page.relative_to(root)), 'target': key, 'error': 'undefined reference label'})
            else:
                links.append(refs[key])
        links.extend(refs.values())
        for raw in links:
            url = raw.strip('<>')
            if re.match(r'^[a-zA-Z][\w+.-]*:', url) or url.startswith('//'):
                exclusions.append({'page': str(page.relative_to(root)), 'target': url, 'reason': 'external URI; no network reachability claim'})
                continue
            if any(x in url for x in ('{', '}', '<', '>')):
                exclusions.append({'page': str(page.relative_to(root)), 'target': url, 'reason': 'dynamic placeholder'})
                continue
            parsed = urllib.parse.urlsplit(url)
            target = (page.parent / urllib.parse.unquote(parsed.path)).resolve() if parsed.path else page
            checked += 1
            if not target.exists():
                errors.append({'page': str(page.relative_to(root)), 'target': url, 'error': 'missing target'})
            elif parsed.fragment and target.suffix.lower() == '.md':
                fragment = urllib.parse.unquote(parsed.fragment)
                if fragment not in anchors(target):
                    errors.append({'page': str(page.relative_to(root)), 'target': url, 'error': 'missing fragment'})
    return {'pages': len(pages), 'checked': checked, 'errors': errors, 'exclusions': exclusions, 'scope': 'inline and explicit/collapsed reference links outside fenced code; external URI reachability excluded'}

if __name__ == '__main__':
    result = check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(bool(result['errors']))
