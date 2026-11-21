# Ram-AdminX 定向源码 Review（2026-11-17）

固定 HEAD `3a4fd98bb98030c67261a4973048c6ba133a828e`，真实tree `97e698b8d92beb4cfef3726b175f2afe6fc043d5`。原样6689 blob/file校验通过（BASELINE.json），API zipball快照非clone、不含历史；完整基线unpacked，整理后的本地补丁版clean-source，运行副本runtime。用户确认这是已获原作者授权的老开源二开；README/全部已有作者归属不删。README:9,427–429自称MIT，但tree未提供根LICENSE；不宣称所有依赖许可已尽调。

## 高优先发现与最小修复

### H1 已验证缺陷：BOSS可接管root账户（本地已修HTTP入口）

原HEAD `backend/apps/rbac/permissions.py:20,35–46`允许boss写；`views/user_views.py:77–100`任意pk更新/删除/重置；`services/user_service.py:92–146`无actor/目标角色边界，create/update可写role_ids。`models.py:55–59`与认证使用同一password_hash。合法BOSS Session+CSRF可POST `/api/rbac/users/{root_id}/reset-password/`。

**动态证据**：隔离临时SQLite、合成root/BOSS；`verify_security.py --baseline`返回HTTP200，authenticate用新密码成功（security-baseline.json）。非匿名攻击、未在公网攻击。

**局部修复**：runtime/clean-source四文件permissions.py、services/user_service.py、views/user_views.py、views/role_views.py：HTTP视图传actor；BOSS禁止管理superuser/root/boss账户，禁止授予/创建管理员角色；role定义写收紧为root，防相邻入口绕过；保留普通用户管理与root操作。27项动态回归PASS（security-patched.json），含reset/update/delete、管理员role_ids提升、普通用户拒绝、root成功、保护对象原密码/激活未变。PATCH.diff可复核。

**边界**：这是依赖HTTP权限层的BOSS护栏，不是service全局授权/默认拒绝；actor=None保留受信内部调用兼容，AI executor actor=None路径未覆盖。非全量权限审计。

### B1 已验证启动缺陷：README声称已修的4项TS错误仍在（已修）

原HEAD `frontend/src/layouts/MainLayout.vue:75`、`views/ai/AINotificationView.vue:50`导入不存在IconBell；`types/ai.ts:56–58`分析响应data与父接口冲突；`views/ai/AIApprovalView.vue:75`a-form缺必填model。原生npm run build实跑exit2。替换现有IconNotification、Omit父data、补现有form model后完整build exit0；保留大chunk warning。`views/login/LoginView.vue:42`补原生submit preventDefault，移除密码placeholder；真实登录与路由跳转通过。9个源码文件总diff，无业务重写。

## 未修风险/不适于生产的旧代码

- **中：Agent Token默认密钥/无撤销**。base.py:9,160–164固定开发SECRET_KEY复用Agent secret；ai/permissions.py:62–96验签与过期，不查issuer有效状态/撤销。默认部署可能离线伪造授权；权限仅approval submit，不等于绕root审批直接执行。未动态攻击Token。演示用随机分离密钥、AI_PROVIDERS=[]；不代表已修上游机制。
- **中：Agent审批审计归属**。ai/views/approval_views.py:43–57未把token root_user_id传入；ai/services/ai_approval.py:55–57,213–223用首root/首用户占位，不能可靠追踪真实issuer。独立review静态确认，未修。
- **部署误用风险而非独立已利用漏洞**。config/settings/dev.py:4,14–15开DEBUG和宽CORS；README:222–226公开默认口令，management/commands/init_rbac.py:28–30,45–46打印默认口令。不运行公开初始化命令；隔离合成账户、DEBUG=False、CORS/CSRF限loopback、随机key，仅127.0.0.1。不能公网部署这份旧后台。
- **已验证文档不一致**。README:19–21,297–305宣称普通操作审计API，但config/urls.py:5–12未注册/api/audit；apps/audit只有包init/apps（tree含目录共3条），缺model/view等。已认证GET /api/audit/logs/实际404（回归记录），不补写整模块。AI审计为不同模块，不混淆。
- **可重现性**。backend requirements范围宽无锁；frontend lock v3只registry.npmjs.org，npm ci ignore-scripts通过，未执行esbuild/fsevents生命周期；保留实际python-freeze与npm-ls。本次未运行npm lint（manifest声明eslint但未依赖），不宣称lint PASS。

## Review覆盖/验证边界

读README、ARCHITECTURE、manifest/lock、settings/manage/root urls、router/login、RBAC models/serializers/views/services/permissions、AI token/approval与网络边界；未发现项目AGENTS、Docker或env example。检索backend subprocess/os.system/eval/exec/FileField/request.FILES未命中；网络出口在AI urllib client和通知webhook，demo providers清空/webhook空，无业务凭据/模型联网。此检索不是任意命令执行不存在的证明。

真实Django+SQLite后端、Vue+Arco前端，AI仅项目原生mock；6图是真实运行页面不是自造样板。build/check/migrate、baseline漏洞复现、27项权限回归、真实浏览器登录/侧栏路由与390手机布局PASS。人工视觉NOT-RUN；真实Provider故障转移、生产部署、客户数据、全面渗透/依赖许可尽调均未做。无远端push、无模板站/全局memory/父Git改动。
