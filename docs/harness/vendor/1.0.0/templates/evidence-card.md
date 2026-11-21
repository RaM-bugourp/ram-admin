# 证据采集卡：{{记录ID}}

> **人工模板，不是有效机器记录。** 不填造pass，不复制演示摘要。严格封套见 [FORMAT](../spec/FORMAT.md)，状态/强度分轴见 [证据协议](../docs/evidence.md)。

- change/任务及当前路由绑定：{{任务输入、resolve输出定位与routing_digest原值；不手造哈希}}
- 路由内容变化：{{manifest/task/全部声明正文变化后重新resolve并复验/采集；不只换digest复活pass}}
- 规则ID/revision与scope：{{准确版本与范围}}
- 检查ID/断言：{{实际可验证目标}}
- 执行器ID/版本/种类与实际执行人：{{身份}}
- 强度及接线证据：{{proposed/advisory/enforced；不得由一次pass自动升级}}
- 源码基线/当前revision、dirty内容摘要：{{采集事实}}
- 环境：{{OS/架构/shell/工具链/配置/权限/依赖摘要}}
- 真实target：{{类型、唯一身份、版本、是否模拟；不只写本地/最新}}
- 产物：{{实际路径、SHA-256及脱敏日志定位}}
- 采集时间/时区与截止：{{有限且有序}}
- 失效触发：source/environment/target/artifacts/rule/executor/scope/change/routing九项及{{额外条件}}
- 实际执行：{{是否执行、原命令或交互步骤、cwd、退出码或观察}}
- 当前结果：{{pass/fail/blocked/not-run/not-applicable之一；未执行不填pass}}
- 不适用依据：{{仅scope证明；缺环境不是N/A}}
- 限制/未覆盖：{{目标、平台、替身与取证真实性边界}}
- 复验/责任方：{{下一步、阻塞申请与失效原因}}

保留历史结果；失效后当前视图重验，不改写历史。静态格式验证不证明产品、外部授权或真实CI保护。
