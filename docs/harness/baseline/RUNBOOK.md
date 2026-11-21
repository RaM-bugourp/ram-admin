# RUNBOOK — ram-admin 本地演示

固定源码：`unpacked/RaM-bugourp-ram-admin-3a4fd98`，HEAD `3a4fd98bb98030c67261a4973048c6ba133a828e`；这是 GitHub API zipball 固定HEAD快照，不是clone，不含历史。完整tree 6689/6689 blob SHA通过，tree SHA `97e698b8d92beb4cfef3726b175f2afe6fc043d5`，证据见 BASELINE.json。清洁整理副本 `clean-source` 只保留README/ARCHITECTURE/backend/frontend(src+manifest)/docs/changelog，不含node_modules/dist/db.sqlite3/密钥/账户/运行日志；PATCH.diff与PATCH.json记录runtime最小改动，不推送远端。

## 当前服务

- Backend：`http://127.0.0.1:8000`，Django dev settings覆写为 `local_demo_settings.py`（仅隔离runtime，不覆盖原源码）：loopback ALLOWED_HOSTS、DEBUG=False、CORS仅127.0.0.1:5173、CSRF同源、随机SECRET_KEY/AI_AGENT_TOKEN_SECRET、AI_PROVIDERS=[]、AI_MOCK_WHEN_NO_KEY=True。managed job `pwsh-b84e2b66b4de42e4`，保持运行；通过Harness工具停止：`job_kill({job_id:'pwsh-b84e2b66b4de42e4'})`（不是PowerShell的数字Job ID）。
- Frontend：`http://127.0.0.1:5173`，Vite job `pwsh-22a894f9f5c04e0e`，保持运行；通过Harness工具停止：`job_kill({job_id:'pwsh-22a894f9f5c04e0e'})`。启动命令增加命令级 `$env:CHOKIDAR_USEPOLLING='true'`，避免编辑器原子写临时文件触发Windows watcher EBUSY。
- 启动后端：在 `runtime/backend` 设置 `$env:DJANGO_SETTINGS_MODULE='local_demo_settings'`，用隔离venv `venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload`。
- 前端：在 `runtime/frontend` 设置命令级 `TEMP/TMP` 到 `.tmp`、`npm_config_cache` 到 `.npm-cache`，`node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort`。
- 数据：SQLite迁移成功，合成5用户/3角色；不得导入客户数据。AI仅原生本地mock边界，未联网调用任何模型，不能据此宣称Provider容灾已验。

## 验证记录

- `manage.py check` exit0；`manage.py migrate --noinput` exit0；`GET /api/auth/csrf/` HTTP200。
- `npm ci --ignore-scripts --no-audit --no-fund` exit0（95 packages）；`npm run build`最终exit0（TEMP/TMP隔离；大chunk warning保留）。原始未修runtime build实际TS exit2，最小修复后通过。
- `verify_security.py --baseline` exit0：BOSS对root reset HTTP200且新密码可认证；`verify_security.py` exit0：27项权限回归全PASS，证据 security-baseline.json/security-patched.json。补丁仅在runtime/local演示副本，未改远端/模板站。
- Playwright/Edge真实登录、/dashboard、/system/users、/system/roles、/ai/approval，390×844工作台截图；evidence/browser-QA.json exit0，console/request/http errors均空，人工视觉审查NOT-RUN。

## 未修/阻碍

原代码仍存在固定开发默认账户文档、默认key回落与Agent token无撤销/issuer状态校验；AI executor actor=None路径未覆盖，审批审计使用首root占位（静态确认）；开发配置不适合公网。BOSS护栏依赖HTTP permission层传入actor，服务actor=None兼容路径不是全局默认拒绝；未做生产部署、真实客户数据、真实Provider/模型、外网暴露、漏洞全量审计。

2026-11-17 19:08 Asia/Shanghai：会话异常中止后job_list为空且两端口不可连，确认原服务均已退出；未改已测源码/截图，仅用原命令恢复一次。新backend/frontend job如上，HTTP各200，仅127.0.0.1监听。历史已完成job结果已于中止前收集，部分任务尾日志无法再由job_output访问，以已落证据和历史工具结果为准。
