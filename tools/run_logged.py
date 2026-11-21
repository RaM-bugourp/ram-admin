"""Run one exact command with independent UTF-8 logs; no secret/environment dump."""
import argparse,datetime as dt,json,os,subprocess,sys,secrets
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);parser.add_argument('cmd',nargs=argparse.REMAINDER);args=parser.parse_args()
    if not args.label.replace('-','').replace('_','').isalnum():raise ValueError('invalid label')
    command=args.cmd[1:] if args.cmd[:1]==['--'] else args.cmd
    run=dt.datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z')+'-'+args.label+'-'+secrets.token_hex(3)
    out=ROOT/'docs/harness/evidence'/run;out.mkdir(parents=True,exist_ok=False)
    temp=ROOT/'.tmp'/run;temp.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy();env.update(PYTHONUTF8='1',TEMP=str(temp),TMP=str(temp),TMPDIR=str(temp),npm_config_cache=str(ROOT/'.npm-cache'))
    for key in list(env):
        if key.startswith(('OPENAI_','DEEPSEEK_','QCLAW_','AI_','DJANGO_')):env.pop(key)
    with (out/'stdout.txt').open('w',encoding='utf-8') as stdout,(out/'stderr.txt').open('w',encoding='utf-8') as stderr:
        result=subprocess.run(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
    (out/'command.json').write_text(json.dumps({'command':command,'cwd':str(ROOT),'exit_code':result.returncode,'time':dt.datetime.now().astimezone().isoformat()},indent=2),encoding='utf-8')
    print(json.dumps({'run':str(out),'exit_code':result.returncode}),flush=True);return result.returncode
if __name__=='__main__':sys.exit(main())
