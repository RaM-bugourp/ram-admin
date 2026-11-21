# 平台适配层：插件 / 全栈 Web / APP

> 状态：可复用模板草案；独立建议，不改既有规划。仅采用项目实际需要的平台与子形态。
> 本文的目录、页面及执行器是待落地接口；未创建对应资源，未运行任何产品验证。

## 1. 选择与路由协议（与 core 协调的建议）

- 项目在现有入口登记 `platforms` 与子形态，例如插件仅 frontend-panel，APP 仅小程序；未选项不自动启用。
- 一个项目可选多类；跨平台任务取相关路由的上下文并集，标注各自目标，不能以一端通过替代另一端。
- 入口只保留任务信号、路由位置、适用范围、责任人，不汇总实现细节；正文由任务/领域就近维护。
- 路由沿用 core：`task → context_set.required/conditional → executor_refs[] → evidence_refs[]`；集合至少含契约/实现边界页与验证页。
- 所有表行额外继承 core 的入口、PR/测试边界、原规划对应章节、受影响实现/测试；不在每格复制。
- 先读入口及命中路由，再加载列出的多页集合；发现关联契约/风险时增量加载，不默认全库灌入。
- 每页声明 `scope / owner / status / applies_when / related`；路由失效应修复指向，不复制全文作新权威。
- scope 内的 PR 限制、测试边界、生命周期及数据安全规则可标为硬约束；入口必须显式提示并链接它们。
- 硬约束在其 scope 内不得被任务便捷方案绕开；不意味着平台页天然压过所有 core 规则。
- 两页相互冲突时列出条款、scope、影响与负责人，停止有风险动作，协调后只修规则所属页。
- 需要 SDK、账号、设备、宿主、隔离数据、skill 或执行权限时明确申请；缺失记为 blocked，不静默降级。
- 下列执行器均为待实现的能力 ID（接线时加 `proposed:`），不是已有命令；项目登记命令/工具、输入输出、版本及权限。
- 不提供虚假的 pass；mock/模拟器/本地服务的结果只覆盖自己的目标，不得冒充真实目标证据。
- 元 schema 归 core 的 `meta-schema/`，产品契约归 `contracts/` 或既有领域页；本文目录仅是可映射的逻辑视图，不要求平行造权威。
- 各类三条红线拟用 `PLG-STAB-001..003 / WEB-STAB-001..003 / APP-STAB-001..003`；落地时补 revision、owner、精确 scope、执行器/证据引用，状态保持 proposed。

### 证据封套 E（所有路由均适用）

- 必填：任务/路由 ID、规则及执行器版本、命令/工具与 cwd、基线/目标 commit SHA、environment、target、时间、退出码/工具状态、result、artifacts。
- 脏工作树另记 dirty diff 摘要及可追溯内容标识；构建物记 artifact hash 及对应源码，不能只写分支名。
- environment 含依赖/运行时版本、配置指纹及部署标识；target 写真实宿主、服务或设备实例及版本。
- 数据、设备和用户标识脱敏；密钥只记引用，不进入证据。证据产物需可访问且可追溯其采集方法。
- result 使用 core 五态 `pass / fail / blocked / not-run / not-applicable`；不适用需给 scope 依据，未实现执行器记 proposed / not-run。
- 附实际范围、未验证项、失败日志与复现路径；代码/dirty diff、目标、配置、权限、环境、规则/执行器或验收契约变化即重新判定/重跑，不沿用旧 pass。
- 下表“证据”指 E 加该格产物；发布接受哪些目标、覆盖矩阵及有效期由本项目定义，不在这里统一设阈值。

## 2. 插件适配层

### 2.1 适用性与目录片段

选择 `in-process / frontend-panel / remote-protocol` 中实际存在的形态；若跨形态，组合验证。
以下以 `docs/` 为文档根，路径为建议落点；真实项目沿用就近目录并在入口映射。

```text
docs/
  entry.md                       # 仅发现与分流
  plugin/route.md                 # 形态、任务路由、负责人
  plugin/host-compat.md           # 宿主 API/版本与降级边界
  plugin/lifecycle.md             # 注册、卸载、取消及资源所有权
  plugin/security-protocol.md     # 信任边界、远程协议及权限
  plugin/build-release.md         # 源码→产物→安装、来源映射
  plugin/verify.md                # 测试分层与真实宿主证据
  domains/<feature>/contract.md   # 就近功能契约
  ui/<panel>/isolation.md         # 面板 CSS/焦点/portal 边界
```

