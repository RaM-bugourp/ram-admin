"""Real Playwright + installed Edge against actual Vue build and isolated Django HTTP."""
import os,json,re
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ORIGIN=os.environ['RAM_LIVE_ORIGIN'];OUT=Path(os.environ['RAM_LIVE_OUTPUT']);PASSWORD=os.environ['RAM_TEST_PASSWORD']
report={'checks':[],'page_errors':[],'ai_requests':[],'limitations':['Automated Edge only; not human visual acceptance or physical phone.']}
def save(): (OUT/'browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def check(name,value=True):assert value,name;report['checks'].append({'name':name,'pass':True});save()
def api(page,path,method='GET',data=None):
 return page.evaluate("""async ({path,method,data})=>{const token=document.cookie.split('; ').find(x=>x.startsWith('csrftoken='))?.split('=')[1];const r=await fetch('/api'+path,{method,headers:{'Content-Type':'application/json','X-CSRFToken':token||''},body:data===null?undefined:JSON.stringify(data)});return {status:r.status,body:r.status===204?null:await r.json()}}""",{'path':path,'method':method,'data':data})
def login(page,name):
 page.goto(ORIGIN+'/login');page.get_by_placeholder('admin',exact=True).fill(name);page.get_by_placeholder('请输入密码',exact=True).fill(PASSWORD);page.get_by_role('button',name='登录',exact=True).click();page.wait_for_url('**/dashboard');expect(page.get_by_role('heading',name='工作台',exact=True)).to_be_visible()
with sync_playwright() as pw:
 browser=pw.chromium.launch(channel='msedge',headless=True,args=['--disable-background-networking']);report['browser_version']=browser.version
 try:
  context=browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page();page.on('pageerror',lambda e:report['page_errors'].append(str(e)));page.on('request',lambda r:report['ai_requests'].append(r.url) if '/api/ai/' in r.url else None)
  login(page,'e2e-root');check('browser root superuser without role login')
  expect(page.get_by_text('用户管理',exact=True)).to_be_visible();expect(page.get_by_text('角色与权限',exact=True)).to_be_visible();check('superuser capability navigation')
  page.goto(ORIGIN+'/system/users');expect(page.get_by_role('button',name='新建用户',exact=True)).to_be_visible();page.reload();expect(page.get_by_role('button',name='新建用户',exact=True)).to_be_visible();check('session bootstrap refresh direct protected route')
  page.get_by_role('button',name='新建用户',exact=True).click();dialog=page.locator('.arco-modal:visible');dialog.get_by_placeholder('至少3位',exact=True).fill('browser-created');dialog.get_by_placeholder('user@example.com',exact=True).fill('browser-created@example.invalid');dialog.get_by_placeholder('至少6位',exact=True).fill('Browser-Only-987!');dialog.get_by_role('button',name='确定',exact=True).click();expect(dialog).not_to_be_visible();check('UI user creation actual HTTP persistence')
  search=page.get_by_placeholder('搜索用户名 / 邮箱');search.fill('browser-created');search.press('Enter');row=page.locator('tr').filter(has_text='browser-created@example.invalid');expect(row).to_have_count(1);check('UI user search actual results')
  row.get_by_role('button',name='编辑',exact=True).click();dialog=page.locator('.arco-modal:visible');dialog.get_by_placeholder('user@example.com',exact=True).fill('browser-updated@example.invalid');dialog.get_by_role('button',name='确定',exact=True).click();expect(dialog).not_to_be_visible();expect(page.get_by_text('browser-updated@example.invalid',exact=True)).to_be_visible();check('UI user edit persisted')
  # Explicit empty state, keyboard dismissal, server errors and last-page deletion.
  search.fill('never-matches-synthetic');search.press('Enter');expect(page.locator('.arco-empty')).to_be_visible();expect(page.locator('tbody tr[data-key]')).to_have_count(0);check('UI search empty state')
  page.get_by_role('button',name='新建用户',exact=True).click();dialog=page.locator('.arco-modal:visible');expect(dialog).to_contain_text('新建用户');page.keyboard.press('Escape');expect(dialog).not_to_be_visible();check('keyboard Escape closes create modal')
  search.fill('');search.press('Enter');expect(page.locator('tbody tr')).to_have_count(20)
  page.route('**/api/rbac/users/?*',lambda route:route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':{'code':'UNAVAILABLE','message':'Synthetic retry error'}})))
  search.press('Enter');expect(page.locator('.arco-alert-error')).to_contain_text('Synthetic retry error');page.unroute('**/api/rbac/users/?*');page.get_by_role('button',name='重试',exact=True).click();expect(page.locator('.arco-alert-error')).to_have_count(0);check('UI loading failure explicit retry')
  # Shrink page two to one record via real authorized HTTP then delete that last record through UI.
  last=api(page,'/rbac/users/?page=2&page_size=20')['body'];fixtures=[x for x in last['data'] if x['username'].startswith('page-fixture-')]
  for fixture in fixtures[:-1]:assert api(page,f"/rbac/users/{fixture['id']}/",'DELETE')['status']==204
  remaining=api(page,'/rbac/users/?page=2&page_size=20')['body']['data']
  # Core protected fixture users remain; reduce only synthetic page-fixture rows, never identities.
  if len(remaining)>1:
   first=api(page,'/rbac/users/?page=1&page_size=20')['body']['data']
   removable=[x for x in first if x['username'].startswith('page-fixture-')]
   for fixture in removable[:len(remaining)-1]:assert api(page,f"/rbac/users/{fixture['id']}/",'DELETE')['status']==204
  page.reload();expect(page.get_by_role('button',name='新建用户',exact=True)).to_be_visible();page.locator('.arco-pagination-item').filter(has_text=re.compile('^2$')).click();expect(page.locator('tbody tr')).to_have_count(1)
  page.locator('tbody tr').get_by_role('button',name='删除',exact=True).click();expect(page.locator('.arco-popconfirm-popup-content:visible')).to_contain_text('确定删除该用户？');page.locator('.arco-popconfirm-popup-content:visible').get_by_role('button',name='确定',exact=True).click();expect(page.locator('.arco-pagination-item-active')).to_have_text('1');check('last page deletion clamps and syncs current page')
  search=page.get_by_placeholder('搜索用户名 / 邮箱');search.fill('browser-created');search.press('Enter');expect(page.locator('tbody tr')).to_have_count(1)
  # Duplicate input returns a visible error and leaves modal open; no second user.
  page.get_by_role('button',name='新建用户',exact=True).click();dialog=page.locator('.arco-modal:visible');dialog.get_by_placeholder('至少3位',exact=True).fill('browser-created');dialog.get_by_placeholder('user@example.com',exact=True).fill('duplicate@example.invalid');dialog.get_by_placeholder('至少6位',exact=True).fill('Browser-Only-987!');dialog.get_by_role('button',name='确定',exact=True).click();expect(page.get_by_text('用户名或邮箱已被使用（含已删除记录）',exact=True)).to_be_visible();expect(dialog).to_be_visible();dialog.get_by_role('button',name='取消',exact=True).click();check('duplicate input visible failure no false success')
  page.goto(ORIGIN+'/system/roles');page.get_by_role('button',name='新建角色',exact=True).click();dialog=page.locator('.arco-modal:visible');dialog.get_by_placeholder('如：超级管理员').fill('browser-role');dialog.get_by_placeholder('如：root（仅小写字母、数字、下划线）').fill('browser_role');dialog.get_by_placeholder('角色的用途说明').fill('Synthetic role');dialog.get_by_role('button',name='确定',exact=True).click();expect(dialog).not_to_be_visible();expect(page.get_by_text('browser-role',exact=True)).to_be_visible();check('UI role create persisted')
  role_row=page.locator('tr').filter(has_text='browser_role');role_row.get_by_role('button',name='编辑',exact=True).click();dialog=page.locator('.arco-modal:visible');dialog.get_by_placeholder('角色的用途说明').fill('Edited synthetic role');dialog.get_by_role('button',name='确定',exact=True).click();expect(dialog).not_to_be_visible();expect(page.get_by_text('Edited synthetic role',exact=True)).to_be_visible();check('UI role edit persisted')
  page.goto(ORIGIN+'/system/audit');expect(page.get_by_text('操作审计',exact=True).last).to_be_visible();page.get_by_placeholder('动作，如 user.create').fill('user.create');page.get_by_role('button',name='查询',exact=True).click();expect(page.locator('tbody tr').first).to_contain_text('user.create');check('UI real audit action filter')
  audit=api(page,'/audit/logs/?action=user.create');check('HTTP audit fixed safe metadata',audit['status']==200 and all(set(x)=={'id','actor_id','actor_name','action','resource','object_id','outcome','created_at'} for x in audit['body']['data']))
  page.goto(ORIGIN+'/settings');expect(page.get_by_role('heading',name='修改本人密码')).to_be_visible();passwords=page.locator('input[type=password]');passwords.nth(0).fill(PASSWORD);passwords.nth(1).fill('Browser-Changed-987!');page.get_by_role('button',name='修改密码',exact=True).click();expect(page.get_by_text('密码修改成功',exact=True)).to_be_visible();page.reload();expect(page.get_by_role('heading',name='修改本人密码')).to_be_visible();check('UI own password change current session survives reload')
  # Authorized HTTP mutation restores only synthetic account's password for repeat login.
  uid=api(page,'/auth/user-info/')['body']['data']['id'];check('restore synthetic password',api(page,f'/rbac/users/{uid}/reset-password/','POST',{'password':PASSWORD})['status']==200)
  # Reset invalidates current session, so test fresh auth and logout.
  login(page,'e2e-root');page.get_by_role('button',name='退出',exact=True).click();page.wait_for_url('**/login');check('UI logout invalidates session',api(page,'/auth/user-info/')['status']==403)
  user_context=browser.new_context(viewport={'width':1440,'height':1000});user_page=user_context.new_page();user_page.on('pageerror',lambda e:report['page_errors'].append(str(e)));login(user_page,'e2e-user');check('ordinary UI login')
  check('ordinary privileged menus absent',user_page.get_by_text('用户管理',exact=True).count()==0 and user_page.get_by_text('操作审计',exact=True).count()==0)
  for path in ['/system/users','/system/roles','/system/audit','/ai/agent-token']:
   user_page.goto(ORIGIN+path);user_page.wait_for_url('**/403');check('ordinary direct route denied '+path)
  for path in ['/rbac/users/','/rbac/roles/','/audit/logs/']:check('ordinary browser HTTP denied '+path,api(user_page,path)['status']==403)
  user_page.goto(ORIGIN+'/dashboard');user_page.set_viewport_size({'width':390,'height':844});user_page.wait_for_timeout(150);check('narrow viewport no document overflow',user_page.evaluate('document.documentElement.scrollWidth<=innerWidth'));user_page.screenshot(path=str(OUT/'ordinary-390.png'),full_page=True)
  user_context.close()
  login(page,'e2e-boss');page.goto(ORIGIN+'/system/roles');expect(page.get_by_text('系统角色 (root/user/boss) 编码不可修改、不可删除')).to_be_visible();check('BOSS read-only role controls',page.get_by_role('button',name='新建角色',exact=True).count()==0);page.goto(ORIGIN+'/system/users');expect(page.get_by_role('button',name='新建用户',exact=True)).to_be_visible();check('BOSS retains user management')
  from browser_security import exercise
  exercise(browser,page,context,ORIGIN,OUT,PASSWORD,login,api,check,report)
  check('no core AI provider requests',report['ai_requests']==[])
  check('no page JavaScript errors',report['page_errors']==[])
  page.screenshot(path=str(OUT/'boss-users-1440.png'),full_page=True);report['status']='pass';report['check_count']=len(report['checks']);context.close()
 except Exception as error:
  report['status']='fail';report['error_type']=type(error).__name__;report['error']=str(error)
  try:page.screenshot(path=str(OUT/'failure.png'),full_page=True)
  except Exception:pass
  raise
 finally:browser.close();report['browser_closed']=True;save()
