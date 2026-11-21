# 平台层离线验收记录

2026-11-14，仓库工作目录 `C:\c\Users\Rick\harness-template`；本记录仅覆盖平台文档和合成机器路由，不是产品证据封套/产品 pass。

## 实跑结果

| 命令/目标 | 实际结果 | 结论范围 |
|---|---|---|
| `python tools/harness.py lint --root . --manifest profiles/platforms/harness.json` | exit 0；31 routes / 31 rules / 1 manual executor / 1 synthetic owner | 核心 CLI 确实消费此 manifest，结构/引用有效 |
| `python tools/harness.py resolve --root . --manifest profiles/platforms/harness.json --task profiles/platforms/tasks/hybrid.json` | exit 0；A4/P5/W8；19 context files | 三平台上下文并集正确 |
| `python profiles/check_platforms.py` | exit 0；124 assertions；31 routes；17 conditional routes | 包括所有链接、逐路由、false/true/null/missing、静态/混合、越权/未覆盖新平台及空证据 |
| 所有 JSON/Markdown/Python/fixture 文本尾随空格扫描 | exit 0；0 issues | 仅本轮独占路径文本卫生 |

自检脚本通过核心 CLI 实际验证：静态发布 exit 0 且不含 DB 页；unknown DB exit 2 blocked；unauthorized/未覆盖平台 exit 2 blocked；空证据 evidence exit 2 not-run。它没有把预期非零吞掉，实际与预期不符将整体失败。

## 发现与修正

- 首次 hybrid resolve exit 1 `E_TYPE`、`$/lifecycle`、`expected string`：生成任务误把 task.lifecycle 写成 scope 数组；已读核心 task schema，修正全部 34 任务为字符串，随后核心 CLI 与完整自检通过。scope.lifecycle 仍为数组，未自造格式。
- `git status --short` 报 `fatal: not a git repository (or any of the parent directories): .git`。无 Git 仓库，不能提供 commit/dirty 基线或声称 scoped Git diff 通过；后续 `git diff --check -- docs/platforms profiles` 在此环境为 no-index 目录比较，不作为有效基线证据。未初始化/修复仓库，未改授权外路径。
- 自检运行使用 `profiles` 下自动清理的临时任务目录，验证核心真实消费，而非另写匹配器冒充核心结果。所有后台验收任务均须收集后交付。

## 明确未完成/不在范围

真实项目原规划/功能契约/实现/测试、实际 owner/权限/target 均待采用项目映射；当前为 simulated 合成 fixture。执行器仅 proposed 人工身份，不执行产品命令。无 profile 自动加载器、CI/required checks/分支保护、宿主、真实服务/DB/恢复、签名、真机/渠道/灰度或生产接线与验收；本地离线通过不外推这些结果。不绑定任何产品或框架，不修改历史草稿及产品规划。