### 2.2 任务路由（路径均相对 docs/）

| ID / 任务信号（适用形态） | 多页 context_set | 待实现执行器 | 证据（均附 E） |
|---|---|---|---|
| P1 新增宿主能力（进程内） | plugin/host-compat.md + domains/<feature>/contract.md + plugin/verify.md | plugin.host-contract | 目标宿主 API/版本矩阵、功能正反向结果 |
| P2 启停/重载/卸载（各形态按资源） | plugin/lifecycle.md + domains/<feature>/contract.md + plugin/verify.md | plugin.lifecycle | 重复启停轨迹、监听/定时器/订阅/句柄释放、残留检查 |
| P3 异步请求取消（进程内/远程） | plugin/lifecycle.md + plugin/security-protocol.md + plugin/verify.md | plugin.cancel | 断连/卸载中的取消、超时、迟到回包不写失效状态 |
| P4 面板布局/交互（前端） | ui/<panel>/isolation.md + domains/<feature>/contract.md + plugin/verify.md | plugin.gui | 真实宿主版本/页面、操作录像或截图、焦点/键盘/窄屏结果 |
| P5 CSS/portal 调整（前端） | ui/<panel>/isolation.md + plugin/host-compat.md + plugin/verify.md | plugin.css-isolation | 宿主与相邻面板样式对照、卸载后 style/portal 残留 |
| P6 宿主升级（依赖该宿主的形态） | plugin/host-compat.md + plugin/lifecycle.md + plugin/verify.md | plugin.compat-matrix | 声明支持版本的真实宿主加载、使用及卸载记录 |
| P7 协议升级（远程） | plugin/security-protocol.md + domains/<feature>/contract.md + plugin/verify.md | plugin.protocol | 新旧端组合、未知方法/字段、断网重连与取消结果 |
| P8 权限/文件/网络访问（相关形态） | plugin/security-protocol.md + domains/<feature>/contract.md + plugin/verify.md | plugin.permission-negative | 拒绝/越界/失效凭据的无副作用断言、脱敏审计 |
| P9 构建/打包/安装（各形态） | plugin/build-release.md + plugin/host-compat.md + plugin/verify.md | plugin.artifact-host | commit→产物哈希→真实安装实例、加载入口及资源解析记录 |
| P10 热更新/包版本切换（支持时） | plugin/build-release.md + plugin/lifecycle.md + plugin/verify.md | plugin.update-cycle | 实际更新通道、旧实例退出/新实例接管、失败后的可用性 |

### 2.3 三条红线（仅所选形态 scope）

1. **资源所有权不缺席**：注册即定义清理责任，覆盖监听、计时器、订阅、请求、句柄、注入样式及 portal；卸载后不得继续操作宿主或提交迟到写入。
2. **兼容声明不靠猜**：不得用浏览器独立页或 mock 代替真实宿主 GUI/加载验证；未覆盖的宿主版本不宣称支持，缺环境明确 blocked。
3. **交付不得错源或污染宿主**：发布产物须可映射源码与安装实例；不得交付旧 bundle 冒充新源码，不得用全局 CSS/不受控 portal 破坏宿主与其他插件边界。

## 3. 全栈 Web 适配层

### 3.1 适用性与目录片段

选择实际的 `API / frontend / DB / deploy`；纯静态站不自动承担数据库迁移，但发布配置仍需明确。

```text
docs/
  entry.md
  web/route.md                   # 已选层、任务与上下游
  api/contracts.md               # 契约版本、鉴权与兼容
  frontend/integration.md         # 消费契约、缓存及错误状态
  data/migrations.md             # 工具账本、checksum、升级路径
  data/recovery.md                # 数据范围、RPO/RTO 与恢复验收
  deploy/config.md                # 配置 schema、必需项及密钥引用
  deploy/release.md               # 拓扑、发布顺序及恢复决策
  ops/observability.md            # 指标、日志、trace、告警责任
  web/verify.md                   # 分层测试、环境及真实服务验证
```

### 3.2 任务路由（路径均相对 docs/）

