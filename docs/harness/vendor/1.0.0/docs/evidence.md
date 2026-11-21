# 证据生命周期、五态与强度分轴

机器封套、严格字段与语义以 [FORMAT](../spec/FORMAT.md) 为唯一技术契约；[证据卡](../templates/evidence-card.md) 是人类采集清单，不是有效 JSON 记录。不得将占位卡当真实证据输入，或从模板制造绿色结果。

## 两个正交轴

| 结果状态（规范小写） | 含义 | 下一步 |
| --- | --- | --- |
| `pass` | 当前范围/目标实际执行且满足断言，有有效证据 | 仅参与相同范围验收 |
| `fail` | 执行或有效观察表明要求不满足 | 修复并复验，不能冒充环境缺失 |
| `blocked` | 明确依赖、权限、环境、未知条件或证据障碍使当前判定无法完成 | 给责任方与解阻路径 |
| `not-run` | 适用但未执行，且没有已确认硬障碍；或旧证据已失效 | 安排实际执行 |
| `not-applicable` | 可审查 scope 证明当前规则不适用 | 保留不适用依据 |

UNKNOWN 是条件事实未定，不是第六种结果；会阻塞相应解析/动作。环境/账号缺失不等于不适用。展示文字可翻译，机器输入只能用上述枚举。

`proposed` / `advisory` / `enforced` 描述规则的执行面强度，独立于一次检查的五态。人工检查 pass 不会把 proposed 升为 enforced；自动脚本存在不等于实际阻断；强制规则也可能 fail。执行器 `manual` / `automated` / `schema` 是种类，亦非结果。

## 从采集到失效

1. **计划**：对当前真实声明运行 resolve，从适用规则得到检查 ID，并原样取得输出 `routing_digest` 写入每条机器证据；不要手造/复制演示哈希。明确断言、目标、执行器及版本、环境、时效和脱敏策略。digest 绑定 manifest、完整 task 与全部声明 source/required/conditional 页的内容摘要，含尚未触发的条件页。
2. **执行与采集**：记录 change、规则 revision、执行器版本、scope、源码基线/commit/dirty digest、环境摘要、真实 target、产物与哈希、带时区采集/截止时间、命令/步骤、cwd、退出码/观察、限制。target 不能只写“本地/最新/未知”。
3. **当前校验**：对照当前任务所有绑定、产物字节、规则/scope、时间与失效触发器；读取真实配置的责任不会被 JSON 摘要替代。v1 pass 还要求 performed=true、exit_code=0、非空命令/观察、产物、非 schema 执行器及非模拟目标。
4. **评审与使用**：确认实际断言与覆盖，不把签名未验或人工声明当自动可信。每条记录只支持其声明的断言。
5. **失效与复验**：`invalidation_triggers` 必须包含 source、environment、target、artifacts、rule、executor、scope、change、routing 九项。任务维度/路径/facts、manifest 或声明页正文变化均须重新 resolve；旧记录可出现 `routing-changed`。保留历史 status，不覆写旧结果；工具给出当前 not-run 和失效原因。重验/重新采集后生成当前绑定记录，不只换 digest 复活旧 pass。已知复验障碍由当前任务另报 blocked，不伪造历史 fail。
6. **留存与退出**：按项目保留期保护原始证据及审计链；脱敏，不保存密钥。清理策略不得破坏仍被采用/发布引用的证据，退出也不抹历史。

## 汇总与边界

适用项优先级为 fail > blocked > not-run > pass；全不适用是 not-applicable，无适用检查需已解析 scope 依据。缺 required 记录是 not-run，未知条件/冲突为 blocked。部分通过不抵消其他状态。当前无效的旧 pass 不计绿灯。

证据验证器是离线一致性检查，不是签名/来源真实性验证、操作系统/Git 状态发现、授权器、产品验收器或远端保护执行器。声明的 digest 和身份须由采集者/评审者在真实环境核实，不能仅靠 JSON 自证。

## 实跑本包示例

命令、路径与退出码详见 [FORMAT](../spec/FORMAT.md)。使用 examples 中标明的演示根，不把 templates 的占位页作为 `--records`。`--now` 使用有时区 RFC3339 实际校验时间，不通过回拨时间让旧证据重新有效。lint exit 0 仅结构/引用有效；证据 exit 0 也只表示请求的离线一致性结果，不背书产品和 CI。
