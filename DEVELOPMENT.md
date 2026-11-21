# 当前本地fork 0.3.0-dev.1 / CORE-003

唯一writer ram-core-next；lead只协调/只读独验。新根由当前实核.2净化复制336源，基线digest fc36e69bb2638991437a384257d0e5f89b02215b2e97b26fc5eb431f55774941；保护baseline/harness.2-protection.json。无remote/commit/push，不是上游发布；下方.2说明属于历史。当前卡docs/harness/TASK-CORE-003.md。

## 一键独立完整复跑（新PowerShell，cwd本新根）
```powershell
Set-Location 'C:\c\Users\Rick\ram-admin-0.3.0-dev.1'
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$py='C:\c\Users\Rick\ram-admin-review-20261117\venv\Scripts\python.exe'
$browserPy='C:\Users\Rick\AppData\Local\Programs\Python\Python311\python.exe'
& $py tools/verify.py --python $py --browser-python $browserPy
if ($LASTEXITCODE -ne 0) { throw 'Verification failed; retain new run logs' }
```
旧venv只复用依赖，不读旧DB/env/账号。默认fresh npm ci --ignore-scripts/typecheck/build；独占本根TEMP/npm cache；新合成库/随机loopback端口不打8000/5173/15173/18000/18791/18792。每run独立证据保留失败。原Token25/BOSS28全文件/原test_core与并发/迁移14/路由14保护。discovery含focused25不是相加唯一数。APIClient不称browser。

## 当前新增契约
- 登录账号8次/来源40次/300秒固定窗口；信任REMOTE_ADDR不读XFF（当前不支持受信代理转发地址，部署代理需另行明确可信链）。账号key casefold与来源都HMAC；成功清账号不清来源；未知/错密/停用同形401与标准Django dummy hash；429带Retry-After；窗口恢复，不改is_active/不永久锁root。10000桶过期清理/容量fail-closed503，受限source不再为新账号分配桶；每桶窗口至多1条limited事件。非DDoS/跨部署容量保证。
- 个人设置安全中心清单仅UUID/时间/当前标记，不含raw session_key/cookie/IP/UA。本人可单撤或退出其他；root-only全撤target包括自己当前（UI明确确认并回登录），非root/BOSS/custom writer皆拒。旧未登记session扫描登记全撤、Django SECRET_KEY_FALLBACKS有效auth hash兼容。失效密码hash旧session不显示、不再可用；过期registry清理；改密保当前仍按旧契约。撤销拒绝审计失败并事务回滚；不承诺终止已授权在途请求。清单为旧数据兼容内部扫描，容量/多worker未作生产承诺。
- 审计列表/CSV共享actor_id/start/end/action/resource/outcome严格过滤器；时间带时区、非法日历/倒置/重复/未知400；CSV最多5000行超限拒绝不截断，UTF8 BOM/标准引用、控制字符清洗/公式前缀中和，固定白名单无email/IP/UA/任意payload/token/password/no-store；下载仅audit.read。

## 本地私有SQLite运维（无HTTP文件接口）
仅本机有OS数据库权限的操作者。按自己明确获准settings配置运行，不可用旧demo账号/env/DB测试。调用入口：
```powershell
# $settings 必须是操作者明确配置的目标，不能把本例当生产授权
& $py backend/manage.py local_ops health --settings=$settings
& $py backend/manage.py local_ops backup --settings=$settings
& $py backend/manage.py local_ops restore --backup-id <返回的32hexID> --settings=$settings
```
备份固定本根`.private-ops/backups/<id>/database.sqlite3`与manifest；隔离恢复固定`.private-ops/restores/<id>/database.sqlite3`，已存在拒绝，不替换live。ID不接受任意路径，所有祖先拒重解析/junction；ignored私有DACL只有当前SID/SYSTEM/Administrators（非Windows0700/0600），私有化失败停止。`health`只结构化bool/count/固定错误，不输出路径或秘密。保留/删除由有权操作者按精确ID执行，不自动定期删除或开放下载。

