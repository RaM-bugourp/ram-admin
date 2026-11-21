# 可复用 Harness 工程文档架构：核心模板

> 状态：设计草稿／模板未部署。本文不表示任何 CI、分支保护、检查器或权限配置已经安装。
> 范围：新增可共存的治理层；不修改、取代或重解释用户已认可的原规划。

## 1. 设计原则
- 路由主义：入口只帮助发现与分流；任务、领域、平台各有就近细节页，不能只读入口就开工。
- 权威属于带 scope 的规则与事实来源，不属于某个文件名；AGENTS 不是唯一细节权威。
- 约束分布在对应责任域：PR 规则归 PR、测试边界归测试、安全规则归安全，禁止汇总成万能最高文件。
- 稳定性硬约束可在明确 scope 内优先于普通建议；不能据此覆盖其他领域或用户授权边界。
- 先暴露目的、动作、风险和必读集合，再按需加载细节；省上下文不得牺牲正确性。
- 文档行数、入口大小、理想三跳均是可评审预算，不是删掉必要约束或拒读依赖的硬上限。

## 2. 推荐目录（均为待采用的目标结构）
```text
AGENTS.md                         # 根入口：发现、风险提示、路由，不承载全套规则
<module>/AGENTS.md                # 模块入口：本地覆盖范围与追加路由
harness/
  README.md                      # 人类导航、采用状态、原规划桥接
  routes/tasks.yaml              # 任务触发器→上下文集合及规则引用
  meta-schema/route.schema.json  # Harness 路由元 schema
  meta-schema/rule.schema.json   # Harness 规则元 schema
  contracts/                     # 产品 API、配置、数据 schema；按领域拆分
  tasks/{bugfix,feature,refactor,docs}.md
  domains/{security,data,api,dependencies}.md
  platforms/{windows,linux,web,desktop}.md
  stability/pr-boundaries.md      # PR 范围、历史保护与高风险动作规则
  stability/test-boundaries.md    # 测试边界、可信证据及禁止规避规则
  owners.yaml                    # 领域 owner 与替补；不是规则正文
  decisions/                     # 跨域裁决、例外与到期记录
  adapters/legacy-plan.md         # 原规划链接、语义映射、差异；不复制改写原文
  evidence/<change-id>/           # 本次执行记录；不得存密钥或未脱敏数据
<module>/harness/                 # 模块契约、规则、验证、局部决策
```
目录是示例而非强制迁移：已有同义页面直接挂接；同一规则正文只维护一处，可被多路由引用。
源代码、接口声明、配置、锁文件及实际运行结果仍是其相应事实源，文档不能捏造实现状态。

## 3. 入口与加载协议
1. 读根入口及变更路径沿途模块入口；确认仓库身份、当前任务、允许范围、不可逆风险。
2. 用任务类型、受影响路径、领域、平台、副作用匹配路由；先用适用性清单选择实际平台／子形态，多项命中取集合并集。
3. 加载匹配路由的 required、适用硬约束、原规划对应章节、契约及相关实现／测试；按条件扩展 optional。
4. 开工前输出上下文清单：已读版本、适用规则 ID、未解决冲突、缺失资源、验证计划。
5. 扩大 diff、触及新平台／领域或发现未知副作用时重新路由；未知类型先做只读发现，不猜默认权限。
入口只保留高风险动作的醒目摘要及到规则的链接；摘要与正文冲突应暂停相应动作并登记修复。
必读页缺失、过期不可判断或无法访问时标记 blocked，申请材料；不把“未读”视为“不适用”。

## 4. 任务→必须读的上下文集合
下表每行均隐含：根／沿途入口、PR 边界、测试边界、原规划对应章节、受影响实现与相关测试。
| 任务触发 | 额外必读集合 | 典型补充证据 |
| --- | --- | --- |
| 修复缺陷 | bugfix 任务页＋模块契约＋复现记录＋所属平台页 | 修复前失败、修复后通过及邻接回归 |
| 新增功能 | feature 任务页＋领域设计＋API／配置 schema＋模块扩展契约 | 验收条件、正反向与权限测试 |
| 重构 | refactor 任务页＋依赖图／模块边界＋行为兼容契约 | 行为不变证明、兼容与回归结果 |
| API／协议变更 | api 领域页＋版本契约＋调用方路由＋迁移说明 | 消费者契约、旧版本兼容验证 |
| 数据库／数据迁移 | data 领域页＋数据 schema＋恢复手册＋目标平台页 | 脱敏夹具、迁移／回滚与数据校验 |
| 安全／权限变更 | security 领域页＋威胁模型＋权限 schema＋审计契约 | 默认拒绝、越权负例、脱敏审计 |
| 依赖／构建升级 | dependencies 领域页＋锁文件策略＋构建／发布平台页 | 可复现构建、许可／漏洞与兼容结果 |
| UI／可访问性 | feature 任务页＋组件契约＋web／desktop 平台页＋可访问性标准 | 真实目标 GUI、键盘、窄视口验证 |
| 测试／CI 变更 | 测试边界＋受测领域契约＋平台矩阵＋CI 权限说明 | 负向样例、门禁确实拦截的证据 |
| 发布／运维 | 发布任务页＋供应链规则＋平台安装／回滚页＋版本规划 | 真实制品、签名、部署／回滚证据 |
| 纯文档／规划桥接 | docs 任务页＋被引用契约＋原规划＋对应 owner 表 | 链接、语义一致性、无实现状态虚报 |
跨域任务必须合并多行；例如带迁移的安全 API 改动须同时读 API、数据、安全、平台及原规划集合。

