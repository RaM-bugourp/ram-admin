# 平台 profile 与机器可消费性

本目录不是新的配置格式，也没有 profile 自动发现/继承/安装器。所有 JSON 严格遵守唯一的 [FORMAT](../spec/FORMAT.md)。当前提供一份由核心 CLI **显式消费**的独立 manifest：`platforms/harness.json`，需要以本仓库根为 `--root .`，因为它直接引用正式领域页面而不复制规范。不能把根设为本目录后用 `../` 绕路径约束。

## 包含什么

- [机器路由目录](platforms/harness.json)：P1–P10、W1–W10、A1–A11，31 条 route/rule；required/conditional 与正式平台路由一致，调用方同时给任务/路径/平台才命中。
- [继承上下文与采用缺口](platforms/context.md)：明确哪些是占位，以及真实产品还须映射的原规划/任务/功能契约/实现/测试。
- `platforms/tasks/P1.json` 至 `A11.json`：每路由一个合成任务；平台值开放，形态按实际项目登记，不是 schema 闭集。
- [静态发布](platforms/tasks/static-web-release.json)：DB=false 有意省去迁移页，保留配置/发布/前端。
- [unknown DB](platforms/tasks/unknown-web-db.json)：DB=null，必须 blocked，不能解释成 false/N/A。
- [跨平台任务](platforms/tasks/hybrid.json)：P5+W8+A4，必须取三个平台上下文并集，去重页面不抵消目标证据。
- [空证据](platforms/evidence/records.json)：没有伪造 pass；适用检查应返回 not-run。target 全为 simulated，不可用于产品 pass。

合成 source/environment/target/hash fixture 仅做本地格式/路由测试；example.invalid owner 不是真实联络；`proposed:platform-target-observation` 是人工身份，不是可运行检查命令。机器 CLI 能读取它不表示真实执行器、profile 加载器、CI、宿主、签名或生产已接线。

## 实际命令（仓库根，Python 3.10+）

```text
python tools/harness.py lint --root . --manifest profiles/platforms/harness.json
python tools/harness.py resolve --root . --manifest profiles/platforms/harness.json --task profiles/platforms/tasks/static-web-release.json
python tools/harness.py resolve --root . --manifest profiles/platforms/harness.json --task profiles/platforms/tasks/hybrid.json
python tools/harness.py resolve --root . --manifest profiles/platforms/harness.json --task profiles/platforms/tasks/unknown-web-db.json
python tools/harness.py evidence --root . --manifest profiles/platforms/harness.json --task profiles/platforms/tasks/hybrid.json --records profiles/platforms/evidence/records.json --now 2026-11-14T10:00:00Z
python profiles/check_platforms.py
```

预期：lint/静态/hybrid exit 0；unknown exit 2 blocked；空证据 exit 2 not-run。最后一条自动检查内部链接、31 路由逐一命中、条件 true/false/unknown、静态站排除数据、混合并集与无伪证据，失败非零退出。它不运行产品命令。

## 采用流程与边界

人工先[选择](../docs/platforms/selection.md)实际层/形态；复用[平台页面](../docs/platforms/README.md)而非机械读取全部。将需要的 route/rule 按 FORMAT 合并进自己的 manifest，并按项目真实 paths/tasks/platforms/facts 定义匹配；不能照搬合成标签后声称路径自动发现。替换 owner、实际原规划/契约/测试引用、真实 source/environment/target/artifacts；unknown 保持阻断直到查明。新类别按[扩展流程](../docs/platforms/extensions.md)添加能力组合，不引入第二套字段。

本目录只交付离线路由与文档验收；真实产品检查未执行，外部 CI/宿主/生产接入不在本轮授权内。实际命令结果、曾遇失败与 Git 基线限制见[验收记录](VALIDATION.md)。
