# 本架构包的协作入口

本仓库是通用 Harness 规范、模板与离线验证工具的源码包，不是用户项目已部署治理的声明。产品环境、CI、远端保护和权限须分别接线验收。

- 采用/使用从 [START-HERE](docs/START-HERE.md) 进入；结构与责任域见 [总览](docs/overview.md)。
- 本包编辑前读 [PR边界](docs/pr-boundaries.md)，测试/验收前读 [测试边界](docs/test-boundaries.md)。保留既有dirty，不越范围，不擅自force push，不削弱测试。
- 任务按 [路由协议](docs/routing.md) 取多页并集，按 [生命周期](docs/task-lifecycle.md) 重路由；冲突交 [owner协议](docs/ownership.md)，不是根文件或最近文件自动赢。
- 机器字段、匹配、状态与CLI只以 [FORMAT](spec/FORMAT.md) 为技术契约；人类 [模板](templates/README.md) 与运行样例分离，模板占位不是证据。
- 缺环境/权限立即走 [能力申请](docs/capabilities.md)，unknown/blocked非N/A，不绕拒绝。通过声明按 [证据协议](docs/evidence.md) 限定范围，schema有效不等于产品pass。
- 草稿仅保留历史设计；本包正式使用指南与技术契约不自动改写任何原产品规划。维护/升级/退出见 [变更控制](docs/maintenance.md) 与 [适配](docs/adoption.md)。
