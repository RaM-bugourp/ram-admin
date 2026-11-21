"""Deterministic source archive builder. Run only after release authorization."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
VERSION='1.0.0'
DIRECTORIES=('docs','spec','schemas','tools','tests','examples','templates','profiles','drafts')
ROOT_FILES=('README.md','AGENTS.md','ACCEPTANCE.md','CHANGELOG.md','INTEGRATION.md','.gitignore')
QA_FILES=('acceptance.py','check_links.py','integration.py','package.py','CASES.md','REPORT.md','SECURITY-REVIEW.md','results.json','integration-results.json','unit-output.txt','RELEASE.md')

def inventory():
    files=[ROOT/name for name in ROOT_FILES]+[ROOT/'qa'/name for name in QA_FILES]
    for directory in DIRECTORIES:
        files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo'))
    missing=[str(p.relative_to(ROOT)) for p in files if not p.is_file()]
    if missing: raise SystemExit('Missing required deliverables: '+', '.join(missing))
    if any(p.is_symlink() for p in files): raise SystemExit('Refusing symlink deliverable')
    return sorted(set(files),key=lambda p:p.relative_to(ROOT).as_posix())

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--build',action='store_true',help='create release archive after explicit authorization; default lists only')
    args=parser.parse_args(); files=inventory()
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    if not args.build:
        print(json.dumps({'version':VERSION,'files':len(files),'manifest':hashes,'mode':'preview-no-release-written'},ensure_ascii=False,indent=2)); return
    out=ROOT/'release'; out.mkdir(exist_ok=True)
    archive=out/f'harness-template-{VERSION}.zip'
    manifest=''.join(digest+'  '+name+'\n' for name,digest in hashes.items()).encode('utf-8')
    entries={p.relative_to(ROOT).as_posix():p.read_bytes() for p in files}; entries['SHA256SUMS.txt']=manifest
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:
        for name,data in sorted(entries.items()):
            info=zipfile.ZipInfo(f'harness-template-{VERSION}/'+name,date_time=(2026,11,14,0,0,0)); info.create_system=3; info.external_attr=0o100644<<16
            z.writestr(info,data)
    (out/'SHA256SUMS.txt').write_bytes(manifest)
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    (out/(archive.name+'.sha256')).write_text(digest+'  '+archive.name+'\n',encoding='utf-8')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,want in hashes.items(): assert hashlib.sha256(z.read(f'harness-template-{VERSION}/'+name)).hexdigest()==want
    print(json.dumps({'archive':str(archive),'files':len(files),'sha256':digest,'verified':True},indent=2))

if __name__=='__main__': main()
