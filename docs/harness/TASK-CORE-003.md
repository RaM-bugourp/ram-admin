# CORE-003 账户安全与本机可恢复运维

2026-11-20 Asia/Shanghai；owner/executor/唯一writer ram-core-next；lead仅协调与只读独验；ram-core-next-review只读安全复核。状态 planning → implementation，当前不是ready或生产安全PASS。

## 授权/现状/事实源
- 用户明确继续ramadmin纯后台，lead确认本轮3关联闭环。唯一写根 C:/c/Users/Rick/ram-admin-0.3.0-dev.1；无remote/commit/push/部署/隧道授权。不改订单/网站/.2/.1/review旧源码/DB/env/账号/父Git/DSH/全局MEMORY，不停止旧服务。
- 新根事先确认不存在；从.2当前实核336源码逐SHA净化复制；digest fc36e69bb2638991437a384257d0e5f89b02215b2e97b26fc5eb431f55774941；基线保护 baseline/harness.2-protection.json。独立Git dev/0.3.0-dev.1仅init，全部新根差异归本writer，不伪称上游发布；沿fork 0.2.0-harness.2版本线。旧146源/ZIP、.1、原25Token/原BOSS前26/原迁移14/路由14与vendor129保护延续。
- .2外置独验 INDEPENDENT-ACCEPTANCE.md证实C01–C14本地有限通过。旧COMPLETENESS/CORE-002、PLAN历史编号语义不改；本卡仅新增S01–S09。
- 真实缺口证据：auth_views.py:29–39登录无专门限速或失败事件；common/exceptions.py已有通用request.rejected，不能说失败完全无审计；仅改密能撤其他session，无会话管理；audit/views.py已有条件分页筛选但无CSV；源码无SQLite backup/恢复CLI。已有身份/CSRF/改密/闭集RBAC不重做。

## 目标/非目标与路由并集
1. 账户安全中心：持久有限窗口登录防暴力/安全事件、本人查看安全会话清单及退出其他会话、root有界全撤用户session；角色/停用逐请求生效。
2. 审计运营：复用现有筛选器、错误校验与最小audit.read，增加白名单/数量上限/防公式CSV，关键安全成功事件与操作同事务，失败事件匿名不伪造root。
3. 本机CLI运维：SQLite在线一致性backup、私有ignored固定根/备份ID、隔离新目标恢复、全表/列/迁移与内部敏感hash比对。绝不新增HTTP文件接口或替换live DB。
- 非目标：ERP/订单/租户/支付/AI主线/任意动态权限树、生产拓扑/发布/容量/跨DB/多worker保证、外部账号模型、远端CI/许可或安全总审。无外部账号/服务器则not-run。
- 路由 fix/feature/security/api/data/ui/build/docs + 本地CLI；平台web-api/sqlite/web-frontend/Windows，W1/W2/W3/W4/W6/W7/W9；schema/local-files/local-tests。has_frontend/has_database=true由实际源码确认；no_deployment=true来自授权，不据此删本地HTTP/Edge。RAM-SCOPE/API/DATA/UI/BUILD/DOC-001 rev1 advisory沿用。
- 实读全局AGENTS/MEMORY最新、DSH-START-HERE、冻结1.0.0 START-HERE/adoption/routing/ownership/pr-boundaries/test-boundaries/evidence、platforms README与web README/api-config/data/operations/frontend/verify、planning-bridge/task-card模板及既有项目关键正文；其余公共页实施/验证前补读。vendor不改。unknown/无授权停止全部相关任务，冲突暂停相交动作给lead，范围扩大重路由。

## 冻结安全契约
- 仅信任REMOTE_ADDR，不信XFF；来源与归一账号两个有限窗口，key仅HMAC摘要，未知账号/错误密码/停用同形401，限流同形429+Retry-After。未知账号也做密码hash工作；不泄露原始账号/IP/密码。限流不会改is_active、不永久锁root；窗口自动恢复；成功仅清相应账号计数而不能清来源计数绕过喷洒；持久表有过期清理与容量上限，容量/DB错误fail-closed 503；更新事务首写/CAS原子。CSRF/Origin先于任何限流/认证副作用。
- 会话句柄为独立随机UUID，不是session_key/token/cookie编码。清单只回句柄/时间/当前标记，无原key/data/IP/UA/密码。只本人清单/退出其他；管理员全撤root-only并复读当前actor/目标，目标最后root资格不受撤销影响、可重新登录；全撤包括目标所有现有session，若目标就是自己当前也退出。本人退出其他保留当前，与改密保当前兼容。既有旧session缺登记仍可安全等效全撤，不能留后门。单句柄跨人不枚举且幂等。
- 每请求有效身份/角色仍实时；撤session不通过重置密码/hash或只前端隐藏实现；审计故障必须拒绝关键成功操作，不能撤完假报失败却无审计。
- CSV复用列表相同过滤：非法/未知/起止倒置拒绝400；固定字段无email/IP/UA/请求payload/密码/token；所有文本前导空白/控制字符后=+-@需中和，CR/LF/tab清洗防跨行/公式，UTF8 BOM+标准csv quoting；超过明确行上限拒绝不静默截断。导出本身留安全事件。
- 备份含秘密，固定本根ignored私有目录，仅本地CLI；Windows ACL当前用户+SYSTEM/Administrators，POSIX 0700/0600；拒绝目录链接/junction/ID路径注入，目的地exist即拒绝，SQLite backup非复制live文件。恢复只独立新目录并核schema/integrity/FK/所有表逐行内部一致；密码hash仅内部比较不输出。备份不含Django/Token密钥，恢复鉴权需同一获准进程配置。

