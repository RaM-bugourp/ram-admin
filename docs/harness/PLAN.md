# CORE-003 / 0.3.0-dev.1当前增量

2026-11-20；唯一写根本版本，writer ram-core-next，lead协调/只读独验。本版本沿fork版本线不是上游发布。当前目标/非目标/真实缺口/有限AC/停止出口见[TASK-CORE-003](TASK-CORE-003.md)，原.2全336源当前重核digest fc36e69bb2638991437a384257d0e5f89b02215b2e97b26fc5eb431f55774941，保护baseline/harness.2-protection.json。3关联闭环为登录与会话安全、审计安全CSV、本地SQLite在线备份隔离恢复。以下旧规划编号/承诺保留历史，不复活旧证据为当前PASS。

---
# Ram-AdminX 后续开发规划

## 0. CORE-002 / 0.2.0-harness.2 当前有效增量（2026-11-19 Asia/Shanghai）
- 当前唯一写入根C:/c/Users/Rick/ram-admin-0.2.0-harness.2；从.1复制546项源/证据逐SHA核对，保护清单baseline/harness.1-protection.json，独立Git无remote/commit。以下.1正文是历史，不将其路径/owner/非目标误用于本轮已批准扩大范围。
- 本轮用户明确完整通用后台开发；目标/非目标、实际缺口与分阶段AC以[COMPLETENESS](COMPLETENESS.md)及[TASK-CORE-002](TASK-CORE-002.md)为准。实施者ram-admin-core，lead只协调与只读独验，ram-core-review只读安全审查。
- 原G1/G2与AC1保护延续；原G3/Token契约和25Token/27BOSS/14迁移/14路由不削弱；原P4审批归属/actor/404等候选在本轮有新授权转入核心P1/P2，不回写旧非目标为已做。UI/API/DB/配置/真实HTTP+browser为本轮并集。
- 新非目标：ERP/多租户/财务等无事实业务、远端/网站/生产发布/DSH安装；AI降非核心可选但保留Token v2与旧审批数据兼容。未验或受阻不能填PASS。
- 新桥接：旧PLAN AC1→CORE P0来源保护；AC2→P1有效身份/显式actor/归属/脱敏和P2用户角色权限/审计；AC3→P3核心UI+P4真实HTTP/browser；AC4→P4本版本新截图与网络证据。执行器统一verify扩展，RAM规则rev1/advisory，具体证据每run独立。
- 回退/停止：仅新根本轮差异；不可回旧Token鉴权，不改旧迁移；DB只新迁移+隔离合成库，优先前滚。测试故障保留日志，不改断言造绿；最终待lead安排独审，不自宣生产PASS。

---
## .1 历史规划（下文保留原编号/承诺）

更新时间：2026-11-18，Asia/Shanghai。状态：本地预发行开发；Harness 1.0.0 advisory 试点，不是生产批准或运行时硬门禁。

## 1. 现状与事实源
- 新工作根 `C:/c/Users/Rick/ram-admin-0.2.0-harness.1`。旧工作根 `C:/c/Users/Rick/ram-admin-review-20261117` 保持只读。
- 上游固定 HEAD `3a4fd98bb98030c67261a4973048c6ba133a828e`，API ZIP 完整快照而非 Git 历史。来源为已净化 clean-source 146 文件；原压缩包 SHA256 `69f462c7eb086f0e62e49def92299f76a90c42fa4eea1384bfccaf42cf936141`。逐文件来源摘要见 [source-files](baseline/source-files.json)。
- frontend/package.json 与 lock 根为 `0.1.0`；进一步核查原README另自称 `v1.0.2`、保留历史changelog，不能误写成仅有一个版本来源，未验证其真实发布或全部功能。采用独立fork命名 `0.2.0-harness.1`，沿package序列，清楚标注本地预发行、不声称大于/替代上游1.0.2正式发布。README历史版本正文保留为历史，当前分支入口与VERSION/manifest一致。
- 技术栈 Django 5.2 / DRF / SQLite + Vue 3 / Arco / Vite 6；旧运行依赖实际 Python 3.13.15、Django 5.2.19、DRF 3.18.3、SQLite 3.53.1；本轮记录实跑版本，不保证任意范围依赖一致。
- 原九文件启动/登录与 BOSS 权限修复、27 条回归保留；原目标/AC 原文只读归档 [原 PLAN](baseline/PLAN-20261117.md)、[Review](baseline/REVIEW.md)、[PATCH](baseline/PATCH.json)、[QA](baseline/QA.json)。原账号文件/SQLite/env/secret 不复制。
- clean-source 无 AGENTS、无测试包、无独立 Git；新根确认后已独立 `git init`，无 remote，未暂存/提交。父 Git 不使用。新源码基线由 provenance/逐文件 SHA 标识，不伪称拥有原 HEAD 的本地 Git 历史。
- 旧架构/设计/实现仍是各自事实源：../../ARCHITECTURE.md、../ai-integration-design.md、../../backend、../../frontend。设计文档的承诺不是已实现证明。

