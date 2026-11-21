# APP 任务路由

> scope：实际 native / cross-platform / mini-program；桌面按能力复用。owner：采用项目的 APP 维护者。status：规范；未接渠道或设备。applies_when：应用任务。related：[选择](../selection.md)、[扩展](../extensions.md)、[证据](../evidence.md)。

每行继承公共选择、任务/稳定性/原规划和真实功能契约/实现/测试，并读[真机验证](device-verify.md)。登记实际 OS/架构、容器/基础库、设备分层和渠道，未选端不自动承诺上线。条件 unknown 必须发现/blocked。

| ID / 任务信号 | 必读领域页 | 条件追加 | 关键证据/负例 |
|---|---|---|---|
| A1 构建/签名/渠道包 | [构建签名](build-signing.md)、[发布](release-rollout.md) | 无 | hash、签名/包身份、真机或真实容器安装 |
| A2 SDK 接入/升级 | [SDK/隐私](sdk-privacy.md)、[构建](build-signing.md) | 无 | 传递依赖/初始化、真实网络/权限行为 |
| A3 权限/隐私流程 | [SDK/隐私](sdk-privacy.md)、[交互/生命周期](interaction.md) | 无 | 拒绝/撤回/受限、同意前后采集及降级 |
| A4 本地数据库升级 | [本地数据](local-data.md)、[发布](release-rollout.md) | 无 | 旧安装数据→新版本、空间不足/中断与对账 |
| A5 后端契约 | [后端兼容](backend-contract.md)、[发布](release-rollout.md) | 无 | 在用旧/新客户端×服务组合、兼容截止 |
| A6 离线/重试/同步 | [后端兼容](backend-contract.md) | 有持久化→[本地数据](local-data.md) | 真机断网/重连、重复/冲突、前后台中断 |
| A7 UI/原生桥接 | [交互/生命周期](interaction.md) | 有桥/SDK/权限→[隐私](sdk-privacy.md) | 真机交互、桥参数/权限负例、系统导航/可访问性 |
| A8 后台/进程终止恢复 | [交互/生命周期](interaction.md) | 有本地数据→[本地数据](local-data.md)；联网→[后端](backend-contract.md) | 系统/容器挂起终止重进、资源释放/未完成恢复 |
| A9 灰度/紧急缺陷 | [发布](release-rollout.md) | 联网→[后端](backend-contract.md)；本地数据→[本地数据](local-data.md) | 渠道/批次/版本分布、停止扩量/开关/前滚 |
| A10 小程序审核/基础库 | [发布](release-rollout.md)、[隐私](sdk-privacy.md) | 无 | 核验日期/政策来源、基础库/宿主、真机预览/通道 |
| A11 性能/包体 | [构建](build-signing.md)、[交互/生命周期](interaction.md) | 无 | 项目设备分层/预算、真机冷启/交互/资源数据 |

实际 feature/mobile 契约由项目就近页提供，不在平台模板复制；未登记不可假装存在。没有本地持久化的 A6/A8 不强制数据页，但必须证明该事实，发现本地队列/缓存再路由。

## 稳定性规则索引（revision 1）

- APP-STAB-001：[包身份](build-signing.md)及[SDK 隐私](sdk-privacy.md)；不旁路签名/用途/权限。
- APP-STAB-002：[本地升级](local-data.md)及[在用客户端](backend-contract.md)；不能假设立即更新。
- APP-STAB-003：[真机](device-verify.md)及[灰度](release-rollout.md)；模拟成功非可发布，停分发非撤回所有安装。

规则只在对应 scope 生效；项目登记实际 owner/执行器/证据，规范存在不代表渠道 enforcement。