## 阶段与可观察AC
| 阶段/依赖 | AC与交付 | 通过/失败与停止恢复 | owner/验收 |
|---|---|---|---|
| P0来源规划 | S01保护/版本/本卡/桥接/路由owner | 原336逐SHA强相等；无秘密复制；新Git无remote/commit。冲突不覆盖 | next/lead |
| P1账户审计 | S02持久限速；S03会话；S04角色撤销/目标保护；S05安全CSV | API+service正反、受控时钟窗口恢复/容量/并发、双session/非root/审计故障；保留原断言；失败日志不抹 | next/review+lead |
| P2恢复UI | S06在线backup+隔离恢复；S07安全中心/管理撤销/审计过滤导出真实消费 | 合成SQLite所有业务列+迁移元数据与hash内部相等、损坏/覆盖/路径/权限负测；Edge新功能与旧核心流程 | next/review+lead |
| P3冻结复验 | S08统一verify fresh；S09报告/digest/清理 | fresh npm ci/typecheck/build、Django check/drift/discovery、Token25/BOSS28/迁移14/路由14/生产15、真实HTTP+Edge；同run源码首尾强相等及原件保护。完整本地目标后才交独验，不自称生产PASS | next/lead安排独验 |

## 验证与阻碍
- cwd本新根；backend Python C:/c/Users/Rick/ram-admin-review-20261117/venv/Scripts/python.exe仅复用依赖；browser Python C:/Users/Rick/AppData/Local/Programs/Python/Python311/python.exe + installed Edge。旧DB/env/账号不读。
- 统一命令 `$env:PYTHONUTF8='1'; & $py tools/verify.py --python $py --browser-python $browserPy`，定向 `& $py backend/manage.py test apps.rbac.test_security_ops --settings=config.settings.test -v 2`；CLI恢复验证由统一入口扩入。每次新evidence目录保存commands/stdout/stderr/源码摘要/cleanup，失败保留。
- 新合成库与随机loopback，明确避开8000/5173/15173/18000/18791/18792；本根独占TEMP/TMP/npm cache+UTF8。APIClient不是browser；真实HTTP urllib与Edge分别报告。
- 关键负例：CSRF/Origin/伪XFF/未知账户同形、限流过期恢复/容量/并发；双session/跨用户句柄/role撤销/inactive/非root/admin目标边界；CSV危险前缀/CRLF/上限/PII；备份损坏/链接/覆盖/source同file拒绝。
- 未验：真实外部Provider、生产安装恢复/中断迁移/容量/跨DB多worker、真人设备/人工视觉、远端CI/签名/许可eslint缺依赖。不能以mock称通过。
- 停止/回退：仅新根本轮差异；不旧二进制Token回退、不改已应用0001/0002/0003，仅新迁移。新源码变动重resolve+重跑；临时job/服务/Edge全部finally收集停止，不长期运行。结束向lead事实摘要，不写全局记忆。

## 实施收口与重路由记录（2026-11-20）
- 新0004会话/窗口与0005 bounded limited event迁移；旧0001/0002/0003字节保护。审计CSV共享过滤且修复实际非法日期ValueError与Accept:text/csv协商；未知账号用Django标准dummy hash。已有失败通用审计不重做，专用失败事件去重。
- 独审指出来源限额后分配新桶/limited日志放大，已先检查受限existing再分配+每桶窗口1事件，1000账号不增状态/其他来源root200/过期恢复并发回归通过。
- 独审指出只三表+ledger无法证明schema，改全schema SQL/index/unique对照；第一版secondary alias migrate会因旧RunPython默认路由串default，已废弃。已知调用全部tools/verify_ops本根.tmp全合成库，未调用旧或真实库。现独立子进程强制default memory，cold cache canary全表全列无写入66断言；未来hook/router/迁移外部IO必须重审，不是OS沙箱。旧42及更早ops不作为无副作用证明。
- 新增legacy从未GET清单直接全撤与SECRET_KEY_FALLBACKS有效hash扫描；修后discovery86=旧61+25新（focused Token25重叠不相加）。新真实HTTP27/Edge45阶段通过，早期hook遗漏旧12/32不冒称新功能。
- 当前所有源码改动使旧证据失效，接下来唯一完整fresh与源首尾强相等；S08/S09完成与digest以最终证据报告为准。补读overview/task-lifecycle/capabilities/platforms selection/evidence/maintenance；vendor未改，路由集合无新增外部权限。

- 最终清理补充：独立links清单/finally与故意异常分支2断言加入，ops66→68；早期cleanup未覆盖4个已断junction，后续逐path/type/target仅删除link并留纠正证据。第一次完整fresh虽86/66/27/45与SHA不变通过，因清理修复不是最终候选；最终须再完整fresh。harness.json project_id/owner同步本fork，原规则rev与旧14路由负例不弱化。
