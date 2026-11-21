# 真实目标与证据边界

> scope：所有平台路由的验证结果。owner：采用项目的测试与平台维护者。status：规范；不声明产品通过。applies_when：计划、采集或复用证据时。related：[适用性](selection.md)、[核心格式](../../spec/FORMAT.md)。

## 只有一套机器封套

机器文件严格使用[FORMAT](../../spec/FORMAT.md)；本页仅解释平台语义，不另造 schema。证据绑定 change、规则 revision、执行器 version、scope、源码 commit/dirty 内容摘要、环境/依赖/配置/权限摘要、真实 target、产物 bytes/hash、命令与 cwd、采集时间/时区、有限有效期和失效条件；`routing_digest` 绑定本次 manifest/task 与上下文正文，失效触发器须包含核心协议要求的 routing 等全部项。敏感标识脱敏、密钥只记录引用。每项写原始观察、限制和未验证项，日志须可定位。

真实 target 是可区分实例与版本，不是“本地/最新”。构建产物以 hash 关联源码和实际安装/部署实例；截图绑定页面/宿主/设备、版本及操作路径，单张截图不能证明取消、清理或权限无副作用。项目决定代表性矩阵、预算和有效期，但不能留空或无限有效。

## 五态及两条轴

- pass：已在声明的非模拟真实目标执行并满足断言；仅覆盖该 scope。
- fail：执行过且断言不满足；不能改标 blocked 隐去缺陷。
- blocked：明确权限/依赖/环境/条件 unknown 阻碍判定；列解阻路径。
- not-run：适用但未执行，尚无明确硬阻碍；缺 required 记录不能算通过。
- not-applicable：有可审查的 scope 排除依据；缺权限/环境/信息不适用此态。

聚合按 fail > blocked > not-run > pass；全部不适用才 N/A。保留部分通过数量但不能抵消失败。proposed/advisory/enforced 是执行面状态，不是第六种结果。静态检查、lint、mock、模拟器与 schema 检查可报告各自实际结果，但不等于真实宿主/服务/设备产品 pass。核心 CLI 是离线一致性核验，不证明签名真实性、测试真的执行、管理员批准或运行时 enforcement。

## 失效与边界

源码/dirty、产物、环境、配置、权限、目标、scope、规则/执行器或 change 变化须重判/复跑；历史状态保留，当前失效状态转 not-run，复验缺条件转 blocked。迁移/隐私/供应链等批准与 owner 签署还须保留项目所需记录，不能从离线退出码推断真实授权。

CI YAML、分支保护、真实阻断、宿主安装、生产发布分别验收。本文及示例不安装这些系统；未获授权不得试生产破坏性负测。隔离的真实目标可验证获准范围，但必须披露与生产的引擎/拓扑/负载差异。