## 5. 路由与规则 schema（示意，校验器待实现）
```yaml
route:
  id: task.api-change
  match: {tasks: [api-change], paths: ["src/api/**"], platforms: [any]}
  match_mode: task_or_path           # 显式布尔语义；命中平台维度仍需满足
  context_set:
    required: [harness/domains/api.md, harness/stability/pr-boundaries.md]
    conditional: [{when: "changes_persistence", add: [harness/domains/data.md]}]
  rule_refs: [API-COMPAT-001, PR-SCOPE-001]
  executor_refs: [proposed:check-api-contract, proposed:check-change-scope]
  evidence_refs: [api-contract-result, diff-report]
  owner: api-maintainers
  fallback: block-and-discover
rule:
  id: PR-SCOPE-001
  revision: 1
  kind: hard-constraint
  scope: {actions: [edit, stage, commit], paths: ["**"], exclusions: []}
  statement: "未获授权不得覆盖既有修改；提交范围须与批准任务一致。"
  owner: repo-maintainers
  source: harness/stability/pr-boundaries.md
  executor: proposed:check-change-scope
  evidence: [base-revision, pre-change-snapshot, approved-paths, diff-report]
  enforcement: proposed             # proposed / advisory / enforced，不能由写文档自动升级
  escalation: repo-maintainers
  exceptions: explicit-record-only
```
结构要求：ID 唯一、引用可解析、owner 有联系／替补、scope 可判定、证据含版本；缺字段不默认放行。
路由 schema 必须定义匹配语义、重复合并、条件表达式与未识别字段处理；不以字符串备注冒充执行逻辑。
规则元数据可建立索引供查询，但索引不是新权威；正文、scope、执行状态需可追溯到对应责任页。

## 6. owner→规则 ID→执行器→证据闭环
| owner | 规则及适用范围 | 执行器（拟议接口） | 必要证据／失败状态 |
| --- | --- | --- | --- |
| 仓库维护者 | PR-SCOPE-001：编辑／暂存／提交范围 | check-change-scope | 基线、既有 diff、批准范围、最终 diff；未授权改动 fail |
| 测试维护者 | TEST-BOUNDARY-001：变更影响的测试 | check-test-integrity | 测试 diff、数量／跳过差异、失败复现、运行结果；缺环境 blocked |
| 安全 owner | SEC-PERM-001：权限边界修改 | check-permission-contract | 拒绝负例、最小权限、审计；未执行不算 pass |
| 发布 owner | REL-PROTECT-001：受保护分支合并／发布 | inspect-branch-protection | 远端配置、权限、required checks；API 无权读／配置 blocked |
完整例子：一次 API 缺陷修复批准只改处理器与对应测试。PR-SCOPE-001 的 owner 先确认路径集合。
执行器比较工作前快照、基线 SHA 与最终工作树／暂存区，保留用户既有差异；若新增无关锁文件则 fail。
证据封套记录 change-id、规则／执行器版本、命令、cwd、环境、平台及真实 target（URL／DB／设备／宿主版本）、基线／目标 SHA、dirty diff 摘要、时间、退出码、结果／限制、脱敏日志与制品摘要。
封套须含有效期／失效条件：目标版本、代码或 dirty diff、配置、权限、环境、规则／执行器或验收契约变化时重新判定／重跑，不复用旧 pass。
维护者审阅差异报告并签署；只在真实执行且所有适用条件满足时该规则 pass，不代表整个 PR 或生产部署通过。
执行器尚未实现时记录 proposed / not-run，人工评审可记人工证据但不能伪装自动门禁已通过。
所有上述命令名只是待实现接口；模板未安装脚本、CI job、分支保护或远端 API 权限。

