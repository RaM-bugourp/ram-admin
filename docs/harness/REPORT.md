# 交付报告：0.2.0-harness.1

2026-11-18（Asia/Shanghai）。状态：**本地预发行，Token切片本地验证通过；整体产品not-run，独立验收待lead安排，不是生产完成或人类安全签署。** 最新不可覆盖run由 [latest.json](evidence/latest.json) 指向；每run summary/commands/source-inventory/records/evidence-evaluation均保留。

## 1. 新版本/边界
- 唯一新源码根 `C:/c/Users/Rick/ram-admin-0.2.0-harness.1`；入口 [AGENTS](../../AGENTS.md)、[开发命令](../../DEVELOPMENT.md)、[完整规划](PLAN.md)、[版本manifest](../../release-manifest.json)。独立Git根、dev/0.2.0-harness.1分支，无remote、未add/commit/push；父Git未操作。
- 来源净化ZIP SHA256 `69f462c7eb086f0e62e49def92299f76a90c42fa4eea1384bfccaf42cf936141`，固定上游HEAD `3a4fd98bb98030c67261a4973048c6ba133a828e`。每次verify核原clean-source全部146文件SHA及原ZIP、冻结1.0.0载荷129文件SHA；原runtime/网站/上游快照/DSH安装无写入。
- 未复制原账号、SQLite、env、密钥；测试账户/密钥仅隔离临时库/进程。新根现有node_modules/dist/cache是本轮本地npm ci/build生成且被ignore，不是从旧runtime拷贝或源码发布载荷。无远端/生产授权。
- 版本沿frontend package0.1.0采用fork独立0.2.0-harness.1；原README另声称v1.0.2，已明确保留为上游历史，不伪称本号大于该正式序列。VERSION、package/lock两处项目版本与release-manifest一致。

## 2. 实际改动与新增
原146文件删除0，修改11：`.gitignore`本根缓存；README当前分支/规范入口；backend AI models/permissions/serializers/agent_views与base secret配置；frontend package/lock版本和typecheck、types/ai、现有Token UI兼容说明。精确列表/字节摘要见每run changes.json、source-inventory.json。
新增：AgentCredential0002迁移、AI tests.py、隔离settings.test；VERSION/AGENTS/DEVELOPMENT；Harness PLAN/BRIDGE/OWNERS/ROUTING/TASK、harness.json与完整原样vendor1.0.0（演示明确隔离）；非敏感旧证据baseline；tools含verify、旧BOSS27移植、迁移/新进程探针、路由矩阵、旧漏洞复现。原9文件修复继续保留，不扩大审批/actor等产品模块。

## 3. Token产品切片
- 新v2随机UUID+HMAC，只持久化完整Token SHA256、issuer/agent/期限/撤销时间，不存明文/secret；同秒签发互异，不复活已撤销token。专用secret显式至少32字符；缺失/过短签发503、verify拒绝，不回落Django/固定密钥。
- 逐请求从DB查issuer当前active/非删、superuser或非删root角色+非删关联；停用/软删/硬删/失root/软删Role立即拒绝。恢复权限可能恢复未撤销未过期凭证，显式撤销不可恢复。
- root专属revoke `{token_id:UUID}`，任意有效root同管理域可撤，单句柄幂等，未知/重复同200；无Token列表/明文再取。DB错误/缺表拒绝，不回退HMAC-only。
- 保持root session独立身份/Session CSRF。Agent仅审批submit权限、身份取token元数据覆盖body，不变为root、不能自己review/issue/revoke/RBAC/chat；submit只pending，无用户写副作用。
- 原签发UI消费token/agent_id/expires_in_hours不变，附token_id类型及安全说明；不新增撤销UI，本轮新版UI真实浏览器未验。旧四段token显式全部失效，迁移后有效root重发。

## 4. 精确验证入口与结果
在新根PowerShell运行：
```powershell
python tools/verify.py --python 'C:/c/Users/Rick/ram-admin-review-20261117/venv/Scripts/python.exe'
```
每次独立时间戳run，读取旧解释器仅复用依赖，不读旧DB或secret；各命令绝对cwd、开始时区/耗时/退出码在commands.json。脚本exit0只代表声明本地检查；Harness evidence刻意exit2/not-run（browser-e2e）。独立验收可用同命令再跑，不信实施者自报；需保持产品/测试/规范文件冻结，验收证据写新run。

| 实际检查 | 实际命令摘要（完整命令见commands.json） | 结果 |
|---|---|---|
| 配置/模型 | `backend/manage.py check --settings=config.settings.test`；`makemigrations --check --dry-run` | exit0；无问题/无漂移 |
| Token定向 | `backend/manage.py test apps.ai --settings=config.settings.test -v 2` | exit0，25测试（含正反/真实session+CSRF/已签但未登记/摘要错/issuer变更无副作用） |
| 原生全量discovery | cwd backend，`manage.py test --settings=config.settings.test -v 2` | exit0，25测试；不与定向相加冒称50唯一测试 |
| 历史BOSS | `tools/verify_boss.py --output <run>/boss.json` | exit0，27断言；原404观察不当已修 |
| SQLite迁移 | `tools/verify_migrations.py --output <run>/migration.json` | exit0，14断言；0001旧审批/日志保留、重复、逆向/前滚、新进程完整verify与撤销可见 |
| 前端 | cwd frontend，`npm ci --ignore-scripts`、`npm run typecheck`、`npm run build` | 均exit0；大chunk warning保留 |
| Harness格式/路由 | 冻结tools/harness.py lint/resolve；`tools/harness_checks.py` | lint/resolve exit0；14探针含8任务族+跨域/unknown/未授权/无路由/冲突/缺证据预期2 |
| 机器证据 | 冻结tools/harness.py evidence 对本run task/records/current now | exit2/not-run；缺新版浏览器E2E，非输入错误 |
| 原件/冻结模板/版本/敏感文件 | verify内建SHA与文件清单 | 146源+ZIP/129冻结载荷、版本一致；无秘密文件/DB进入源码清单 |

