# 新平台与能力 overlay

> scope：开放类别扩展与复用。owner：采用项目的平台/领域维护者。status：规范；示例不是既有集成。applies_when：现有形态不能完整描述目标时。related：[选择](selection.md)、[证据](evidence.md)、[机器 profile 说明](../../profiles/README.md)。

## 公共骨架不等于平台闭集

保留公共的选择、scope、授权、冲突、五态和证据协议；能力 overlay 负责实际契约/实现边界/负例/目标矩阵。类别标签是发现入口，不提供默认权限，也不自动启用整套能力。

| 新形态 | 优先复用的能力页 | 只补形态特有内容 |
|---|---|---|
| CLI | [协议/权限](plugin/security-protocol.md)、[构建交付](plugin/build-release.md) | 参数/stdin/stdout/退出码、TTY/非TTY、shell quoting、信号/管道、真实安装路径 |
| 库/SDK | [兼容](plugin/host-compat.md)、[生命周期](plugin/lifecycle.md) | ABI/API/序列化兼容、依赖消费者矩阵、线程安全与资源所有权 |
| 无 UI 服务 | [API/配置](web/api-config.md)、按需[数据](web/data.md)、[运维发布](web/operations.md) | 实际进程/编排、探针/优雅退出、流量与任务幂等边界 |
| 桌面 | [APP 交付](app/build-signing.md)、[本地升级](app/local-data.md)、按需[UI 隔离](plugin/ui-isolation.md) | 安装器/权限、OS 权限、自动更新、多进程/窗口、文件关联与卸载残留 |

复用页面必须声明具体 scope 映射，例如库的“宿主”指真实消费者运行时；不适用的 GUI/商店规则不得强塞，无映射依据则先发现。跨形态组合仍取并集。

## 扩展落地步骤

1. 登记目标、负责人/替补、支持矩阵和未知事实；链接现有产品契约及原规划，不重写产品目标。
2. 写一个短导航，描述触发信号与 required/conditional，复用领域页；仅独有风险才增正文。每页标 scope、owner、status、applies_when、related。
3. 给新增边界分配稳定 ID/revision，明确动作/路径/任务/平台/生命周期及冲突语义。按核心 FORMAT 写规则与路由；平台值是项目定义字符串，不增加封闭 schema 枚举。
4. 验证正例、拒绝/取消/中断负例、unknown 阻断、false 有依据和跨平台并集；维护可执行命令、真实 target 与失效条件。
5. 运行核心 lint/resolve，检查所有链接和孤立规则；离线 profile 通过只证明可消费。执行器、CI、宿主或发布接入另需授权及真实验收。

不要为框架/OS 名字复制规范；仅当生命周期、能力或交付约束真正不同才拆页。owner 联系与能力尚未映射时可保持 proposed，但高风险动作仍 blocked。