## 7. scope 与冲突处理
- 先判是否适用：任务、路径、动作、平台、生命周期均须纳入；路径更近并不自动胜过适用硬约束。
- 同 scope 下兼容规则累计执行；局部细节可细化普通建议，但不得静默解除适用硬约束。
- 原规划拥有产品目标／验收语义；平台页拥有平台事实；稳定性页仅拥有自身约束范围。无“所有问题以 X 为准”。
- 不能同时满足、scope 重叠不清、事实源与文档不符：暂停冲突动作，允许不依赖该动作的只读调查。
- 记录冲突双方 ID／版本／scope、任务、候选方案及风险；交责任 owner，跨域交双方 owner 与指定裁决人。
- 例外需有有权批准人、理由、精确范围、补偿措施、到期／撤销条件与证据；用户禁令不得由 owner 自行豁免。
冲突例：平台页建议禁用不稳定端到端测试，TEST-BOUNDARY-001 禁止未经批准缩小验收边界。
处理：不加 skip、不宣称通过；提交失败证据给平台与测试 owner，申请隔离环境或有期限的补偿方案。
若尚无授权或运行环境，则该测试 gate 为 blocked；产品原规划不改，待条件满足重跑，不通过改文案消灭要求。

## 8. PR／测试边界红线（正文分别留在所属页）
- PR：禁止擅自重写历史、force push、删用户文件、覆盖既有 dirty changes、扩大任务范围或提交秘密。
- 建立工作前快照并区分本次改动与既有改动；无法区分时先申请确认，不以清理工作树解决。
- 合并／发布受批准范围、review 与远端保护配置约束；本地通过不能替代远端实际配置证据。
- 测试：禁止为通过而删除／跳过测试、放宽断言／阈值、替换成无效 mock、减少平台矩阵或掩盖失败。
- 允许合理修改测试，但必须说明需求／契约变化、保留等效或更强边界、补负例，并由测试责任人审核。
- 记录实际命令和覆盖范围；定向测试不等于全量，离线夹具不等于真实集成，dry-run 不等于 enforcement。
- 状态至少区分 pass、fail、blocked、not-run、not-applicable；后者需给出 scope 不适用依据，不能稀释 required gate。
- 环境、沙箱、skill、网络、账号、GUI 或工具能力不足时明确申请所需能力与风险；稳定性／质量优先，不静默降级。

## 9. 模块扩展与失效维护
1. 新模块沿用入口协议，增加本地契约、任务路由、owner、规则 ID 前缀及最小验证集合，无须复制根页。
2. 模块 manifest 声明路径、平台、对外接口、依赖、路由入口、证据位置；跨模块任务取双方集合。
3. 新硬约束先声明 scope、owner、执行器与证据；缺执行器保留 proposed，并暴露未部署状态。
4. 契约／路径／owner 变更时同步路由和链接；规则 ID 稳定，正文变更升 revision，旧证据保留对应版本。
5. 移除规则须保留替代／废弃记录；失效链接、孤立模块、无 owner、重叠 scope 纳入后续检查器检测。
6. 定期抽样真实任务：能否发现必读集合、是否过度加载、是否漏关键边界；以错误率和总工作量优化预算。

## 10. 与原规划共存
- 原规划保持原路径、原编号、原里程碑、原验收；本模板不生成替代规划，不追溯修改已认可内容。
- 桥接页只记录“原章节→任务路由／规则／证据”的映射、已知缺口与实施状态，并链接原文。
- 工程约束暴露原规划实现缺口时记录差异，执行原有变更流程；不得擅自降级目标或改称已经完成。
- 采用模板、实现执行器、启用 CI、配置远端保护、达到里程碑分别验收，禁止一个勾选替代全部。

## 11. 最小落地阶段与验收
| 阶段 | 范围 | 验收／停止条件 |
| --- | --- | --- |
| S0 盘点 | 只读发现既有规划、规则、工具、权限与 dirty state | owner 确认映射及边界；未知不猜 |
| S1 文档接线 | 经批准新增入口路由、领域页与桥接，不迁移原规划 | 至少八类任务可得到完整上下文集合，冲突可升级 |
| S2 本地验证 | 单独实现 schema／链接／规则与证据校验器 | 正反向夹具通过；能报告 blocked／not-run，失败不吞掉 |
| S3 试运行 | 小范围真实 PR 记录人工与自动证据 | 检查漏路由、误报与成本；advisory 明示不冒充强制 |
| S4 门禁启用 | 获授权后接 CI、required checks 与远端分支保护 | 实测不合规变更被拦截；权限不足记 blocked，不记 pass |
每阶段均需独立批准、可回退及真实证据。当前仅交付核心模板设计，S0–S4 均未据此视为完成。