SQLite backup在线一致性，不是复制live主文件；全schema来自独立子进程**default内存**真实migration结果，父配置数据库绝不用于参考migrate；继承环境剥DB/DATABASE/DJANGO/AI/RAM_TEST/provider/PYTHONPATH等，强制config.settings.test并assert memory，纯JSON返回schema。历史0003未改。RunPython历史无using(default)曾使早期alias参考方案重写本次合成库，旧ops42及更早**不能**当无副作用证明；已修独立default内存并66断言cold canary全列不变。本方案不是OS沙箱；未来新增AppConfig.ready/router/启动hook/迁移外部I/O必须使证据失效并复审。超时/非0/非JSON/错误形状failclosed，无不完整schema fallback。

备份含密码hash、会话与Token摘要/业务数据！同Django/Token secret下恢复的session/Token可能继续有效；绝不把副本公开或起公网服务。备份不含应用secret，需操作者独立保护配置/密钥与保留策略。恢复验证全schema/索引约束/迁移账本/integrity/FK及每表全列，敏感hash只内部比对；它是本机SQLite隔离恢复，不等于生产RPO/RTO/跨DB/灾备批准。需要live切换/生产演练必须另行授权。

## 当前验证索引与未验
68ops隔离/全部junction清理回归、86discovery、真实HTTP27/Edge45已阶段实跑；最终统一fresh run/冻结digest只看docs/harness/evidence最新完整summary，早期阶段结果不冒充冻结。最终CORE-003报告落在docs/harness/evidence/CORE-003-DELIVERY.md（证据目录不入源码digest）。人工视觉/真人手机/外部Provider/生产部署恢复/中断迁移/容量/其他DB/远端CI/签名许可和旧eslint缺依赖均未验，不自宣生产安全PASS。

---
## 以下.2开发说明保留为历史

# 独立本地开发 0.2.0-harness.2

本根唯一writer ram-admin-core；lead只协调与独立验收。未发布，无remote/commit，不动.1/review旧根、父Git、网站、DSH或全局MEMORY。先读AGENTS、docs/harness/PLAN、COMPLETENESS、TASK-CORE-002。冻结Harness1.0.0是advisory，离线绿不是生产批准。

## 当前机器一键完整验证（PowerShell，cwd本根）
```powershell
Set-Location 'C:\c\Users\Rick\ram-admin-0.2.0-harness.2'
$env:PYTHONUTF8='1'
$py='C:\c\Users\Rick\ram-admin-review-20261117\venv\Scripts\python.exe'
$browserPy='C:\Users\Rick\AppData\Local\Programs\Python\Python311\python.exe'
& $py tools/verify.py --python $py --browser-python $browserPy
if ($LASTEXITCODE -ne 0) { throw 'Verification failed; inspect new evidence run' }
```
- 旧venv仅复用Python/Django依赖，不读旧DB/env/账号。browserPy是已安装Playwright的Python，实际Edge channel msedge。新机器可建本根独立venv安装backend/requirements.txt，另提供有Playwright的Python+Edge；实际freeze记录每run，不声称后端宽范围已锁死。
- 默认npm ci --ignore-scripts、typecheck/build；npm cache和所有TEMP/TMP/TMPDIR使用本根独占run。`--skip-install`仅快速复测，不能声称本次干净依赖安装。
- 省略--browser-python只做本地组件/迁移/构建，Harness required browser证据not-run/exit2，统一脚本本地检查exit0不等整体完成。提供该参数才真正启随机loopback HTTP+Edge。
- 每run独立docs/harness/evidence/时间戳；原stdout/stderr、commands、summary、source-inventory/changes、依赖/产物/路由摘要和cleanup保存，失败不覆盖；latest仅索引，不是永久批准。源码/环境/配置/目标变化相关证据失效。

## 拆分复验（输出请用新目录，不覆盖既有证据）
```powershell
& $py tools/run_logged.py --label discovery -- $py backend/manage.py test apps.rbac apps.ai --settings=config.settings.test -v 2
& $py tools/run_logged.py --label migration -- $py tools/verify_migrations.py --output docs/harness/evidence/manual-new-migration.json
& $py tools/run_logged.py --label core-boundaries -- $py tools/verify_core_boundaries.py --output docs/harness/evidence/manual-new-boundaries.json
& $py tools/run_logged.py --label boss -- $py tools/verify_boss.py --output docs/harness/evidence/manual-new-boss.json
& $py tools/run_logged.py --label live -- $py tools/verify_live.py --python $py --browser-python $browserPy
```
Token原25测试不改；原BOSS前26安全断言不改，旧第27为audit404观察，C08获准实现后升级root200安全字段+ordinary403（共28），原脚本与SHA保存在baseline；原14迁移、14路由保持。新增核心/session/approval/并发与0003历史fixture/production settings检查真实执行。