## 2. 目标、非目标与授权
- G1：建立可独立继续开发的新源码版本；版本与来源可追踪，原件字节不变。
- G2：按冻结 1.0.0 落地现状、桥接、路由/owner、阶段 AC、验证和风险；机器输入与人工卡分离。
- G3：首切片闭环 Agent Token：持久化摘要/单 token 撤销、逐请求当前 issuer 权限、专用密钥缺失 fail-closed；保留 root 有效 session 独立访问。
- G4：实跑旧 27 回归、原生 Django 测试、迁移/API/安全回归与 frontend typecheck/build，留下命令/退出码/NOT-RUN，不把静态检查当 E2E。
- 获准依据：本会话用户明确“新版本、适配规范、开始后续开发”；lead 2026-11-18 确认此目录/版本/Token 范围，并要求兼容失效、迁移回退、脱敏、issuer负例。原作者二开授权由用户已确认；不推导依赖许可尽调完成。
- 允许：仅新根产品/测试/规划/证据、隔离临时合成数据、独立本地 Git 初始化、包依赖本地安装与验证。唯一实现写入人 ram-harness-dev；lead及独立验收只读/隔离测试。
- 禁止：旧 runtime/ZIP/快照、网站、DSH安装、全局记忆、父Git；远端 push/部署/保护配置/CI安装；读取业务凭据或持久化明文 token/secret；持续服务器。danger-full-access 不等于发布授权。
- 非目标：审批归属、actor=None、普通审计API、真实模型接入、UI新功能、生产加固总审、生产发布、全平台/性能/SBOM/许可结论。

## 3. 路由、owner、上下文
见 [ROUTING](ROUTING.md)、[OWNERS](OWNERS.md)、[任务卡](TASK-TOKEN-001.md)。冻结规范随副本保留在 vendor/1.0.0，不修改载荷。当前任务并集：缺陷/安全+API生产/消费+DB迁移+测试+版本/文档；W1/W2/W3/W4 与数据/运维恢复边界；frontend 有签发消费者 AIAgentTokenView.vue、api/modules/ai.ts 与 types/ai.ts；已复核旧UI只消费token/expires_in_hours，新增token_id为兼容附加字段；撤销先提供API不新增UI，仍执行类型检查与整体构建。

## 4. 旧规划桥接
[BRIDGE](BRIDGE.md) 引用原 AC1–4，不迁移编号、不撤销原验收、不把旧截图测试算作新版本 GUI。长期新规划事实源为本页；目标语义批准人为用户，经 lead 转达/验收。实施者不能代签最终批准。

## 5. 分阶段可观察 AC
| 阶段/owner | 交付物 | 通过/失败条件 | 依赖/停止与恢复 |
|---|---|---|---|
| P0 盘点/ram-harness-dev，lead验 | 新根、VERSION、provenance、baseline摘要 | 146来源文件可比、无秘密/DB拷入、旧根保护；版本一致 | 目的地冲突/身份不明即停，只读核实 |
| P1 规划/ram-harness-dev，lead验 | 本页、桥接、owner/路由、任务、manifest | 8类代表路由+unknown/conflict/unauthorized负例可解释；离线格式0不等产品PASS | 缺正文/授权/冲突暂停相关动作 |
| P2 Token/ram-harness-dev，独立review及lead验 | 模型+新增迁移、service/permission/API、测试 | 修前真实漏洞复现；修后有效token可提交pending；单token撤销幂等、其他token不受影响；旧token/缺密钥/篡改/过期/未知/停用/软删/失root/软删角色均拒绝且无approval/log副作用；无token/secret入日志或DB | 不用生产数据；新增范围先重路由；失败保留输出修复再验 |
| P3 验证/ram-harness-dev，lead独验 | 机器证据/原始日志/交接报告 | 定向+迁移+原27+Django discovery、typecheck/build实际退出0；精确数量；未执行明确标记 | 缺工具/目标则blocked，不能编PASS |
| P4 后续/lead协调 | 下一任务卡 | 由owner选择审批归属等下一切片；生产门禁独立授权 | 本轮不自扩展到其他缺口 |

