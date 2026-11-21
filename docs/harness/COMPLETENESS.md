# CORE-003 增量矩阵入口

当前有限AC为[TASK-CORE-003 S01–S09](TASK-CORE-003.md)，现状证据已写卡：旧已有CSRF/有效身份/改密撤其他/审计白名单分页，不重做。新缺口登录专用限速事件、句柄会话管理、安全CSV、SQLite恢复。最终状态只采用本版本冻结同run证据，旧C01–C15留原语义和事实，不挪编号。

---
# 通用后台有限完整性矩阵（CORE-002）

2026-11-19 Asia/Shanghai；实施 owner ram-admin-core；验收 lead + ram-core-review。此表是新范围事实/AC，不改旧 TOKEN-001 结论。状态 existing/fix/missing/deferred 表示发现分类，不表示通过。证据待每阶段真实执行后追加；不得把旧浏览器证据当本版本。

## 边界与事实源
- 实际源：backend/apps/rbac/{models,permissions,backends,services,views,serializers}、config/urls.py、apps/ai审批/Token链、frontend/src/router/index.ts、layouts/MainLayout.vue及system/dashboard组件。
- 支持：本机Windows + Django/DRF/SQLite + Vue/Arco，管理后台既有用户/角色/权限、会话、个人密码、审计、工作台与必要设置。默认无provider可运行，AI为可选扩展。
- 排除：ERP/多租户/财务/新业务域、远端/网站/部署/CI、生产验收、外部AI实调。不是以缺能力排除核心HTTP/browser。
- 旧保护：.1与review-20261117只读；546份源和证据已逐文件SHA复制；清单baseline/harness.1-protection.json；无node_modules/dist/DB/env/账号/密钥复制。

| ID/阶段 | 现状分类与真实缺口 | 有限实现边界/可观察AC | owner | 证据/状态 |
|---|---|---|---|---|
| C01/P1 | fix：已有session登录/退出；DRF SessionAuthentication已拒inactive（review纠正，不称外部越权）；内部effective身份需统一；登录CSRF需真实负测 | 每请求有效用户；停用/软删session失效；login显式CSRF保护；匿名/伪CSRF拒绝无登录副作用；注销失效 | core | not-run |
| C02/P1 | fix：RBAC读操作全体认证放行；has_role未过滤live role；actor=None内部fail-open | 服务端按动作权限默认拒绝；effective user+live role+live link；None/普通/失权actor不能写；root/superuser与BOSS保护保持 | core | not-run |
| C03/P1 | fix：Token v2已25测试；审批丢issuer、首root占位；执行器不传actor | 保留v2摘要allowlist/当前issuer/专用secret；提交归真实issuer；review需当前root；显式reviewer actor，拒绝任意内部绕过；旧审批数据保留不虚构issuer | core | not-run |
| C04/P1 | fix：审批审计params可含password；执行异常捕获可能半完成 | 提交与审计原子；动作/执行/审计savepoint；敏感参数不进审计或查询；失败不留用户变更；历史归属unknown明确表示 | core | not-run |
| C05/P2 | fix：用户CRUD/重置已有；role_ids无live/去重校验、软删关联遗留 | 用户创建编辑分页搜索/重置契约一致；非法/重复/软删role 400无副作用；唯一字段含墓碑预留冲突409；删除解绑且事务；最后有效root不可删除/停用/撤权 | core | not-run |
| C06/P2 | fix：角色CRUD/唯一角色已有；多人false→true无检查；删除隐式解除 | 系统code不可改/删除；BOSS不能管理root/BOSS；自定义role权限不能越权授予；unique占用与切换一致；已分配角色删除409需先解绑 | core | not-run |
| C07/P2 | missing：RolePermission仅存储预留；user-info permissions=[]；无真实权限菜单契约 | 闭集现有后台权限目录；root全权/BOSS有界管理；可授予不超actor；菜单/route与API同一权限；不增加动态菜单数据库/业务系统 | core | not-run |
| C08/P2 | missing：普通audit模块仅apps.py，/api/audit/logs/404 | 新真实只读审计查询：最小audit.read、分页筛选；真实actor/动作/对象/时间/结果，固定安全字段无密码token/prompt；用户/角色写与日志同事务 | core | not-run |
| C09/P3 | missing：无个人修改密码/设置路由 | 设置以本人密码变更+公开只读运行能力为实际功能；校验旧密码/强度；他人ID不可改；更新session哈希保持当前会话、其他旧session失效；不造系统配置大模型 | core | not-run |
| C10/P3 | fix：工作台统计来自ORM但页面是否假活动待核 | 工作台只展示真实计数/有权操作，无假图表/活动；无权限不泄露管理数据 | core | not-run |
| C11/P3 | fix：全局布局默认provider请求/告警；AI为主导航 | 默认核心无AI请求/依赖；显式可选入口保留Token/审批安全；关闭UI不豁免API鉴权、不删旧数据 | core | not-run |
| C12/P3 | fix：loading/error/empty/403/404各页需补齐 | 列表/对话框真实成功与错误、空态可重试、阻止重复提交；root/非root导航/直达一致；窄屏键盘浏览器 | core | not-run |
| C13/P3 | fix：默认开发Django secret存在 | 明确local/test/production settings；生产缺secret/hosts/安全配置拒启，不以测试关闭生产检查；无默认密码/秘密落盘 | core | not-run |
| C14/P4 | existing+fix：25Token/27BOSS/14迁移/14路由统一verify已有，无新版真HTTP/browser | 保留原断言原测试载荷；必要契约变化明确补更强测试；统一入口分local/browser/production边界；独立run日志、源/依赖摘要；随机loopback端口隔离库；所有服务finally停止 | core | not-run |
| C15 | deferred：外部AI/生产恢复/容量/远端门禁 | 非核心，明确未验；本地通过不自宣生产PASS；由lead安排独审 | lead | not-run |