| ID / 任务信号（适用层） | 多页 context_set | 待实现执行器 | 证据（均附 E） |
|---|---|---|---|
| W1 API 字段/语义变更（API/消费者） | api/contracts.md + frontend/integration.md + web/verify.md | web.contract | schema diff、真实生产者/消费者版本组合、错误语义结果 |
| W2 登录/鉴权/租户隔离（API/前端） | api/contracts.md + deploy/config.md + web/verify.md | web.auth-negative | 匿名/越权/跨租户/过期会话矩阵、无泄露及无副作用断言 |
| W3 配置/密钥变更（部署/API） | deploy/config.md + deploy/release.md + web/verify.md | web.config-closed | 缺失/非法配置导致安全拒启或拒绝相关功能、密钥脱敏检查 |
| W4 结构迁移（DB/API） | data/migrations.md + api/contracts.md + deploy/release.md + web/verify.md | web.migrate-ledger | 真实目标引擎/版本、迁移前后账本与 checksum、旧新服务兼容 |
| W5 历史回填（DB/API） | data/migrations.md + data/recovery.md + web/verify.md | web.backfill | 数据快照范围、断点/重试策略、并发影响与完整性对账 |
| W6 备份恢复演练（DB/部署） | data/recovery.md + deploy/release.md + web/verify.md | web.restore | 真实目标环境恢复、数据完整性及业务可用验证、实测 RPO/RTO |
| W7 前端交互/缓存（前端/API） | frontend/integration.md + api/contracts.md + web/verify.md | web.browser | 实际浏览器/服务实例、弱网/错误/旧缓存路径、交互证据 |
| W8 发布/回退（部署/相关层） | deploy/release.md + data/migrations.md + deploy/config.md + web/verify.md | web.release | 实际部署 ID、路由流量、健康门禁、回退或前滚演练结果 |
| W9 故障诊断/告警（API/部署） | ops/observability.md + api/contracts.md + web/verify.md | web.observe | 真实请求 trace/脱敏日志、告警触达、故障与恢复关联 |
| W10 性能/容量变化（相关层） | ops/observability.md + deploy/release.md + web/verify.md | web.load | 项目批准预算、代表性负载/数据量/环境、原始结果与瓶颈 |

### 3.3 三条红线（仅所选层 scope）

1. **契约与安全不默认放行**：契约版本/兼容窗口必须明确；必需配置缺失或非法时 fail-closed，不能悄用生产默认值；鉴权必须含负向与跨租户验证，不能只验成功响应。
2. **迁移账本不篡改**：保留工具自身的排序、唯一标识及已应用记录语义；已应用脚本受 checksum 保护，修正用新迁移或工具正式修复流程并审计，不暗改历史/伪造账本。
3. **恢复与发布不靠口头保证**：项目先定义数据范围、恢复点/时间目标，再在获准的真实目标环境恢复并实测；备份存在、健康页绿或日志存在不等于业务恢复、鉴权正确或告警可用。

迁移补充：不强制全局连续编号；不要求已应用脚本可重复执行或逐条幂等。
“重复部署不重跑已完成迁移”由迁移工具/账本保障；回填的续跑和重试策略另行约定，不混淆两者。
恢复演练可在隔离的真实目标引擎/拓扑环境进行，不默认授权生产破坏性演练；代表性差异必须记入证据。

## 4. APP 适配层

### 4.1 适用性与目录片段

选择 `native / cross-platform / mini-program`，并记录实际 OS、容器与分发渠道；不默认全部平台上线。

```text
docs/
  entry.md
  app/route.md                   # 形态、系统/容器、渠道矩阵
  app/build-signing.md            # 构建变体、签名、产物身份
  app/sdk-privacy.md              # SDK 清单、权限与数据用途
  app/local-data.md               # 本地 schema、升级与数据保护
  app/backend-contract.md         # 服务兼容窗口、离线及重试
  app/device-verify.md            # 真机/真实容器、系统与网络矩阵
  app/release-rollout.md          # 灰度、停止分发、前滚与应急
  domains/<feature>/mobile.md     # 功能交互、后台/前台行为
```

### 4.2 任务路由（路径均相对 docs/）

