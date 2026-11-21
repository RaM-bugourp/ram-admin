# 插件任务路由

> scope：in-process / frontend-panel / remote-protocol 的实际所选组合。owner：采用项目的插件维护者。status：规范；执行器需项目接线。applies_when：插件任务。related：[选择](../selection.md)、[证据](../evidence.md)。

每行均继承[公共选择](../selection.md)及[验证](verify.md)，并读实际功能契约/实现/测试。条件 false 须有依据，unknown 阻断；跨形态取并集。下表能力名不是已安装命令，机器实例使用人工执行器身份，不执行任意命令。

| ID / 任务信号 | 必读领域页 | 条件追加 | 重点证据/负例 |
|---|---|---|---|
| P1 新增宿主能力 | [宿主兼容](host-compat.md) | 有资源所有权→[生命周期](lifecycle.md) | 真实宿主 API/版本、缺能力与非法调用拒绝 |
| P2 启停/重载/卸载 | [生命周期](lifecycle.md) | 有 UI→[隔离](ui-isolation.md) | 重复启停、全部资源清理、卸载后无迟到写 |
| P3 异步取消 | [生命周期](lifecycle.md)、[协议安全](security-protocol.md) | 无 | 超时/断连/卸载取消、迟到结果丢弃 |
| P4 面板布局/交互 | [UI 隔离](ui-isolation.md) | 使用宿主 UI API→[兼容](host-compat.md) | 真实宿主页、键盘/焦点/窄屏、错误状态 |
| P5 CSS/portal | [UI 隔离](ui-isolation.md)、[兼容](host-compat.md) | 无 | 邻面板/宿主对照、卸载 style/portal 残留 |
| P6 宿主升级 | [兼容](host-compat.md)、[生命周期](lifecycle.md) | 有 UI→[隔离](ui-isolation.md) | 支持矩阵真实加载/使用/卸载，不猜版本支持 |
| P7 远程协议升级 | [协议安全](security-protocol.md) | 持有长连接/请求→[生命周期](lifecycle.md) | 新旧端组合、未知方法/字段、断网重连 |
| P8 权限/文件/网络 | [协议安全](security-protocol.md) | 无 | 越界/失效凭据/撤销拒绝，无副作用及脱敏审计 |
| P9 构建/包/安装 | [构建交付](build-release.md)、[兼容](host-compat.md) | 无 | commit→产物 hash→安装实例与资源入口 |
| P10 热更新/版本切换 | [构建交付](build-release.md)、[生命周期](lifecycle.md) | 有 UI→[隔离](ui-isolation.md) | 实际更新通道、旧实例退出/新接管、失败可用性 |

不支持热更新且本任务没有引入它时，P10 可不命中；不能通过漏写任务掩盖版本切换风险。P1/P4/P7 对应不同形态；事实尚不明时先发现。

## 稳定性规则索引（revision 1）

- PLG-STAB-001：[资源所有权/取消](lifecycle.md)，适用持有资源/异步工作的插件生命周期。
- PLG-STAB-002：[真实宿主支持声明](host-compat.md)，适用兼容/加载/GUI 验收；mock 不替代宿主。
- PLG-STAB-003：[产物来源](build-release.md)与[UI 边界](ui-isolation.md)，分别适用交付和 UI 隔离。

以上是相应 scope 的硬边界；规范存在不表示外部 enforcement。项目登记 owner、执行器及证据，实际接线遵守[FORMAT](../../../spec/FORMAT.md)。
