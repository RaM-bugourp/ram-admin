# CORE-003 旧规划桥接增量

不改旧编号或验收语义；当前任务[TASK-CORE-003](TASK-CORE-003.md)。

| 原章节/AC | 新任务/规则 | 执行/证据 |
|---|---|---|
| PLAN G1/G2与CORE C14 | S01/S08/S09；RAM-SCOPE/BUILD/DOC-001 rev1 | 当前源码清单/统一verify/原件保护，advisory |
| CORE C01/C02/C09 | S02/S03/S04安全中心；RAM-API/DATA/UI-001 rev1 | 新API+service+双session+真实HTTP/Edge，旧改密不重做 |
| CORE C08 | S05安全过滤CSV；RAM-API/UI-001 rev1 | 共享过滤/危险CSV/权限/浏览器下载 |
| CORE C15恢复not-run | 本次新授权S06仅本机隔离恢复；RAM-DATA-001 rev1/W6 | SQLite在线backup与全表内部对账，不把本地结果当生产恢复 |
| 原AC3/AC4 | S07/S08本版本真实UI+HTTP/Edge | 旧截图/HTTP不能算新版本通过 |

无新增远端/CI/生产授权；实现者完成只交lead独验，不自签。

---
# 原规划共存桥接

原规划唯一定位：[2026-11-17 PLAN](baseline/PLAN-20261117.md)（来源C:/c/Users/Rick/ram-admin-review-20261117/PLAN.md）；原owner ram-admin-build，lead验收。归档字节不改，原编号/承诺不重写。新长期规划[PLAN](PLAN.md)是新增版本的事实源，不宣称取代上轮交付结论。

| 原文/AC | 本轮任务与路由 | 规则rev/owner | 执行器/强度 | 证据与缺口 |
|---|---|---|---|---|
| PLAN AC1来源核验 | P0来源/version；docs | RAM-SCOPE-001/1 dev | Python摘要核对/advisory | baseline/source-files、release-manifest；旧完整快照不重下载 |
| PLAN AC2鉴权/配置 | TOKEN-001安全/API/数据 | RAM-API-001、RAM-DATA-001/1 dev | Django+SQLite/advisory | 新Token回归；不把旧局部review当全面安全审计 |
| PLAN AC3真实运行 | P3旧27回归+构建 | RAM-BUILD-001/1 dev | Python/Node/advisory | 保留旧QA原文，新版真实浏览器/模型not-run；不抹旧AC |
| PLAN AC4截图 | 不在本切片变更UI | RAM-UI-001/1 dev | 本轮仅typecheck/build | 旧截图属旧版；新GUI not-run，不虚报最新版截图PASS |
| REVIEW未修Token | TOKEN-001 | RAM-API-001/1 dev | 原生ORM/API测试/advisory | 首切片完整撤销与issuer状态；默认密钥fail-closed |
| REVIEW审批归属/actor=None/404 | 后续候选，非本次实现 | scope owner lead | proposed未来任务 | 保持风险，不扩大产品承诺 |

文档接线与机器格式、真实API/DB测试、GUI、外部门禁分别验收。旧计划只允许局部维护，本轮完整开发授权来自用户新请求，经lead明确新目录/预发行/切片；这不是迁移原AC。无CI或远端强制接线，产品整体未PASS，人类签署pending。回退本层仅撤薄路由，保留原规划/证据和既有产品测试；新Token兼容/安全停用及前滚见PLAN第6节。
