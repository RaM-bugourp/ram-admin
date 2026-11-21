# 通用 Harness 工程治理架构

可复制采用的**平台中立架构成品**：薄入口发现、多任务上下文路由、带 scope 的规则、owner／执行器／证据闭环、JSON 数据契约与只读本地校验器。不是某个产品的部署包，也不表示所有平台、真实产品、CI 或远端保护已验证。

## 选择你的路径

| 目的 | 直接入口 |
|---|---|
| 首次采用，在获准模块建立最小试点 | [从这里开始](docs/START-HERE.md) |
| 接入旧工程，保留原规划与现有事实源 | [共存、接线与退出](docs/adoption.md) |
| 扩展平台或混合插件／Web／APP | [平台扩展流程](docs/platforms/extensions.md)；[适用性选择](docs/platforms/selection.md) |
| 理解路由与 scope／冲突处理 | [路由协议](docs/routing.md)；[责任与裁决](docs/ownership.md) |
| 编写机器清单与检查证据 | [唯一技术格式](spec/FORMAT.md)；[证据语义](docs/evidence.md) |

入口只分流，不是全量规则最高文件。按任务、路径、动作、领域、平台与生命周期匹配多条路由，取必读集合与适用约束并集；未知条件或冲突停止受影响动作，不静默择宽。已有规划继续拥有其目标和验收语义，模板不重写它。

## Quickstart（先运行合成演示）

依赖 **Python 3.10+ 标准库**，无第三方包安装步骤；无需 Node、数据库或模型账号。`python` 必须指向受支持版本（Windows 可先用 `py -3 --version` 确认，必要时以 `py -3` 代替）。从仓库根目录运行：

```sh
python --version
python tools/harness.py --help
python tools/harness.py lint --root examples/demo --manifest harness.json
python tools/harness.py resolve --root examples/demo --manifest harness.json --task tasks/hybrid.json
python tools/harness.py evidence --root examples/demo --manifest harness.json --task tasks/hybrid.json --records evidence/records.json --now 2026-11-14T10:00:00Z
```

`lint` 预期 exit 0，仅表示结构／引用有效；`resolve` 预期 exit 0，得到插件、Web、APP 三路并集；演示 `evidence` 预期 **exit 2／not-run**，因为示例没有冒充真实目标执行。固定 `--now` 仅为复现示例，真实项目使用当前时间，不能回拨时间复活过期证据。全部输出为 JSON（help／参数错误除外）；exit 1 为输入／schema／引用错误，2 为未解决／fail／blocked／not-run（参数误用也为 2），3 为 I/O／操作错误。有 scope 依据的 not-applicable 可 exit 0，**exit 0 不等于产品 PASS**。

校验器仅检查声明支持的受限 schema 方言，不是完整 JSON Schema 引擎；未知 schema 关键字拒绝。清单路径用 root-relative POSIX 写法；工具不会运行证据里的 command，不读取真实 Git／OS 配置、不授权操作、不认证证据签名或真实性，也不会安装 CI／分支保护。

## 交付内容

- [规范总览](docs/overview.md)、[任务生命周期](docs/task-lifecycle.md)、[PR 边界](docs/pr-boundaries.md)与[测试边界](docs/test-boundaries.md)：稳定性与授权分域约束。
- [模板卡](templates/README.md)：人工入口、任务、规则、证据、决策和规划桥接；Markdown 卡不是 JSON CLI 输入。
- [平台目录](docs/platforms/README.md)与[profile 索引](profiles/README.md)：按真实子形态组合，不默认全选或互相替代。
- [格式契约](spec/FORMAT.md)、`schemas/`、`tools/`、`tests/`、`examples/demo/`：机器格式、只读工具与明确合成示例。
- [验收契约](ACCEPTANCE.md)、[独立验收报告](qa/REPORT.md)、[变更记录](CHANGELOG.md)：完成标准、实跑范围、限制和结果。

## 本地验收与适用边界

```sh
python -m unittest discover -s tests -v
python qa/acceptance.py
python qa/check_links.py
```

五态固定为 `pass`、`fail`、`blocked`、`not-run`、`not-applicable`；`proposed`／`advisory`／`enforced` 是独立的实施强度轴。自述执行记录即使离线一致且为 pass，也不能证明发生了真实执行，更不能把 proposed 自动升级为 enforced。Schema 结构、semantic 检查、产品真实执行和远端 CI 强制分别验收，详见 [四层判据](ACCEPTANCE.md)。

当前实测平台及每条命令结果以 [独立报告](qa/REPORT.md) 为准。Python 3.10+ 是兼容性要求，不表示各版本与所有 OS 已矩阵实测；原生 symlink／junction 等受 OS 权限影响的分支须按实际报告，不外推。平台资料覆盖插件、全栈 Web、桌面与移动 APP 的接线方法，不提供通用运行时执行器、安装器、签名／设备环境、CI 配置或所有产品的验证证明。遇缺环境／权限先走 [能力申请](docs/capabilities.md)。

## 权威与历史

机器契约以 [FORMAT](spec/FORMAT.md) 为准；各领域细节以其 scope 页面为准。`drafts/` 中的 [核心设计](drafts/00-core.md)、[平台讨论](drafts/10-platforms.md)和[红队记录](drafts/90-redteam.md)仅保留历史推导，**不是当前字段／命令／完成状态的权威**。冲突按 [维护协议](docs/maintenance.md) 登记，不能据历史稿扩大授权。

As of 2026-11-14 · 本仓库成品入口；最终发布状态见独立验收报告。
