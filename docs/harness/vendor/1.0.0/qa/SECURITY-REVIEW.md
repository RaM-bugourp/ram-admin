# 第五路独立只读安全审查

日期：2026-11-14。审查对象：通用离线 Harness 核心，不代表产品/CI/权限验收。只写本报告；未修改实现、schema、测试或其他 QA 文件，未安装依赖、访问网络或生产。已加载 agent-experience 技能。

结论：确认 3 项缺陷，均不是误 pass 漏洞；前两项影响通用成品的合法输入可用性，第三项影响 CLI 对不可信 JSON 的稳定错误协议。未发现新的高影响放行阻断。不重复报告正在修复的 schema 全遍历、routing_digest 绑定、route-only check/executor 问题。

修复/复测状态（2026-11-14 18:23）：第 1、2 项已由技术 owner 修复，本审查已在临时目录独立完成 9 项定向 CLI 复测，全部符合预期：OR-path-only exit 0、OR-task-only exit 0；OR 下 platform/domain/effect 各自不匹配均 exit 2；字面方括号 task path/source 均 exit 0；文件引用含星号和路径穿越仍 exit 1。复测前后核心 SHA-256 相同：6d32b81d9dc3d4ad0f64cae77e0a57676926ae04db1cf2987b6b5b87aaf698ea。下文两项实际结果保留为修复前证据，行号也是发现时快照。第 3 项亦已修复并独立完成 9 项定向 CLI 复测：D800/DFFF 各作 object key、value、list item、重复坏 key 的 8 例均稳定输出 JSON、exit 1、E_UNICODE；正常中文+emoji 同时放 change_id 与 facts key 的正向例 exit 0/pass。最终复测核心 SHA-256 同为 6d32b81d9dc3d4ad0f64cae77e0a57676926ae04db1cf2987b6b5b87aaf698ea，前后不变。本审查 3 项发现均已修复并经总计 18 项定向复测确认，后文保留修复前发现与初始异常。可发布建议：就本轮审查范围，同意作为通用离线一致性工具发布；最终集成验收由父会话统合各路 QA，不能据此声明产品执行、授权或文件系统竞态保证。未发现高影响误 pass 不等于无漏洞；FS race、离线授权真实性未验证，历史 artifact invalid 为已披露限制。

## 1. P2：task-or-path 模式在只由 path 命中时被后续 coverage 误阻断

位置：`tools/harness.py:150-158` 正确实现 OR；`tools/harness.py:238-240` 给路径覆盖作 OR 补偿；`tools/harness.py:261-264` 对 tasks 覆盖仍只作集合交集。

契约：`spec/FORMAT.md:18` 明确 task-or-path 下 tasks/paths 为 OR，其他维度 AND。

最小变更：使用下文单规则基线，将 route.match.mode 改成 `task-or-path`，task.tasks 改成 `["bugfix"]`，保持 task.paths 为 `["src/a.txt"]`。

实际 CLI：exit 2，status=blocked，matched_routes=["route"]，errors=[{"code":"E_UNCOVERED_DIMENSION","path":"$/tasks","message":"reroute uncovered values: bugfix"}]，stopped_actions=["edit"]。

预期：路径分支已满足 OR，且其他维度合法，应 exit 0/status=pass。coverage 不应推翻已经明定的 OR 语义。

影响：按目录路由的 bugfix 等新任务标签会被迫人为加入 route.tasks；实际发现的路由和规则已经齐全，仍阻断合法行动。

反向实跑：task.tasks=["build"]、task.paths=["other/a.txt"] 时同一 OR route exit 0/pass；route.match.platforms=["linux"]、task.platforms=["win"] 时 exit 2/blocked 正确。修复应保持这些边界，不应把 OR 扩展到 platform/domain/effect。

## 2. P2：将方括号当作文件引用通配符，拒绝合法工程路径

位置：`tools/harness.py:42-43`；调用点 `tools/harness.py:179`、`tools/harness.py:218`、`tools/harness.py:223-225`。

契约：`spec/FORMAT.md:3,24` 要求规范 POSIX 相对路径，glob 仅声明 `*`、`?`、整段 `**`。方括号并未被定义为 wildcard 或禁止字符；`tools/harness.py:136` 的 glob_match 自身也将方括号转义为字面量。

