# Web 任务路由

> scope：实际 frontend / API / DB / deploy 层。owner：采用项目的 Web 维护者。status：规范；非已部署服务。applies_when：Web 或服务任务。related：[选择](../selection.md)、[证据](../evidence.md)。

每行继承公共选择、项目任务/稳定性/原规划及实际契约/实现/测试，并读[验证](verify.md)。已证实无 DB 的静态站不读迁移页；unknown 不是 false。API 消费契约不意味着强制有本地后端。

| ID / 任务信号 | 必读领域页 | 条件追加 | 关键证据/负例 |
|---|---|---|---|
| W1 API 字段/语义 | [API/配置](api-config.md) | 有前端消费者→[前端](frontend.md) | schema diff、真实生产者/消费者版本、错误语义 |
| W2 登录/鉴权/租户 | [API/配置](api-config.md) | 有前端→[前端](frontend.md) | 匿名/越权/跨租户/过期、无泄露/副作用 |
| W3 配置/密钥 | [API/配置](api-config.md)、[运维发布](operations.md) | 无 | 缺失/非法配置拒启或拒功能，脱敏 |
| W4 结构迁移 | [数据](data.md)、[API/配置](api-config.md)、[运维发布](operations.md) | 无 | 真引擎/版本、前后账本/checksum、旧新服务 |
| W5 历史回填 | [数据](data.md) | 影响 API→[API/配置](api-config.md) | 快照、断点/重试、并发、完整性对账 |
| W6 备份恢复 | [数据](data.md)、[运维发布](operations.md) | 无 | 获准真实引擎/拓扑恢复、业务/RPO/RTO |
| W7 前端交互/缓存 | [前端](frontend.md) | 消费 API→[API/配置](api-config.md) | 真实浏览器/服务、弱网/错误/旧缓存 |
| W8 发布/回退 | [运维发布](operations.md)、[API/配置](api-config.md) | 有 DB→[数据](data.md)；有前端→[前端](frontend.md) | 部署ID、流量/健康、实际回退或前滚 |
| W9 故障/告警 | [运维发布](operations.md) | 涉 API→[API/配置](api-config.md) | 请求 trace/脱敏日志、告警触达、故障恢复关联 |
| W10 性能/容量 | [运维发布](operations.md) | 涉 DB→[数据](data.md)；涉 UI→[前端](frontend.md) | 批准预算、代表负载/数据/环境、原始结果 |

W4–W6 仅实际数据任务匹配；若信息与任务标签矛盾（称静态站却改迁移），先发现并修任务事实，不能用 false 掩盖路径风险。机器 manifest 按已选组件编写，条件集合用于剩余变化，不凭空给任务部署权。

## 稳定性规则索引（revision 1）

- WEB-STAB-001：[API/配置](api-config.md)的兼容、鉴权负例与 fail-closed。
- WEB-STAB-002：[数据](data.md)的迁移工具账本/checksum 与历史保护。
- WEB-STAB-003：[数据恢复](data.md)及[运维发布](operations.md)的实测恢复/发布边界。

规范为相应 scope 硬边界，项目登记 owner/执行器/证据；不表示自动门禁生效。
