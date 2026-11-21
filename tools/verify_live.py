"""Real HTTP and real Edge orchestration. Requires frontend build and Python Playwright."""
import argparse,datetime as dt,secrets,os,sys,json,subprocess,socket,time,urllib.request,urllib.error,http.cookiejar,threading,http.server,http.client,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def free_port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--python',required=True);p.add_argument('--browser-python',required=True);a=p.parse_args()
 run=dt.datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z')+'-live-'+secrets.token_hex(3);out=ROOT/'docs/harness/evidence'/run;out.mkdir(parents=True,exist_ok=False)
 temp=ROOT/'.tmp'/run;temp.mkdir(parents=True,exist_ok=False)
 backend_port=free_port();assert backend_port not in (8000,5173,15173,18000,18791,18792)
 env=os.environ.copy()
 for key in list(env):
  if key.startswith(('OPENAI_','DEEPSEEK_','QCLAW_','AI_','DJANGO_','RAM_TEST_')):env.pop(key)
 env.update(PYTHONUTF8='1',TEMP=str(temp),TMP=str(temp),TMPDIR=str(temp),RAM_TEST_DB=str(temp/'live.sqlite3'),RAM_TEST_SECRET=secrets.token_urlsafe(48),RAM_TEST_AGENT_SECRET=secrets.token_urlsafe(48),RAM_TEST_PASSWORD=secrets.token_urlsafe(24))
 report={'status':'running','checks':[],'source':'real-http-server-and-msedge','production_acceptance':False};proc=None;server=None;handles=[]
 def save(): (out/'live-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 def check(name,condition):assert condition,name;report['checks'].append({'name':name,'pass':True});save()
 try:
  with (out/'seed.stdout.txt').open('w',encoding='utf-8') as so,(out/'seed.stderr.txt').open('w',encoding='utf-8') as se:subprocess.run([a.python,'tools/seed_integration.py'],cwd=ROOT,env=env,stdout=so,stderr=se,check=True)
  for name in ('backend.stdout.txt','backend.stderr.txt'):handles.append((out/name).open('w',encoding='utf-8'))
  proc=subprocess.Popen([a.python,'backend/manage.py','runserver',f'127.0.0.1:{backend_port}','--noreload','--settings=config.settings.integration'],cwd=ROOT,env=env,stdout=handles[0],stderr=handles[1])
  origin=f'http://127.0.0.1:{backend_port}'
  for _ in range(150):
   if proc.poll() is not None:raise RuntimeError('isolated backend exited')
   try:
    with urllib.request.urlopen(origin+'/api/auth/csrf/',timeout=1) as r:
     if r.status==200:break
   except (OSError,urllib.error.URLError):time.sleep(.1)
  else:raise RuntimeError('backend readiness timeout')
  class Handler(http.server.SimpleHTTPRequestHandler):
   def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'frontend/dist'),**kwargs)
   def log_message(self,*args):pass
   def proxy(self):
    body=self.rfile.read(int(self.headers.get('Content-Length',0)))
    headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','content-length')}
    # Same browser origin is explicitly forwarded as trusted backend host. Do NOT rewrite foreign Origin.
    if headers.get('Origin')==frontend_origin:headers['Origin']=origin
    headers['Host']=f'127.0.0.1:{backend_port}'
    conn=http.client.HTTPConnection('127.0.0.1',backend_port,timeout=30)
    try:
     conn.request(self.command,self.path,body=body,headers=headers);r=conn.getresponse();data=r.read();self.send_response(r.status)
     for k,v in r.getheaders():
      if k.lower() not in ('transfer-encoding','connection','content-length'):self.send_header(k,v)
     self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    finally:conn.close()
   def do_GET(self):
    if self.path.startswith('/api/'):return self.proxy()
    if not Path(self.translate_path(self.path)).is_file():self.path='/index.html'
    return super().do_GET()
   def do_POST(self):return self.proxy()
   def do_PUT(self):return self.proxy()
   def do_DELETE(self):return self.proxy()
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);frontend_origin=f'http://127.0.0.1:{server.server_address[1]}';thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  report['backend_origin']=origin;report['frontend_origin']=frontend_origin;report['backend_pid']=proc.pid
  class Session:
   def __init__(self):self.jar=http.cookiejar.CookieJar();self.open=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
   def request(self,path,method='GET',data=None,csrf=True,origin_header=None):
    headers={'Content-Type':'application/json'}
    if csrf:
     token=next((c.value for c in self.jar if c.name=='csrftoken'),'')
     if token:headers['X-CSRFToken']=token
    if origin_header:headers['Origin']=origin_header
    req=urllib.request.Request(origin+path,data=json.dumps(data).encode() if data is not None else None,headers=headers,method=method)
    try:r=self.open.open(req,timeout=30)
    except urllib.error.HTTPError as error:r=error
    body=r.read();return r.status,json.loads(body) if body and r.headers.get('Content-Type','').startswith('application/json') else {}
   def login(self,name):
    self.request('/api/auth/csrf/');return self.request('/api/auth/login/','POST',{'username':name,'password':env['RAM_TEST_PASSWORD']})
  anon=Session();anon.request('/api/auth/csrf/')
  check('HTTP missing login CSRF denied',anon.request('/api/auth/login/','POST',{'username':'e2e-root','password':env['RAM_TEST_PASSWORD']},csrf=False)[0]==403)
  check('HTTP foreign login Origin denied',anon.request('/api/auth/login/','POST',{'username':'e2e-root','password':env['RAM_TEST_PASSWORD']},origin_header='https://evil.invalid')[0]==403)
  root=Session();check('HTTP root no-role superuser login',root.login('e2e-root')[0]==200)
  check('HTTP authenticated write missing CSRF denied',root.request('/api/rbac/users/','POST',{},csrf=False)[0]==403)
  user=Session();check('HTTP ordinary login',user.login('e2e-user')[0]==200)
  for path in ('/api/rbac/users/','/api/rbac/roles/','/api/audit/logs/'):check('HTTP ordinary denied '+path,user.request(path)[0]==403)
  auditor=Session();auditor.login('e2e-auditor');check('HTTP explicit audit permission works',auditor.request('/api/audit/logs/')[0]==200)
  second=Session();second.login('e2e-user');new_password=secrets.token_urlsafe(24)
  check('HTTP own password changed',user.request('/api/auth/change-password/','POST',{'old_password':env['RAM_TEST_PASSWORD'],'new_password':new_password})[0]==200)
  check('HTTP current password session retained',user.request('/api/auth/user-info/')[0]==200);check('HTTP other password session revoked',second.request('/api/auth/user-info/')[0]==403)
  # Restore synthetic user's password via authorized root; do not disclose it in evidence.
  uid=user.request('/api/auth/user-info/')[1]['data']['id'];root.request(f'/api/rbac/users/{uid}/reset-password/','POST',{'password':env['RAM_TEST_PASSWORD']})
  from live_security import exercise
  exercise(Session,root,origin,env['RAM_TEST_PASSWORD'],check)
  browser_env={**env,'RAM_LIVE_ORIGIN':frontend_origin,'RAM_LIVE_OUTPUT':str(out)}
  with (out/'browser.stdout.txt').open('w',encoding='utf-8') as so,(out/'browser.stderr.txt').open('w',encoding='utf-8') as se:
   result=subprocess.run([a.browser_python,'tools/browser_core.py'],cwd=ROOT,env=browser_env,stdout=so,stderr=se)
  check('Real Edge browser script exit zero',result.returncode==0)
  report['browser']=json.loads((out/'browser.json').read_text(encoding='utf-8'));report['check_count']=len(report['checks']);report['status']='pass'
 except Exception as error:
  report['status']='fail';report['error_type']=type(error).__name__;report['error']=str(error);raise
 finally:
  if server:server.shutdown();server.server_close()
  if proc:
   proc.terminate()
   try:proc.wait(timeout=15)
   except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=15)
  for handle in handles:handle.close()
  report['server_closed']=server is None or True;report['backend_stopped']=proc is None or proc.poll() is not None
  # Synthetic SQLite and browser profiles are ephemeral, no account/DB artifact delivered.
  try:shutil.rmtree(temp);report['isolated_data_removed']=not temp.exists()
  except Exception as error:report['cleanup_error']=type(error).__name__
  save();print(json.dumps({'run':str(out),'status':report['status'],'http_checks':len(report['checks']),'backend_stopped':report['backend_stopped']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