最小变更 A：基线 task.paths=["src/[id].tsx"]；不需要该待改文件存在，approved_paths 仍为 ["**"]。

实际：exit 1/invalid，E_PATH，path=$/paths，message="wildcard not allowed in file reference"。

最小变更 B：在临时根创建普通文件 `[policy].md`，将 rule.source 指向它，再 lint。

实际：exit 1/invalid，E_PATH，path=$/rules/0/source，同上消息。

预期：这些是合法字面路径，应正常 lint/resolve；`src/[id].tsx` 是常见动态路由文件名，不能要求用户改动其既有工程布局。实际含 `*`/`?` 的文件引用仍应拒绝，目录穿越和根逃逸检查仍应保留。

影响：动态路由工程及括号命名的证据/规则文件无法采用通用 Harness。它是误拒绝，不是根逃逸。

正反向实跑：普通 `src/a.txt` 基线 resolve exit 0；普通存在的 policy.md 基线正常；`../escape` 仍 exit 1/E_PATH。

## 3. P2：JSON 转义孤立代理项触发未捕获 UnicodeEncodeError，CLI 不返回规定 JSON

位置：`tools/harness.py:30-34` 接受 JSON 转义；`tools/harness.py:36-37` 对 ensure_ascii=False 序列化结果直接 UTF-8 encode；经 `tools/harness.py:230-236`/`tools/harness.py:281` 调用；`tools/harness.py:381-385` 仅捕获 Invalid 和 OSError。

最小变更：基线 task.change_id 设为 `chr(0xd800)`，用标准库 `json.dumps(task)` 默认 ensure_ascii=True 写入 UTF-8 临时 task.json。文件字节只含 ASCII 转义 `"\ud800"`；不存在非法 UTF-8 原始字节。

实际：输入被 read_json/schema 接受，resolve 在 routing digest 阶段抛出未捕获的 `UnicodeEncodeError`：`'utf-8' codec can't encode character '\ud800' in position 944: surrogates not allowed`。本次位置 944 随字段内容变化。调用 h.main 的外层探针准确捕获此异常，h.main 自身没有生成 JSON 结果。正常独立 CLI 将传播 traceback 并非约定 JSON 错误。

预期：明确拒绝非 Unicode scalar 输入并输出 schema_version/status/errors、exit 1，或在既定字符规范下稳定处理该字符串；不可让编码异常逃出 CLI。`spec/FORMAT.md:12` 明确除 argparse help 外输出均为 JSON，意外运行错误也有 exit 3 契约。

影响：不可信机器输入可破坏调用方依赖的结构化错误协议；这不是命令执行、越界读写或证据误 pass。不要因为此例全拒绝合法非 ASCII 字符。

## 最小公共夹具与运行方法

所有上述反例已使用 Python 3.11.9、标准库、TemporaryDirectory 临时合成根实跑。以下建立等价单规则正向基线；从仓库根执行，之后对内存 m/t 作各条最小变更，重新写 JSON，调用同一 CLI 即可。它不复制或修改正式项目夹具。