## 测试与运行边界
- config.settings.test：隔离内存/测试SQLite、进程随机secret、providers=[]、无webhook；APIClient不是浏览器。
- config.settings.integration：必须显式本根.tmp绝对SQLite路径及随机进程secret，只合成数据；verify_live使用新随机空闲端口，不打旧8000/5173；代理仅服务frontend/dist+本次backend；try/finally关闭Edge/HTTP/进程并删除隔离DB。凭据只在进程环境/内存，不输出或交付账号文件。
- config.settings.dev：进程随机Django密钥（未显式指定时重启session失效），仅localhost调试，不公网。
- config.settings.production：真实独立配置，显式50+字符高多样secret、非通配hosts、绝对DB路径，否则拒启；DEBUG false、secure cookies、HTTPS/HSTS。测试只验证配置导入正反，未部署、不推测代理信任/TLS拓扑/生产恢复。没有默认密码。

## 核心权限与数据
权限闭集dashboard.read/users.read/users.write/roles.read/roles.write/audit.read；root或superuser全权，BOSS保留用户管理/角色只读，不可管理root/BOSS/超自身权限；普通用户仅本人会话设置及显式授权。菜单/路由消费user-info.permissions，刷新先bootstrap，不依赖provider。AI_UI_ENABLED默认false；API安全独立保留不是隐藏后门，启用可选UI须显式环境配置并保持root权限。
服务写入一律显式当前actor，None/失权/软删角色拒绝。软删username/email/role name/code墓碑预留409；删用户解绑；有用户的role先解绑才能删；最后有效root不可删/停用/撤角色。SQLite事务首写预留+两连接竞争测试覆盖最后root/唯一分配/同审批；不是其他数据库/生产压力保证。
通用审计固定安全字段，不存任意payload；成功mutation与日志同事务。拒绝/失败在服务rollback后独立记录安全事件，审计不可用时日志只报固定错误不泄密，不假称记录已持久化。

## Token与审批兼容
- v2随机+完整摘要allowlist/当前issuer/专用32+字符secret fail-closed保留；旧四段全部失效需重发，不回旧鉴权。已撤销永久，新请求拒绝，不取消已授权在途请求。
- 新approval.submitted_by真issuer；历史NULL=unknown不伪造首root；review用当前root，非None内部绕过，条件claim防重执行，执行savepoint失败不半写。
- create_user提交serializer校验后Django make_password单向摘要，外部不能传password_digest/password_hash/encoded；摘要只受控审批消费且不双哈希，执行/拒绝/失败清除；响应白名单脱敏。0003保留业务行但清理旧明文/旧agent prompt/评论，旧pending密码转摘要；单向不可恢复明文，不宣称历史从未泄露。
- 0001/0002不改；0003新增来源与历史清理。0002逆向丢凭证账本，禁止生产逆迁移或旧二进制回退；优先前滚，生产备份/恢复/流量切换另需授权。

## 明确未验
真实外部AI、真人手机/人工视觉/辅助技术、生产部署/恢复/中断迁移/容量/其他DB与分布式多worker、取消在途Token请求、远端CI/保护/签名、许可证和漏洞总审未验。eslint旧脚本缺依赖不报lint通过。最终由lead安排独立验收，不自宣生产PASS。

清理纠正：早期ops66/旧42的created_private_folders_removed没有覆盖被覆盖变量遗留的junction，不能据此称全部链接已清。2026-11-20已逐绝对路径/type/target核4个本轮断链并仅删junction本身，evidence/junction-cleanup-before/after.json留存；新runner独立links清单finally清理并含异常分支，cleanup.all_tracked_links_removed必须true。此前WinError32残合成DB目录已精确清理并记录failed-fixture-cleanup.json。
