"""Runs inside verify_live against a real isolated Django server, never APIClient."""
import csv,io,json,urllib.request,urllib.error,secrets

def exercise(Session,root,origin,password,check):
    first=Session();second=Session();check('HTTP security two user logins',first.login('e2e-user')[0]==200 and second.login('e2e-user')[0]==200)
    code,body=first.request('/api/auth/sessions/');rows=body['data'];check('HTTP safe session UUID metadata',code==200 and len(rows)>=2 and all(set(x)=={'id','created_at','expires_at','current'} for x in rows))
    check('HTTP sessions reject target field',first.request('/api/auth/revoke-other-sessions/','POST',{'user_id':1})[0]==400)
    check('HTTP own other sessions revoked',first.request('/api/auth/revoke-other-sessions/','POST',{})[0]==200 and second.request('/api/auth/user-info/')[0]==403 and first.request('/api/auth/user-info/')[0]==200)
    user_id=first.request('/api/auth/user-info/')[1]['data']['id']
    check('HTTP nonroot cannot revoke root sessions',first.request('/api/auth/revoke-user-sessions/','POST',{'user_id':user_id})[0]==403)
    check('HTTP root all target sessions revoked',root.request('/api/auth/revoke-user-sessions/','POST',{'user_id':user_id})[0]==200 and first.request('/api/auth/user-info/')[0]==403)
    # Grant/revoke an existing session's role and permissions through actual authorized APIs.
    actor=Session();actor.login('e2e-user');role=root.request('/api/rbac/roles/','POST',{'name':'HTTP security role','code':'http_security_role','permissions':['audit.read']})
    assert role[0]==201
    role_id=role[1]['data']['id'];check('HTTP grant current session audit role',root.request(f'/api/rbac/users/{user_id}/','PUT',{'role_ids':[role_id]})[0]==200 and actor.request('/api/audit/logs/')[0]==200)
    check('HTTP role revoke immediate for same session',root.request(f'/api/rbac/users/{user_id}/','PUT',{'role_ids':[]})[0]==200 and actor.request('/api/audit/logs/')[0]==403)
    check('HTTP inactive session denied immediately',root.request(f'/api/rbac/users/{user_id}/','PUT',{'is_active':False})[0]==200 and actor.request('/api/auth/user-info/')[0]==403);assert root.request(f'/api/rbac/users/{user_id}/','PUT',{'is_active':True})[0]==200
    for q in ['start=2026-02-30T00:00:00%2B08:00','start=2027-01-01T00:00:00Z&end=2026-01-01T00:00:00Z','action=a&action=b']:
        check('HTTP audit invalid filter structured 400 '+q.split('=')[0],root.request('/api/audit/logs/?'+q)[0]==400 and root.request('/api/audit/export/?'+q)[0]==400)
    request=urllib.request.Request(origin+'/api/audit/export/?resource=session',headers={'Accept':'text/csv'})
    response=root.open.open(request,timeout=20);content=response.read();parsed=list(csv.DictReader(io.StringIO(content.decode('utf-8-sig'))))
    check('HTTP CSV UTF8 safe fields download',response.status==200 and content.startswith(b'\xef\xbb\xbf') and parsed and set(parsed[0])=={'id','actor_id','actor_name','action','resource','object_id','outcome','created_at'} and response.headers['Cache-Control']=='no-store')
    check('HTTP nonroot CSV denied',actor.request('/api/audit/export/')[0]==403)
    # Controlled service clock tests cover exact expiry; real HTTP covers enforcement and Retry-After.
    name='missing-'+secrets.token_hex(5);fail=Session();fail.request('/api/auth/csrf/');statuses=[]
    for _ in range(8):statuses.append(fail.request('/api/auth/login/','POST',{'username':name,'password':'Synthetic-wrong-987!'})[0])
    csrf=next(c.value for c in fail.jar if c.name=='csrftoken')
    req=urllib.request.Request(origin+'/api/auth/login/',data=json.dumps({'username':name,'password':password}).encode(),headers={'Content-Type':'application/json','X-CSRFToken':csrf,'X-Forwarded-For':'9.8.7.6'},method='POST')
    try:result=fail.open.open(req,timeout=20)
    except urllib.error.HTTPError as error:result=error
    data=json.loads(result.read());check('HTTP real account limit XFF cannot bypass Retry-After',statuses==[401]*8 and result.status==429 and int(result.headers['Retry-After'])>0 and data['error']['code']=='LOGIN_LIMITED')
