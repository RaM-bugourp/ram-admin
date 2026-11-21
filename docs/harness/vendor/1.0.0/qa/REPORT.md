# 独立集成验收报告

> 2026-11-14；状态：通用源码包离线验收通过；全部已发现缺陷修复闭环。范围仅本通用架构包；禁止外推到外部产品真实运行／远端 CI 强制。

## 已实跑快照

工作目录为本仓库根；Python 3.11.9 / MSC v.1938 64-bit AMD64 / Windows。兼容性要求 Python 3.10+，不是各版本／OS 均已实测。脚本只依赖标准库，没有安装第三方依赖。

| 实际命令 | 结果 | 含义 |
|---|---|---|
| `python qa/acceptance.py`（18:13 首轮） | exit 0；60 cases / 60 passed / 0 failed | 独立临时合成 manifest/task/evidence 的结构与语义断言；含三个实际 CLI 子进程 |
| `python qa/check_links.py`（18:14 过渡快照） | exit 1；40 页／176 目标／14 缺页 | 并行文档尚未落盘，需最终收敛复查，不视为已通过 |
| 深层未知 schema 关键字探针（初始） | exit 0，unexpected acceptance | 发现 optional 未出现属性的子 schema 未检查未知关键字；已反馈修复 |
| `python qa/acceptance.py`（routing_digest 升级过渡） | exit 1；62 cases／47 passed／15 failed | fixture 尚缺新必填 routing_digest；同步契约后保留原断言并新增失效用例 |
| `python qa/acceptance.py`（18:19 稳定核心） | exit 0；66 cases／66 passed／0 failed | 含深层未知 keyword 两条回归、paths／facts／approved_paths／source 页内容变化失效 |
| `python -m unittest discover -s tests -v`（18:19） | exit 0；Ran 78 tests，OK (skipped=1) | 77 项实际通过；原生 Windows symlink 权限不足跳过 1 项，不伪记全覆盖 |
| `python qa/integration.py`（18:19 收集） | exit 0；11 条命令／42 JSON instances／0 failed | README／START-HERE／profile 命令按预期 0／2 退出，所有 shipped JSON 结构检查 |
| `python qa/check_links.py`（18:18） | exit 0；62 页／320 目标／0 errors／0 exclusions | 当时所有可见 Markdown 内部目标及 anchors；安全报告落盘后再刷新 |

逐例结果保存在 [机器报告](results.json)，代表最近一次运行；[验收脚本](acceptance.py)自己构造 fixture，不依赖实现者的 manifest 示例。fixture 在系统临时目录自动移除，不是产品证据。测试命令里的 shell 字符串只是数据，独立断言未生成 sentinel。

## 独立发现与修复待验

1. 深层 schema keyword fail-closed：`validate({}, {type:object, properties:{absent:{type:string, unknownKeyword:true}}})` 初始接受，与受限 schema 方言声明不符。技术 owner 已修复；缺失 optional 与空数组 items 两条独立回归现均通过。
2. task／routing 完整绑定已集成；fixture 依据当前契约生成 routing_digest，输入变化后不重写旧证据 digest，新增路径／facts／授权路径／source 页内容变化均正确失效。
3. 原生 Windows symlink／junction 不因纯代码检查或 mock 就算真实覆盖；当前平台权限限制须保留未运行／skip 事实。
4. 独立 [安全审查](SECURITY-REVIEW.md) 发现并推动修复 3 项 P2：task-or-path OR 二次覆盖误阻断、literal 方括号路径误拒、JSON 转义孤立 surrogate 导致未捕获编码异常。安全 owner 已独立完成 18 项定向复测全部通过；本 QA 另新增 8 项独立正反回归，包含 platform/domain/effect 的 AND 不放宽与正常中文 emoji 不误拒。初次新增 Unicode 负测误期望 status=fail，实输出契约规定 invalid；修正 QA 期望后 74/74 通过，不将该夹具误差算产品缺陷。

## 必须分开的结论

- Schema 结构：只保证项目声明支持的关键字；不是完整 JSON Schema。
- Semantic：离线一致性、引用、适用性、失效与路由断言；不能认证输入是否诚实。
- 产品真实执行：本包未对外部产品／真实宿主／服务／设备采集验收证据；NOT_RUN，不适用字段不能掩盖缺能力。
- 远端 CI 强制：未安装、修改或实测外部 CI／保护配置；NOT_RUN。

`proposed` 与 `pass` 可以作为两轴自述数据同时出现，但不等于真实执行证明或已强制。`performed=true`、`simulated=false` 仍可被伪造，离线工具无法认证真实性。内部自述记录满足契约仅证明一致性。

## 最终结论

最终全包链接复核：65 页／338 个内部目标，0 errors／0 exclusions；`python qa/package.py` 发布清单预览 exit 0，未写 release。

最终稳定快照：实现回归 84 tests / OK (skipped=1)，独立矩阵 74/74，文档实际命令 11/11（含平台 124 assertions / 31 routes / 17 conditional / hybrid 19 页），示例与 profile JSON 42/42；安全 18/18 定向复测已闭环。完整命令输出见 [集成机器报告](integration-results.json)，原生测试输出见 [实现回归输出](unit-output.txt)。建议作为通用离线架构源码包发布，Python 3.10+ 仅为要求，本机只实测 3.11.9。主会话明确批准后按 [发布清单](RELEASE.md) 构建与复核；不声明产品真实执行或远端 CI 强制。