| ID / 任务信号（适用形态） | 多页 context_set | 待实现执行器 | 证据（均附 E） |
|---|---|---|---|
| A1 构建/签名/渠道包（各形态） | app/build-signing.md + app/release-rollout.md + app/device-verify.md | app.signed-install | 产物哈希、签名/包身份校验、目标设备或真实容器安装/加载 |
| A2 接入或升级 SDK（使用 SDK 时） | app/sdk-privacy.md + app/build-signing.md + app/device-verify.md | app.sdk-audit | SDK/传递依赖清单、初始化时序、实际网络与权限行为 |
| A3 权限申请/隐私流程（相关形态） | app/sdk-privacy.md + domains/<feature>/mobile.md + app/device-verify.md | app.permission-negative | 真机拒绝/撤回/受限权限、同意前后采集行为及降级边界 |
| A4 本地数据库升级（持久化时） | app/local-data.md + app/release-rollout.md + app/device-verify.md | app.local-upgrade | 旧安装数据→新版本真实升级、断电/空间不足路径、数据对账 |
| A5 后端契约变更（联网时） | app/backend-contract.md + app/release-rollout.md + app/device-verify.md | app.backend-matrix | 在用旧客户端/新客户端与服务版本组合、兼容截止决策 |
| A6 离线/重试/同步（相关功能） | app/backend-contract.md + app/local-data.md + app/device-verify.md | app.sync | 真机断网/重连、重复提交与冲突处理、前后台中断后的状态 |
| A7 UI/原生桥接（跨端/相关原生） | domains/<feature>/mobile.md + app/sdk-privacy.md + app/device-verify.md | app.device-ui | 实机交互、桥权限/参数负向、系统导航及可访问性路径 |
| A8 后台/进程终止恢复（相关形态） | domains/<feature>/mobile.md + app/local-data.md + app/device-verify.md | app.lifecycle | 真实系统/容器挂起终止、重进、资源释放与未完成操作恢复 |
| A9 灰度/紧急缺陷（分发时） | app/release-rollout.md + app/backend-contract.md + app/local-data.md | app.rollout | 真实渠道/批次、版本分布、停止扩量、kill switch 或前滚验证 |
| A10 小程序审核/基础库升级（小程序） | app/release-rollout.md + app/sdk-privacy.md + app/device-verify.md | app.container-release | 指定平台/政策版本、基础库/宿主版本、真机预览及发布通道记录 |
| A11 性能/包体治理（相关形态） | app/device-verify.md + app/build-signing.md + domains/<feature>/mobile.md | app.device-budget | 项目设备分层与预算、真实设备冷启动/交互/资源测量 |

### 4.3 三条红线（仅所选形态 scope）

1. **包身份与隐私不可旁路**：签名密钥/渠道凭据不得入库或进日志；签名主体、包身份和环境必须校验；SDK 权限与采集按本项目获准用途、实际法规及平台政策逐项确认，不能以模板代替合规审核。
2. **升级不破坏已安装用户**：本地迁移保护现存数据并覆盖实际升级路径；后端兼容在用客户端，不能假设用户立即更新；不可逆迁移必须先有经验证的数据保护与发布阻断方案。
3. **模拟成功不等于可发布，发布不等于可即时回滚**：必需真机/真实容器缺失即 blocked；灰度须有停止扩量和应急责任人，旧安装包仍存续，停分发/关开关不等于撤回全部客户端或逆转数据。

## 5. 与通用 core 的协调清单

- **接口命名**：本文字段和执行器 ID 可由 core 统一命名；语义不应丢失多页集合、适用范围、真实目标与失败状态。
- **入口职责**：若 core 要求单一入口，它只承担发现；不得把所有开发细节集中为唯一依据，平台页继续指向就近领域页。
- **优先级**：需对齐 core 的规则层级；scope 内硬约束允许阻断任务，但跨 scope 冲突必须显式协调，不能凭“平台更具体”直接覆盖。
- **证据模型**：可复用 core 的封套并扩展目标字段；若只存命令退出码，需补 commit/环境/真实目标/产物映射与未验证项。
- **验收边界**：测试深度与 PR 限制以所属 scope 的稳定规则为准；本模板不私自扩大修改授权、生产权限或发布权限。
- **可移植性**：性能预算、支持版本、商店/小程序政策均由项目页面声明来源、版本与核验日期；不得升级为跨平台通用事实。
- **落地顺序**：先选适用性并映射现有页面，再接线执行器/申请能力，最后采集真实目标证据；未实现接口不可作为已执行检查列入验收。
