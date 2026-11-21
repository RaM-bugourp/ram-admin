# 当前0.3.0-dev.1入口（2026-11-20）

本根沿fork版本线的本地预发行，非上游发布。唯一writer ram-core-next，lead只协调/只读验收。先读[TASK-CORE-003](docs/harness/TASK-CORE-003.md)，其中现状/授权/目标非目标/阶段S01–S09/路由/验证为当前增量事实；下方.2入口保留为历史，只读保护.2/.1/review/网站/订单/父Git/DSH/全局MEMORY。不提交远端/部署/持续服务。完整验证见DEVELOPMENT。

---
# Ram-AdminX 开发入口

本根是 **0.2.0-harness.2 本地预发行开发根**，不是旧 runtime，不是 DSH 插件。先读 [规划/事实源](docs/harness/PLAN.md)、[有限完整性矩阵](docs/harness/COMPLETENESS.md)、[路由](docs/harness/ROUTING.md)、[owner](docs/harness/OWNERS.md)，再读命中正文、旧规划[桥接](docs/harness/BRIDGE.md)和当前[CORE-002任务卡](docs/harness/TASK-CORE-002.md)。TOKEN-001及原REPORT是历史记录，不代表本版本验收。唯一写入者ram-admin-core；lead协调/只读验收。保护.1和review旧根，不改父Git/网站/DSH安装/全局MEMORY。

Harness固定 [1.0.0 START-HERE](docs/harness/vendor/1.0.0/docs/START-HERE.md)，采用是 advisory，不是运行时或CI强制。新任务按路由并集、unknown/冲突暂停、扩大范围重路由。人工卡与机器harness.json分开，格式通过不等于产品通过。

- 唯一写入范围本根，保留已有差异；不得改旧工作根/runtime/ZIP、网站、父Git、DSH安装或全局记忆。发布/远端/CI另需授权。不得复制秘密/账号/SQLite。
- 改前读 [PR边界](docs/harness/vendor/1.0.0/docs/pr-boundaries.md)；测前读 [测试边界](docs/harness/vendor/1.0.0/docs/test-boundaries.md)。先复现再修，正反回归不删弱。
- 验证入口 `python tools/verify.py --python <含requirements的Python>`；见 [开发运行说明](DEVELOPMENT.md)。输出目录为docs/harness/evidence，每次运行保留独立时间戳，不覆盖历史失败。
- 交接列命令、退出码、测试数、目标、未跑与失效条件；禁止把Django test client/静态检查称浏览器E2E。人类签署只能由人提供，当前pending。
