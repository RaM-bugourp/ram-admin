# 从这里采用

本指南适用于任何工程；不绑定特定产品或 agent 宿主。交付的是通用规范/模板/离线检查契约，不宣称已安装到你的项目。先读 [总览](overview.md)，已有项目走 [共存与采用](adoption.md)。

## 先做一个获准试点

1. 只读盘点原规划、事实源、dirty 状态、owner、平台/子形态与权限。声明支持与排除范围；未知/缺能力不是排除理由。
2. 选择一个任务族或模块；批准路径、动作和验收。编辑前读 [PR 边界](pr-boundaries.md)，验证前读 [测试边界](test-boundaries.md)。
3. 从 [模板目录](../templates/README.md) 复制薄入口和需要的卡；显式替换占位。入口链接到你现有规范，不把本包根入口冒充项目已部署入口。
4. 按 [路由协议](routing.md) 建必读/条件集合，按 [owner 协议](ownership.md) 明确责任与冲突出口；从 [平台导航](platforms/README.md) 按实际适用范围加载，不默认全读或任选一种。
5. 用 [规划桥接](../templates/planning-bridge.md) 指向原规划；原路径/编号/验收不动。按 [任务生命周期](task-lifecycle.md) 试运行，按 [证据协议](evidence.md) 分层报告。

## 机器输入与演示

技术字段/匹配/退出语义仅以 [FORMAT](../spec/FORMAT.md) 为准。模板卡都是人工 Markdown，不是 lint 输入；演示根是 `examples/demo`，不可用演示身份/证据替代真实项目事实。平台任务的独立机器输入、命令与合成数据边界见 [平台 profiles](../profiles/README.md)。

在本包根目录、Python 3.10+ 环境运行：

```sh
python tools/harness.py lint --root examples/demo --manifest harness.json
python tools/harness.py resolve --root examples/demo --manifest harness.json --task tasks/hybrid.json
python tools/harness.py evidence --root examples/demo --manifest harness.json --task tasks/hybrid.json --records evidence/records.json --now 2026-11-14T10:00:00Z
```

最后一条固定时间只为复现演示；项目实际校验用当前带时区时间，不回拨时钟复活旧证据。输出 JSON、退出码 0 有效/完成、1 输入/schema/引用无效、2 未解决/blocked/fail/not-run（参数误用亦 2）、3 I/O/操作错误。N/A 有 scope 依据才可完成；成功不执行任何清单命令，不发现真实 Git/OS，不授权，也不证明产品 pass 或 CI 已强制。本包演示预期 lint/resolve 为 pass（exit 0），evidence 保留三项 not-run（exit 2）；非全绿是刻意保留的未执行边界，不应改成假 pass。

## 单独验收接线与真实效果

至少八类真实/代表性任务，含跨域并集、未知条件、冲突、重路由和阻塞出口；除了链接存在，还核对到达的正文是否足够执行。发现预算是建议，不删安全依赖。

执行器、CI required checks、远端保护与真实产品目标各自需要授权、接线和证据。独立验证违规确实被拒，不能以 YAML/脚本存在代替。环境缺失走 [能力申请](capabilities.md)，报告 blocked；不适用要 scope 证明。版本升级/退出按 [适配](adoption.md)，持续维护按 [变更控制](maintenance.md)。
