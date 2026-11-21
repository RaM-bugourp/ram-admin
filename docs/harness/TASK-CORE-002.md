# CORE-002 通用后台完整性闭环

2026-11-19 Asia/Shanghai（用户采样时区），阶段 planning→implementation；owner/executor ram-admin-core；lead协调与只读验收，ram-core-review独立审查；联系使用agent消息。

## 授权、事实与路由
- 用户本轮完整开发授权+lead已确认.2：仅 C:/c/Users/Rick/ram-admin-0.2.0-harness.2 内产品/规划/测试/证据、本地独立git无提交远端、临时合成数据与loopback随机端口。禁改.1/review旧根、网站、父Git、DSH、全局MEMORY；不读取旧env/账户/DB，不请求sandbox_permissions。
- 来源：.1已验digest 8f29f49f1ea6c39e72291a874fd5b7a82036cb0372276a88fe02994ae2e94fe1；baseline/harness.1-protection.json复制546项SHA；独立git dev/0.2.0-harness.2无remote，所有本轮dirty归core，无其他写入者。旧证据保留不冒充新版本通过。
- 规划事实源：PLAN与COMPLETENESS；旧TOKEN-001、BRIDGE、REPORT仍历史权威。详细finite AC C01–C15见COMPLETENESS。
- 命中fix/feature/security/api/data/ui/build/docs；web-api/sqlite/web-frontend；schema/local-files/local-tests；has_frontend=true/has_database=true由源码确认；no remote deployment由授权确认。
- 冻结1.0.0必读：START-HERE/adoption/routing/ownership/pr-boundaries/test-boundaries/evidence/task-lifecycle/capabilities；platforms README、web README/api-config/data/operations/frontend/verify，模板planning-bridge/task-card；本轮实读。selection/evidence/overview/maintenance及既有TASK/REPORT/DEVELOPMENT在对应阶段补读。不更改vendor。规则RAM-SCOPE/API/DATA/UI/BUILD/DOC-001 rev1继续advisory，扩CORE契约不是运行时Harness门禁。

## P1密码与历史兼容补充（lead已要求）
- create_user在提交边界使用现有UserCreateSerializer校验并用Django make_password单向哈希；存储内部字段password_digest，不存原password；外部params中password_digest/password_hash等未知字段拒绝，不允许任意哈希注入。执行只从已持久审批取内部digest，经Django identify_hasher校验后显式消费；普通UserService仍仅明文输入，专用approval入口必须当前root并校验已批准记录/绑定reviewer，不能成为actor=None后门。
- 不自制加密、不持久化明文测试账号。新审批响应params仅安全字段+password设为[REDACTED]；执行结束清除digest，日志无params/自由文本敏感值。
- 新增迁移处理旧create_user.params.password→Django make_password、清除旧注入hash字段；旧AI agent_submission prompt替换固定安全摘要；旧归属留NULL unknown，不伪造。迁移向后不可恢复明文；旧审批仍可由当前root执行。
- AC：数据库/响应/AI审计均不含合成明文；执行后用户check_password成功（不双哈希）；伪造digest提交400；历史fixture迁移保留审批/正确密码且移除明文；失败保存点回滚用户与管理审计。

## 阶段/AC/停止与恢复
| 阶段 | 交付物和依赖 | 可观察正向AC | 负向AC/恢复 |
|---|---|---|---|
| P0保护与规划 | 新根、来源清单、COMPLETENESS、任务/桥接/owner/路由 | 源证据逐SHA；finite矩阵逐项existing/fix/missing/deferred+owner | 目标存在/秘密/越界停止；只读确认，不覆盖 |
| P1安全根因 | effective身份/权限、显式actor、归属与审计脱敏、保存点；依赖P0 | 当前root/BOSS有界；token真issuer→pending→root review执行；审计实际actor；原25Token不退化 | None/普通/停用/删角色拒绝且无副作用；注入失败不留用户；敏感字段不出查询/日志 |
| P2核心管理 | 用户角色权限目录、唯一性/软删生命周期、通用审计；依赖P1 | CRUD/分页/搜索/权限菜单与真实API一致；审计查询过滤最小权限；最后root安全 | duplicate/非法role 400/409非500；越权/已用role删除拒绝；审计故障回滚；原27BOSS和14迁移保留 |
| P3消费与配置 | profile/password、设置/工作台、error/loading/empty、AI可选、production检查 | 无provider默认核心完整；密码变更/退出/刷新；真实指标；错误可重试 | 非root直达403、重复提交防止；缺生产secret拒启且不造密码 |
| P4真实验证与交接 | verify统一入口、本地+HTTP/browser分离、机器清单/digest/日志/交接 | 原25/27/14/14不弱化；定向新增；npm ci/typecheck/build；真实Edge/Playwright root/非root核心流程 | 每run独立保留失败；随机新端口/隔离库；finally关闭进程/browser；旧源SHA重核；lead独审前不宣生产PASS |

## 验证命令与目标
- cwd新根；旧解释器仅依赖：C:/c/Users/Rick/ram-admin-review-20261117/venv/Scripts/python.exe。统一入口 `python tools/verify.py --python <该路径>`；新增focused入口将附最终RUNBOOK。
- settings.test内存/隔离SQLite，AI_PROVIDERS=[]，webhook空，随机进程密钥，UTF8；npm cache与TEMP/TMP/TMPDIR固定本根独占run。现存8000/5173不碰。
- 真HTTP: 新子进程Django runserver --noreload，loopback随机空闲端口、全新临时SQLite；requests/urllib cookie+CSRF正负；不是APIClient。真browser: 先核Playwright+Edge，真实UI登录/用户/角色/审计/个人密码/退出与非root负例、窄屏、页面错误。
- 生产只检查显式settings配置拒绝/接受，不部署、不读真实生产秘密；未知拓扑/外部AI/真人手机/远端门禁/并发容量列not-run不假N/A。
- 每阶段真实命令/计数/退出码给lead；每run原始stdout/stderr、commands、summary、版本、依赖/源摘要及失败证据；代码/环境/产物变化相关旧证据失效。
- 停止：目标超新根、需真实业务凭据、发布/生产/不可用浏览器工具不绕过；报告lead，继续独立获准工作。回退仅新根针对本轮差异，不旧二进制回退Token；迁移只加新文件，优先前滚。
