# TOKEN-001：可撤销 Agent Token 与当前签发人资格

- 原定位：baseline/REVIEW.md 未修Token；本期 PLAN P2–P3；版本0.2.0-harness.1。
- owner/执行：ram-harness-dev；review：lead委派ram-token-review；独立验收lead；联系为agent消息，替补lead。无人工签署。
- 阶段：规划完成、待实现，2026-11-18 Asia/Shanghai。授权来自用户本会话及lead确认；只改新根，排除原件/生产/远端/全局记忆。
- 源码：固定上游HEAD+净化146文件SHA，独立git无remote/commit；来源baseline/source-files.json。禁止使用父Git。
- 维度：fix/security/api/data/build/docs；Web API+SQLite+frontend消费者检查；本地源码/测试/新增schema。frontend存在true、DB存在true（实际源码）；未部署是授权界限，不是N/A证明。
- 目标：Python3.13.15/Django5.2.19/DRF3.18.3/SQLite3.53.1 Windows隔离临时库+APIClient；Vue/Node锁文件构建。配置test无provider/webhook、随机进程密钥、无监听端口。

## 必要上下文与冲突
已读冻结1.0.0 START-HERE/overview/adoption/routing/ownership/PR/test/evidence/lifecycle/capabilities及平台README/selection/web README/api-config/data/operations/frontend/verify；补读平台evidence与maintenance后开工。实际models/managers/permissions/serializers/agent_views/approval_views/service/settings/urls、旧27脚本/Review/PLAN已读。规则RAM-SCOPE/API/DATA/BUILD/DOC revision1；consumer frontend存在AIAgentTokenView.vue签发UI/API/types，旧消费字段保留，token_id附加，撤销API无新UI；已重路由并读组件。现无语义冲突；旧token失效是显式安全预发行契约，lead已要求写明，不伪装向后兼容。

## 小工作包、可观察AC与停止点
1. 先保留旧代码复现：旧token在issuer停用/撤role后仍verify成功、同秒重复，记录布尔与状态不写token。若未复现则先调查不改断言。
2. 新AgentCredential模型只存token SHA256、uuid句柄、issuer/agent/期限/撤销时间；独立0002，新增token随机不重复。显式32字符专用secret，缺失issue 503、verify拒绝，无默认回落。
3. 有效root签发，撤销root-only且CSRF；摘要allowlist、签名、expiry(now>=exp)、issuer当前DB资格并集检查；拒绝四段旧token、不存在、撤销/错签/非ASCII/过期。保留root session独立语义，不关闭CSRF，不把agent标成root用户。
4. 撤销幂等、单句柄粒度，其他issuer/agent token不受影响；DB故障拒绝不放行；无明文入表/日志。撤销完成后新鉴权拒绝，已在途请求不承诺取消。状态恢复可恢复未撤销凭证，已撤销不可恢复。
5. issuer停用/软删/硬删/失去superuser/root关联/关联软删/角色软删逐项负例；有效superuser无需root关联仍支持，停用superuser拒绝。submit只pending、token agent_id覆盖body伪造、不执行用户写操作；issue/revoke/list/review/chat/RBAC不扩大agent权限。
6. Django TestCase/真实SQLite+APIClient会话登录/CSRF、迁移空库/0001升级/重复/逆向前滚、旧27回归、typecheck/build。失败保留原始日志，修复后新run，不吞失败。

迁移/兼容/安全停用详PLAN第6节；测试入口DEVELOPMENT.md；执行结果写独立evidence run与REPORT.md。扩大审批/actor/UI/生产必须停报lead、重路由；没有明文token/secret/账号持久化。完整生产/浏览器E2E/远端门禁not-run，整体产品未PASS。

## 后续状态
最终状态与准确命令/退出码/测试数以 REPORT.md 和 latest.json 指向的不可覆盖run为准；本卡保留实施前计划，不把最终测试结果回填为伪造预先批准。
