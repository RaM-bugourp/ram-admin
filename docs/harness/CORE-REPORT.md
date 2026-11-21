# CORE-002 / 0.2.0-harness.2 本地交接

2026-11-19 Asia/Shanghai；实施ram-admin-core，lead协调与只读验收，ram-core-review独立只读安全审查。**这是本地未发布开发结果，不是生产PASS；最终接收等待lead安排独立验收。**

## 交付与实际结果定位
- 新根C:/c/Users/Rick/ram-admin-0.2.0-harness.2；完整可复跑命令[DEVELOPMENT](../../DEVELOPMENT.md)，范围与逐C证据[COMPLETENESS](COMPLETENESS.md)、任务[TASK-CORE-002](TASK-CORE-002.md)、既有目标桥接[PLAN](PLAN.md)/[BRIDGE](BRIDGE.md)。
- 本轮全部实际命令/退出码/计数在独立evidence run，当前完整run由[evidence/latest.json](evidence/latest.json)定位。以该run的summary、commands、source-inventory、source-protection、changes、core-boundaries、migration、boss、routing、frontend-artifacts和live-binding核对，不以本文静态文字或旧REPORT绿色代替。
- 使用完整`--browser-python`入口后，summary.core_local_status及browser-e2e命令/嵌套live-summary/browser.json必须全部pass，cleanup/backend_stopped/browser_closed/isolated_data_removed必须true才可将该run作为本地验收候选；若任一失败则当前候选不完成。人工视觉/生产/外部provider等即使本地全过仍未验。
- 旧REPORT/TOKEN-001/历史latest副本属于.1；本轮中间31、51和第一轮12HTTP+28browser只是阶段证据，后续源码变化使其不再覆盖当前版本。最终源digest从完整run读取；冻结后任何源/环境/产物变化触发重跑，不手改digest复活证据。

## 功能与安全闭环
- 当前有效actor+live role/link、动作闭集默认拒绝；None内部写一律403。root/superuser、BOSS、普通自定义角色范围服务端执行，菜单/路由消费permissions，刷新bootstrap。
- BOSS/自定义writer禁止接管active/inactive管理员及超actor权限的custom目标：reset/update/role stripping/reactivate/delete共用_target；role editor也不能先剥高权限role。合法等低权限与root操作保持。
- 用户角色实际CRUD、唯一字段墓碑409、非法/重复/软删role400、删除用户解绑、唯一角色占用/切换检查、已分配role删除409、最后有效root保护。SQLite首写预留锁+两个独立连接竞争测试，不声称其他DB/容量/跨服务分布式保证。
- 真实通用只读审计API /api/audit/logs/，最小audit.read、固定字段/分页/筛选；成功业务和日志同事务，失败/拒绝在rollback外安全事件记录。审计存储故障只固定错误诊断，不把缺失记录冒充已存。
- login显式CSRF（含合法token+恶意Origin），会话查询当前有效用户，设置修改本人密码，当前session更新/其他旧session失效。API403不再全局误跳转，UI有错误重试/空态/请求世代/提交保护/键盘搜索和末页校正。
- 工作台真实ORM计数（0不变省略号），无假活动；设置不是无效按钮。AI_UI_ENABLED默认false，核心无provider请求，安全实现保留，不删除旧审批/凭证、不造隐式后门。
- Token v2原实现/25测试不改，专用secret/摘要allowlist/当前issuer/撤销和旧Token失效边界保持。新审批真issuer，旧submitted_by NULL=unknown；提交密码Django单向hash不落明文、不信外部digest，受控review消费不双hash，终态清摘要；查询脱敏，执行savepoint+条件claim。0003处理历史敏感params/prompt/comment，单向不可恢复明文，不宣称历史从未泄露。
- base/dev无共享默认Django secret；production.py真配置缺/弱secret/hosts/绝对DB拒启，HTTPS安全cookie/HSTS，测试没有关闭生产检查或造默认密码。

## 回归保留与失败透明
- 原Token25测试逐SHA未改；原14迁移与14路由保留。原BOSS前26权限断言保持；第27原为审计404观察，lead确认C08后升级root200固定字段+ordinary403，共28；原脚本baseline/verify_boss-harness.1.py SHA256 5dace21aa0982af0bb7309af29c566d6c5e21845a2a82cc7abc9dbbc95cb9509。
- 失败全部保留：PowerShell原生stderr采集中断/UTF16日志；新auth方法settings与DRF属性冲突、测试helper client冲突；原404→200观察失败并引发旧脚本异常路径SQLite清理WinError32；浏览器Arco modal/空态/alert/toast/popconfirm定位误差；真实键盘Enter搜索缺事件（已修产品而非改测click）。每次修后新run，不覆盖失败。
- 独审发现inactive管理员与高权限custom目标接管链，实施者修公共根因并增加API/service负例，不以‘disabled不能登录’掩盖；复验以最终fresh discovery日志为准。

## 来源、机器与禁止范围
- .1源/全部历史证据546项复制SHA清单baseline/harness.1-protection.json；统一verify复核原.1所有546项、原clean146/ZIP、vendor129，且原Token测试字节一致。原已验digest 8f29f49f1ea6c39e72291a874fd5b7a82036cb0372276a88fe02994ae2e94fe1保留，不伪称本轮新digest。
- 无旧node_modules/dist/venv/DB/env/账号/secret复制；本根npm ci/build生成依赖/产物且ignored。独立Git dev/0.2.0-harness.2无remote/commit/push；父Git/网站/DSH/全局MEMORY不修改。
- 机器实际版本以run toolchain/node/npm/python-freeze及browser.json为准；当前运行Python3.13+Django5.2/DRF/SQLite，browser Python3.11+Playwright+Edge。旧venv只复用依赖，无旧DB/env读取；每run root-local缓存/TEMP与随机loopback端口，不碰旧8000/5173。
- 所有本轮服务/Edge必须finally结束，真实HTTP与browser隔离DB在finally删除；执行结束核job_list及清理输出，不交付常驻服务/测试账号文件。

## 未验、风险与独审下一步
- 不造ERP/多租户/财务/动态菜单系统。闭集权限+既有导航是有界实现，不声称任意插件/业务权限引擎。
- 真实外部AI/人工视觉/真人手机/辅助技术、生产部署与备份恢复/中断迁移/容量/其他DB、Token严格并发压力和在途取消、远端CI保护/签名、依赖许可/漏洞总审未验。eslint原脚本缺依赖未跑。
- 生产升级优先前滚；0002逆迁移删除凭证账本，禁止直接回旧二进制/旧鉴权；0003清理不可恢复明文，生产动作需独立授权/备份/恢复方案。
- lead独审可直接执行DEVELOPMENT完整命令，核最终source digest前后不变、C01–C14每项证据、C15明确deferred和jobs全部结束；不信实施者摘要代替实跑，不以Harness evidence pass代替生产批准。
