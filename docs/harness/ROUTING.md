# CORE-003 当前路由增量

2026-11-20；[任务卡](TASK-CORE-003.md)。fix/feature/security/api/data/ui/build/docs + Windows本地CLI，web-api/sqlite/web-frontend；W1/W2/W3/W4/W6/W7/W9；schema/local-files/local-tests；has_frontend/has_database=true。RAM既有rev1/advisory不变；W6加读web/data和operations正文，恢复只隔离新目标，不授权生产。writer ram-core-next，lead只读验收；unknown/无授权停任务、冲突停相交动作给lead。

---
# 路由与必读集合（revision 1）

CORE-002增量：当前卡TASK-CORE-002及COMPLETENESS；实际并集fix/feature/security/api/data/ui/build/docs，W1/W2/W3/W4/W7，web-api/sqlite/web-frontend、schema/local-files/local-tests，ram-admin-core执行，lead/ram-core-review只读验收。无部署授权，不因此排除本地真实HTTP/browser。冻结页正文实读记录见任务卡；规则仍advisory。下方TOKEN-001为历史，不用它删减CORE覆盖。

公共必读：AGENTS、PLAN、BRIDGE、OWNERS、当前任务卡、实际实现/测试；冻结1.0.0 docs/START-HERE、overview、adoption、routing、ownership、pr-boundaries、test-boundaries、evidence、task-lifecycle、capabilities；平台必读platforms/README、selection、evidence。以上由实施者于2026-11-18读完；副本来自冻结目录，载荷哈希需核对。

| 任务信号/ID | 追加正文（均在vendor/1.0.0/docs） | 实际owner/规则/check |
|---|---|---|
| 缺陷 fix | routing.md、实际复现/模块 | dev / RAM-SCOPE-001 / product-tests |
| 功能 feature | 实际serializer/service及任务卡 | dev / RAM-SCOPE-001 / product-tests |
| API api | platforms/web/README、api-config、verify；frontend为有消费者时追加 | dev / RAM-API-001 / product-tests |
| 安全 security | 同API，Token契约/威胁/授权/审计边界 | dev / RAM-API-001 / product-tests |
| 数据 data | platforms/web/data、operations，实际migrations | dev / RAM-DATA-001 / migration-tests |
| 前端 ui | platforms/web/frontend、verify、实际router/组件 | dev / RAM-UI-001 / frontend-build |
| 依赖/构建 build | 锁文件/requirements、test-boundaries | dev / RAM-BUILD-001 / frontend-build |
| 文档/规划 docs | adoption、maintenance、原规划桥接 | dev / RAM-DOC-001 / harness-routing |
| 发布 release/运维 | operations、data（有DB）、frontend（有消费者） | dev计划；用户批准人 / RAM-RELEASE-001 / deployment；本轮未授权 |

机读harness.json与tools/harness_checks.py提供8类代表性任务、跨域并集、unknown、未授权、冲突探针。所有规则advisory；离线工具不执行命令/发现Git/OS/授权。人工任务类型与机读维度同义，新增任务先显式列paths/platforms/domains/effects/actions/lifecycle/facts，不能用*事实代替发现。

当前TOKEN-001实际命中fix/security/api/data/build/docs，平台web-api/sqlite/web-frontend，副作用schema/local-files/local-tests，has_frontend=true、has_database=true（实际源码证明），no_deployment=true（本轮用户边界，不是产品无部署）。未知条件先只读发现；缺页/无匹配/未覆盖维度/未授权停全部动作；约束真冲突停相交动作交lead。范围/源码/配置/产物变化重resolve并复验相关证据，不复制旧digest复活pass。