## 6. 首切片契约与迁移/兼容
- 旧 token 格式实际为 `exp.issuer.agent.HMAC`，无登记、无撤销、同秒同agent重复。新发 `v2.<random uuid hex>.<HMAC>`，DB仅摘要、随机标识、issuer外键、agent_id、expires_at、created_at/revoked_at，不存明文或secret。签名用显式 AI_AGENT_TOKEN_SECRET（至少32字符），不回落 Django SECRET_KEY/固定默认。
- 旧四段token和任意未登记token在新版本一律拒绝：安全收紧的预发行兼容变更，必须迁移后由仍有效root重发，不能导入旧token伪登记。新签发接口保留 token/agent_id/expires_in_hours，新增 token_id（撤销句柄）；POST revoke/ {token_id: UUID} 仅有效root；重复/不存在同样200，避免枚举，单token粒度，所有root是同一管理域。
- 每请求数据库重读 issuer；active且非软删，superuser或未软删root角色+未软删关联。issuer被撤权后token立即拒绝；若恢复权限，未过期且未撤销token可恢复（不承诺不可逆失权吊销，需永久吊销调用revoke）。显式撤销不可复活。
- 认证失败不回退旧HMAC、默认secret、匿名成功；DB查询错误verify拒绝，issue/revoke不可假成功。已登录有效root session是原有独立授权，不是token失败降级；停用/软删root也拒绝。
- 新增0002迁移，不改0001。SQLite空库/旧schema→新schema、重复migrate、逆迁移→再前滚实测保留原审批业务行，核验Django迁移账本；逆向DropModel必丢新凭证登记，前滚后须重发，不宣称保留凭证账本；故障事务注入/生产恢复另列未跑。旧应用不会使用新登记表，可能重新接受旧无状态token，所以**禁止直接回退旧二进制继续服务**；仅在保持新版本fail-closed代码时可清空专用secret以停用Token，保留表/证据并优先前滚。旧版清空secret会回退弱密钥，绝不是安全停用方案，只有独立关闭Token入口或下线隔离后才能讨论旧版。孤立临时库逆迁移仅验证schema，不授权生产删除凭据数据。
- root_id等外部输入严格校验，不依赖前端隐藏按钮。Token仅签发响应出现，不在审计响应中写前缀。

## 7. 验证计划与证据
- 可重现统一入口：从新根运行 `python tools/verify.py --python C:/c/Users/Rick/ram-admin-review-20261117/venv/Scripts/python.exe`；该解释器仅复用包，不读/改旧项目数据；如干净机使用新venv+requirements。
- backend：专用config.settings.test，内存/临时SQLite，AI_PROVIDERS=[]、webhook空、随机进程密钥；Django TestCase/APIClient是真实ORM/DRF+SQLite测试，无监听端口，不冒充真实HTTP服务器/浏览器E2E。冻结旧27脚本独立移植测试入口保持原断言及404观察，不宣称404已修。
- frontend：npm ci --ignore-scripts，npx --no-install vue-tsc --noEmit，npm run build；锁版本不做无关升级。lint命令旧有但eslint依赖缺失，NOT-RUN，不冒充通过。
- Harness：随包工具lint/resolve；八族+unknown/constraint/unauthorized路由测试。人工MD非JSON输入；实际证据封套使用解析产生digest、当前时区、源码与产物摘要，保留fail/not-run。
- frontend消费者搜索、版本一致、来源保护、冻结vendor SHA核对与秘密文件扫描列入 verification；不输出环境变量或token。
- 新版GUI/真人手机/真实Provider/远端CI/保护/生产安装与恢复均not-run（涉及真实外部目标需另行授权或设备），不是本切片产品PASS。最终签署pending lead独立验收，不造人类签字。

## 8. 风险、未知、阻碍与后续
| ID | 状态/owner | 风险/下一步 |
|---|---|---|
| R1 | 未解决/lead | 审批审计归属仍占位；下一小切片需issuer归属需求与审计契约 |
| R2 | 未解决/lead | actor=None受信内部路径，不能宣称全服务默认拒绝；另立边界任务 |
| R3 | 已知/lead | 普通审计API404保留，不创建整模块 |
| R4 | unknown/用户+lead | 生产拓扑/消费者/secret分发/数据库版本未知，本轮不部署；升级时需明确重发窗口与业务停用 |
| R5 | not-run/lead | 人工GUI、真实模型/生产安全总审、依赖许可/漏洞/后端锁策略未完成 |
| R6 | advisory/lead | Harness无远端/执行器强制；八路由通过也不能代替真实违规阻断 |
| R7 | 设计边界/API owner | 角色恢复会恢复未撤销token；多worker verify/revoke竞态不承诺中断已授权在途请求，撤销完成后新鉴权请求必须拒绝 |
| R8 | 复验触发/测试owner | 源码/路由/依赖/目标/secret配置/迁移改变均使相关证据失效，先重resolve再重跑 |

停止：跨新根、业务密钥/真实账号依赖、生产攻击性测试、发布请求均停交lead；不会用离线mock绕过目标。回退Harness仅撤薄路由、保留规划与证据，不削弱已有测试。