目标：Windows x64，Python3.13.15/Django5.2.19/DRF3.18.3/SQLite3.53.1；Node24.19.0/npm11.17.0。后端requirements原为宽范围，实际freeze入run，不谎称任意机器可复现同解析。APIClient+ORM/真实SQLite不是监听HTTP/浏览器E2E，不用模板模拟证据冒充目标。

## 5. 失败、纠正与历史保留
1. 初始manifest lint exit1：同required页重复，去重后exit0；未改冻结validator。
2. 首轮Token23测试1失败：误测`/api/ai/chat/`得404；读真实router+action后改正确`/api/ai/chat/chat/`，仍要求403，非放宽断言。原始工具输出可由本会话查，后续25全过。
3. 完整run `20261118T233453+0800-445abb`：前端build exit1，系统Temp esbuild临时文件删除Access denied；失败日志保留；runner打印符号触发GBK UnicodeEncodeError也保留。仅新进程TEMP/TMP改为本根独占并使用UTF8，未改系统Temp权限/全局环境/安装。后续build exit0，退出尽力清理的cleanup.json记录removed。未请求升级、未运行ACL修复。
4. 完整run `20261118T233831+0800-d9b135`：产品测试/前端build均0，机器证据schema exit1：execution.cwd用绝对Windows路径；按冻结契约改root-relative POSIX（根为`.`），未伪改PASS。后续evidence exit2/not-run正确。
5. 独审发现规划错误已明确纠正：现有Token UI真实存在；清空secret仅新fail-closed代码可停用，旧版反而回弱密钥；逆迁移会丢新凭证账本，不能宣称生产安全回滚保留。后续补正确签名未登记/摘要错、真实登录后失权issue/revoke、新进程完整verify，不只SQL状态读取。
6. 只读侦察曾尝试不存在models/user.py（实际models.py）、clean-source git rev-parse非repo exit1；均调查确认后改正，无父Git写入。裸系统Python3.11缺Django，实际改用既有隔离3.13解释器。

## 6. 明确未完成/风险/下一阶段
- 新版真实HTTP+浏览器GUI/人工视觉/真人手机、真实Provider、生产部署/恢复/中断迁移故障注入、严格并发revoke压力与取消在途请求、远端CI/required checks/保护/签名/许可审计NOT-RUN。顺序幂等和跨进程存储/完整鉴权通过不冒充并发压力。eslint缺依赖未跑，不报lint成功。
- 0002逆向会删除凭证/撤销登记，新版再前滚空表仍拒旧token但必须重发；**生产不得执行该逆迁移或直接回退旧二进制**。保持新代码时才可清空专用secret停用；旧版需独立关闭Token入口或下线隔离，另行评审。
- 审批审计issuer归属、actor=None内部路径、普通审计API404、Django开发配置/默认开发secret仍未修，不称全产品安全。root-only helper此处强化不等于全RBAC服务已统一默认拒绝。
- 后续由lead协调用户选择：优先审批issuer归属独立任务卡；再actor内部边界、审计模块真实需求、部署/后端锁策略；目标/授权/AC先补再实现。
- 本轮后台job数0，job ids=[]；未启需保留服务器、未杀旧runtime服务。所有测试子进程同步完成；临时数据库自动关闭清理，新进程probe不打印token/secret。
- 最终独立验收由lead委派ram-token-review执行；本文只报实施者实跑，不把lead协调/抽查写成lead实跑，也不伪造人类签署。

## 7. 待主会话追加的事实记忆（未编辑全局MEMORY）
2026-11-18：ram-admin独立新根C:/c/Users/Rick/ram-admin-0.2.0-harness.1，本地fork预发行（package0.1.0线；README上游自称1.0.2另保留），固定3a4fd98+旧九文件补丁，原146SHA+净化ZIP保护。冻结Harness1.0.0原样129载荷，AGENTS/PLAN/BRIDGE/owner/路由/任务与机器封套advisory齐；非运行时/远端强制。Token v2随机+摘要allowlist/issuer当前状态/专用secret fail-closed/UUID单token幂等revoke，旧token失效需重发；逆迁移丢凭证不可生产使用，禁回旧二进制。实施者实际Token25/discovery25同集合+BOSS27+迁移14+路由14、npm ci/typecheck/build通过；浏览器E2E/真实Provider/生产/严格并发等未跑，evidence刻意2/not-run。完整结果查最新run，独立验收另由主会话收集，不在此先宣称。原runtime/网站/父Git/全局记忆/远端未动；0后台job。审批归属/actor=None/普通审计404未修。