```python
import sys, runpy, types, pathlib, tempfile, json, hashlib
sys.dont_write_bytecode = True
h = types.SimpleNamespace(**runpy.run_path(str(pathlib.Path.cwd() / 'tools/harness.py')))
tmp = tempfile.TemporaryDirectory(prefix='harness-review5-')
root = pathlib.Path(tmp.name)
(root / 'policy.md').write_text('synthetic policy', encoding='utf-8')
(root / 'artifact.txt').write_text('v1', encoding='utf-8')
scope = dict(actions=['edit'], paths=['**'], platforms=['*'], tasks=['*'], lifecycle=['*'], exclusions=[])
rule = dict(id='rule', revision=1, owner='owner', scope=scope, source='policy.md',
            statement='synthetic', enforcement='enforced', executor_refs=['exec'], evidence_refs=['check'], constraints=[])
route = dict(id='route', owner='owner',
             match=dict(tasks=['build'], paths=['src/**'], platforms=[], domains=[], effects=[], mode='all'),
             context_set=dict(required=['policy.md'], conditional=[]),
             rule_refs=['rule'], executor_refs=['exec'], evidence_refs=['check'])
m = dict(schema_version=1, project_id='review', owners=[dict(id='owner', contact='test', backup='backup')],
         executors=[dict(id='exec', version='1', kind='manual')], rules=[rule], routes=[route])
t = dict(schema_version=1, change_id='c1', tasks=['build'], paths=['src/a.txt'], platforms=['win'],
         domains=[], effects=[], actions=['edit'], lifecycle='dev', facts={}, approved_paths=['**'],
         source=dict(base_commit='a', commit='b', dirty_digest='0'*64),
         environment=dict(os='win', arch='x64', shell='pwsh', toolchain_digest='0'*64,
                          config_digest='0'*64, permissions_digest='0'*64, dependencies_digest='0'*64),
         target=dict(kind='fixture', id='synthetic-1', version='1', simulated=False),
         artifacts=[dict(path='artifact.txt', sha256=hashlib.sha256(b'v1').hexdigest())])
# 在此应用上文一条最小变更；每条都从独立基线开始。
(root / 'harness.json').write_text(json.dumps(m), encoding='utf-8')
(root / 'task.json').write_text(json.dumps(t), encoding='utf-8')
code = h.main(['resolve', '--root', str(root), '--task', 'task.json'])
print('exit=', code)
# source 方括号例改用：h.main(['lint', '--root', str(root)])
# 结束时 tmp.cleanup()；未创建 symlink，未绕过任何权限。
```

## 实际范围、正向控制与未实跑界限

已读：spec/FORMAT.md 全文；tools/harness.py 全文；全部五份 schemas（manifest 的后半结构由完整独立 route.schema 与前半内嵌 rule 对照）；docs/pr-boundaries.md、docs/test-boundaries.md；tests/test_harness.py 按路由、scope、证据、路径与只读用例按需阅读。没有宣称重跑整个正式测试套件。

定向执行：普通单规则 resolve exit 0；同一夹具合成完整 pass envelope，evidence exit 0/current_status=pass（仅一致性正向控制，非真实产品执行认证）；OR 双向与 platform 负向；方括号 task/source；schema_version=1.0（当前 exit 1/E_CONST，仅记 JSON Schema 数值互操作限制，未列高价值发现）；孤立代理项；历史 artifact 改字节/缺失；路径穿越控制。

历史 artifact：当前 task 指向更新后的真实 artifact/hash，历史记录仍引用旧 hash 时，evidence exit 1/E_ARTIFACT_DIGEST；历史记录文件缺失时 exit 1/E_MISSING_FILE。两者发生在 freshness 降级之前，所以不会保留该条为 historical_status=pass/current_status=not-run。FORMAT:30 的历史降级描述与 artifact 当前必须存在/校验的要求存在读法张力；父会话已告知最终 INTEGRATION 明示其为 invalid exit 1。此报告按保守拒绝限制记录，不升级为误 pass 安全漏洞。

只读保证：探针在加载核心前设 sys.dont_write_bytecode=True，所有机器 JSON、普通 artifact 和页面仅写 TemporaryDirectory；核心最终一次运行前后 SHA-256 相同：baebb7aeb0f03177fda624e0a7ae8153c61cdbe49f8ca9521ac3ca8a846ed24c。未尝试 symlink（含权限绕行）、junction、FIFO/设备文件、硬链接竞态、并发替换或跨 OS 文件系统；静态读 safe 的 resolve/is_relative_to/is_file 链未发现新的静态越根或特殊文件读取证据，不能扩称这些边界已实跑通过。未认证离线声明 performed/目标/授权来源，属明示限制而非漏洞。

初次探针在自行构造孤立代理项的错误 encode/decode 语句处中断：UnicodeEncodeError，exit 1。已调查并改用 chr(0xd800)+json.dumps 的合法 ASCII 转义夹具，后续定向探针正常结束并确认核心同样存在上述独立异常；未将探针自身错误充当产品证据。

仓库身份：cwd=C:\c\Users\Rick\harness-template；git rev-parse HEAD 与 git status 均报告 `fatal: not a git repository (or any of the parent directories): .git`，因此没有可报告的 HEAD/working-tree diff。未清理既有文件；本报告为唯一正式文件写入。