## 最终验证索引（实现已落盘，独审pending）
下表的not-run是开工时状态，当前结果统一以最终verify run的summary/commands/source-inventory与live-binding为准，不回填历史绿灯。P1/P2中间31/51测试和首次12HTTP+28browser证据均保留，但最终只采用完整fresh run。

| AC | 最终run内直接证据/断言 | 实现状态 |
|---|---|---|
| C01 | django-all.stderr：CoreSessionTests；live-summary真实HTTP CSRF/Origin/改密双session+browser session bootstrap/logout | implemented；待最终verify和独审 |
| C02 | CoreSecurity/ManagementTests；原25Token；BOSS28；禁inactive管理员及高权限custom目标接管，API+service | implemented；待最终verify和独审 |
| C03 | TokenTests原字节；ApprovalExecutionTests+two-connection parallel approval；core-boundaries历史unknown | implemented；待最终verify和独审 |
| C04 | 审批hash注入/执行失败savepoint/审计失败rollback；0003旧明文/terminal清理；安全查询字段 | implemented；待最终verify和独审 |
| C05 | invalid_roles/tombstone/last_root/delete_releases+two-connection最后root/唯一角色；browser CRUD/search/末页删除 | implemented；待最终verify和独审 |
| C06 | role_unique/in_use/system/BOSS/权限下放；role editor不能剥高权限role；browser角色创建编辑 | implemented；待最终verify和独审 |
| C07 | permissions闭集/API；explicit_audit_read/custom_writer；browser root/BOSS/user菜单与direct route负测 | implemented；待最终verify和独审 |
| C08 | audit字段白名单/分页筛选/403/显式reader200/事务rollback；browser实际查询 | implemented；待最终verify和独审 |
| C09 | 真实settings/change-password、双session与旧密码错误；browser个人改密reload | implemented；待最终verify和独审 |
| C10 | dashboard真实ORM计数、0不丢、无权限不泄漏，browser工作台 | implemented；待最终verify和独审 |
| C11 | AI_UI_ENABLED默认false，browser ai_requests=[]；原Token25/旧审批迁移保护 | implemented；待最终verify和独审 |
| C12 | browser错误503重试/空态/ESC/键盘Enter/重复输入/末页删除/390无overflow；JS errors=[] | implemented；待最终verify和独审 |
| C13 | core-boundaries生产settings缺/弱secret/hosts/DB拒启与明确配置成功，共15边界包含迁移 | implemented；待最终verify和独审 |
| C14 | commands中Token25、discovery、BOSS28、原迁移14、路由14、ci/typecheck/build、HTTP/browser；source-protection旧546/146+ZIP/vendor129 | implemented；待最终verify和独审 |
| C15 | 外部AI/生产/真机视觉/其他DB/远端明确not-run；不自宣生产PASS | deferred，lead负责后续 |

## 冻结契约（实现前制定，实施按此验证）
1. root=有效active非删用户且superuser或live root关联；BOSS=有效boss且非root。普通用户仅本人会话/设置和获明确授权的菜单/动作。内置root/boss不接受自定义permission提升其固定边界；未知permission拒绝。
2. 所有用户/角色mutation service要求显式actor且重读数据库身份，actor=None一律403；初始化只用显式管理命令直接模型bootstrap，不把内部信任标志做后门。审批执行使用本次reviewer，不继承任意params actor。
3. 最后有效root保护作用于删除/禁用/撤销root；预检+事务，SQLite代表性并发限制如未压力验证如实列出。BOSS不能目标root/BOSS、不能授予root/BOSS或超自身权限。
4. 软删唯一username/email/name/code继续由数据库全局预留，返回409而不恢复墓碑；role关联只接受live role，删除用户解除全部关联；用户/role/permission写+审计同事务。
5. 审批新增submitted_by可空保留旧行，旧NULL表示unknown不回填假归属；新提交必须真issuer，提交create_user密码仅转为Django单向password_digest供受控执行，拒绝外部摘要注入；执行/拒绝/失败终态清除摘要，查询仅白名单安全字段，密码永不写AI审计prompt。旧明文经0003单向清理，不宣称可还原或历史从未泄露。对旧敏感审计采用脱敏迁移/读边界，不能声称原历史从未泄露。
6. 失败记录保留；本机合成测试密码只进进程内存，不持久化账号或secret；旧venv仅解释器依赖，不打开旧DB/env。
