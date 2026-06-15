# AI 集成功能设计文档

> 为 ram-adminx 增加 AI 能力：智能统计、自动化工作、自然语言交互
> 
> 创建日期: 2026-06-09
> 状态: 设计中

---

## 1. 目标与场景

### 1.1 核心目标

将 AI 能力集成到后台管理系统，实现：
- 自然语言查询数据（替代手写 SQL）
- 智能数据分析与洞察生成
- 自动化报告生成
- 异常检测与告警

### 1.2 使用场景

| 场景 | 描述 | 优先级 |
|------|------|--------|
| 智能仪表盘 | AI 自动分析统计数据，生成洞察文字 | P0 |
| 自然语言查询 | "显示上周创建的用户" → 自动生成查询 | P0 |
| 自动报告 | 定期生成用户活跃度、角色分布报告 | P1 |
| 异常检测 | AI 分析登录日志，检测异常行为 | P1 |
| 智能建议 | 基于用户行为给出权限调整建议 | P2 |

---

## 2. 系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │AI Chat   │ │AI Report │ │AIInsights│ │审批看板   │ │
│  │(仅root)  │ │Generator │ │Card      │ │Approval  │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       └─────────────┼────────────┼─────────────┘       │
│                     ▼                                    │
│             Axios API Client                             │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS /api/ai/*
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Backend (Django + DRF)                      │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │              apps/ai/                            │     │
│  │                                                 │     │
│  │  permissions.py  ── RootOnlyAI 权限守卫           │     │
│  │                                                 │     │
│  │  views/                                         │     │
│  │    ├── chat_views.py         ← /api/ai/chat/    │     │
│  │    ├── analyze_views.py     ← /api/ai/analyze/  │     │
│  │    ├── report_views.py     ← /api/ai/report/   │     │
│  │    └── approval_views.py   ← /api/ai/approval/ │     │
│  │                                                 │     │
│  │  services/                                      │     │
│  │    ├── ai_service.py       ← 故障转移 + 多Provider │
│  │    ├── ai_failover.py      ← 熔断/切换/告警      │
│  │    ├── ai_approval.py      ← Agent 审批流       │
│  │    ├── ai_audit.py         ← 审计日志记录        │
│  │    ├── prompt_builder.py  ← Prompt 工程         │
│  │    └── data_formatter.py  ← 数据格式化           │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │      AIService (核心 ─ 多Provider + 故障转移)      │     │
│  │                                                 │     │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐        │     │
│  │  │OpenAI   │→→│DeepSeek │→→│QClaw    │  N+1   │     │
│  │  │(Primary)│  │(Backup) │  │(Fallback│  兜底   │     │
│  │  └────┬────┘  └────┬────┘  └────┬────┘        │     │
│  │       │            │            │               │     │
│  │       └── 任一失败 → 自动切换 → root 告警 ─┘     │     │
│  └────────────────────────────────────────────────┘     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │    AI Provider Pool      │
         │  OpenAI / DeepSeek / ...│
         └─────────────────────────┘
```

### 2.2 目录结构

```
ram-adminx/
├── backend/
│   └── apps/
│       └── ai/                          # AI 应用
│           ├── __init__.py
│           ├── apps.py
│           ├── models.py                 # AI 调用日志 / 审批记录
│           ├── services/
│           │   ├── __init__.py
│           │   ├── ai_service.py        # 多Provider + 故障转移
│           │   ├── ai_failover.py       # 熔断检测 / 自动切换 / root告警
│           │   ├── ai_approval.py       # Agent 审批流
│           │   ├── ai_audit.py          # 审计日志（谁调用/谁审批）
│           │   ├── prompt_builder.py    # Prompt 模板
│           │   └── data_formatter.py    # 数据脱敏
│           ├── serializers/
│           │   └── ai_serializers.py
│           ├── views/
│           │   ├── chat_views.py        # 对话
│           │   ├── analyze_views.py     # 分析
│           │   ├── report_views.py     # 报告
│           │   └── approval_views.py   # 审批管理
│           ├── urls.py
│           └── permissions.py          # RootOnlyAI 权限类
│
├── frontend/
│   └── src/
│       ├── api/modules/
│       │   └── ai.ts                    # AI API
│       ├── types/
│       │   └── ai.ts                    # AI 类型
│       ├── views/
│       │   └── ai/
│       │       ├── AIChatView.vue       # 对话（仅root）
│       │       └── AIApprovalView.vue   # 审批看板（仅root）
│       └── components/
│           └── AIInsightsCard.vue      # 洞察卡片
```

---

## 3. API 设计

### 3.1 AI 对话接口（仅 root）

```
POST /api/ai/chat/

Request:
{
    "messages": [
        {"role": "user", "content": "显示上周创建的用户"}
    ],
    "context": "dashboard",
    "stream": false,
    "agent_mode": false        // true=A**** 代发，需审批
}

Response:
{
    "reply": "...",
    "provider_used": "openai",     // 实际使用的 Provider
    "failover_triggered": false,    // 是否发生了故障转移
    "call_id": "uuid",              // 审计日志 ID
    "data": [...],
}
```

### 3.2 Agent 审批接口（仅 root）

```
# 提交 Agent 操作（需 root 审批）
POST /api/ai/approval/submit/
{
    "agent_id": "audit-bot",
    "operation": "create_user",
    "params": {"username": "test", "role_ids": [2]},
    "reason": "自动创建审计账号"
}
→ 201 { "approval_id": "uuid", "status": "pending" }

# root 审批列表
GET /api/ai/approval/?status=pending
→ 200 [ { "approval_id": "...", "agent_id": "...", "operation": "...", ... } ]

# root 审批（通过/拒绝）
POST /api/ai/approval/{id}/review/
{ "action": "approve", "root_user_id": 1, "comment": "同意" }
→ 200 { "status": "approved", "executed": true }

# 查询日志（谁调用/谁审批）
GET /api/ai/audit/?start_date=2026-06-01
→ 200 [ { "call_id": "...", "root_user": "admin", "agent_id": null, 
          "operation": "chat", "approved_by": null, "created_at": "..." } ]
```

---

## 4. 后端实现要点

### 4.1 多 Provider + 故障转移 (AIService)

```python
# apps/ai/services/ai_failover.py

import time
from dataclasses import dataclass
from enum import Enum

class ProviderStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"

@dataclass
class ProviderConfig:
    name: str           # 'openai' | 'deepseek' | 'qclaw'
    api_key: str
    base_url: str
    model: str
    timeout: int = 30

class CircuitBreaker:
    """熔断器：连续失败 N 次后自动切换 Provider"""
    def __init__(self, failure_threshold=3, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = None
        self.status = ProviderStatus.HEALTHY

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.status = ProviderStatus.FAILED

    def record_success(self):
        self.failures = 0
        self.status = ProviderStatus.HEALTHY

    def can_use(self) -> bool:
        if self.status == ProviderStatus.HEALTHY:
            return True
        if self.last_failure_time:
            elapsed = time.time() - self.last_failure_time
            if elapsed > self.recovery_timeout:
                self.status = ProviderStatus.DEGRADED
                return True
        return False


# apps/ai/services/ai_service.py

class AIService:
    """多 Provider 自动故障转移 AI 服务"""
    _providers: list[ProviderConfig] = []
    _breakers: dict[str, CircuitBreaker] = {}
    _current_index: int = 0

    @classmethod
    def load_providers(cls):
        """从环境变量加载 Provider 列表，按优先级排序"""
        cls._providers = [
            ProviderConfig(
                name='openai',
                api_key=os.environ['OPENAI_API_KEY'],
                base_url=os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
                model=os.environ.get('OPENAI_MODEL', 'gpt-4o'),
            ),
            ProviderConfig(
                name='deepseek',
                api_key=os.environ['DEEPSEEK_API_KEY'],
                base_url=os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
                model=os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat'),
            ),
            # 最后一个兜底 Provider（N+1 策略）
            ProviderConfig(
                name='qclaw',
                api_key=os.environ['QCLAW_API_KEY'],
                base_url=os.environ.get('QCLAW_BASE_URL', 'https://api.qclaw.ai/v1'),
                model=os.environ.get('QCLAW_MODEL', 'pool-deepseek-v4-pro'),
            ),
        ]
        for p in cls._providers:
            cls._breakers[p.name] = CircuitBreaker()

    @classmethod
    def chat(cls, messages: list) -> tuple[str, str, bool]:
        """
        返回: (response, provider_name, failover_triggered)
        自动尝试下一个 Provider，直到成功或全部失败
        """
        tried = []
        failover_triggered = False

        for i in range(len(cls._providers)):
            idx = (cls._current_index + i) % len(cls._providers)
            config = cls._providers[idx]
            breaker = cls._breakers[config.name]

            if not breaker.can_use():
                continue

            tried.append(config.name)
            try:
                response = cls._call_provider(config, messages)
                breaker.record_success()
                cls._current_index = idx  # 成功则切换基准
                return response, config.name, failover_triggered
            except Exception as e:
                breaker.record_failure()
                failover_triggered = True
                cls._alert_root(config.name, str(e))

        raise AIAllProvidersFailedError(f"所有 Provider 失败: {tried}")

    @classmethod
    def _call_provider(cls, config, messages):
        # 根据 config.name 实例化对应 Provider
        if config.name == 'openai':
            return OpenAIProvider(config).chat(messages)
        elif config.name == 'deepseek':
            return DeepSeekProvider(config).chat(messages)
        elif config.name == 'qclaw':
            return QClawProvider(config).chat(messages)

    @classmethod
    def _alert_root(cls, failed_provider: str, error: str):
        """Provider 失败时通知所有 root 用户"""
        from apps.rbac.models import User, Role
        # 查找所有 root 角色用户
        roots = User.objects.filter(
            roles__code='root', is_deleted=False
        ).distinct()
        for root in roots:
            # 发送站内通知（也可接入邮件/钉钉）
            NotificationService.send(
                user=root,
                title=f"⚠️ AI Provider 故障告警",
                message=f"Provider '{failed_provider}' 失败: {error}\n系统已自动切换备用 Provider。",
                level='error'
            )
```

### 4.2 Agent 审批流 (AIApproval)

```python
# apps/ai/services/ai_approval.py

class AIApprovalService:
    """
    Agent 操作两阶段审批：
    1. Agent 提交操作 → status=pending
    2. Root 审批通过 → 执行操作 → status=approved
       Root 审批拒绝 → status=rejected
    """

    def submit_operation(self, agent_id: str, operation: str,
                         params: dict, reason: str) -> AIApproval:
        """Agent 提交操作（Agent 自身不能执行写操作）"""
        return AIApproval.objects.create(
            agent_id=agent_id,
            operation=operation,
            params=params,
            reason=reason,
            status='pending',
        )

    def review(self, approval_id: int, root_user, action: str,
               comment: str = '') -> AIApproval:
        """Root 用户审批操作"""
        approval = AIApproval.objects.get(id=approval_id, status='pending')

        approval.approved_by = root_user
        approval.approved_at = timezone.now()
        approval.approver_comment = comment

        if action == 'approve':
            approval.status = 'approved'
            approval.save()
            # 自动执行操作
            self._execute_operation(approval)
        else:
            approval.status = 'rejected'
            approval.save()

        return approval

    def _execute_operation(self, approval: AIApproval):
        """执行已审批的 Agent 操作"""
        op_map = {
            'create_user': lambda p: UserService().create_user(**p['params']),
            'update_user': lambda p: UserService().update_user(**p['params']),
            'delete_user': lambda p: UserService().delete_user(p['params']['user_id']),
            'assign_roles': lambda p: UserService().assign_roles(**p['params']),
        }
        handler = op_map.get(approval.operation)
        if handler:
            handler(approval.params)
```

### 4.3 审计日志 (AIAudit)

```python
# apps/ai/services/ai_audit.py

class AIAuditService:
    """记录所有 AI 调用及审批操作的完整审计链"""

    def log_call(self, root_user, call_type: str, prompt: str,
                 response: str, provider: str,
                 failover_triggered: bool, call_id: str):
        AICallLog.objects.create(
            root_user=root_user,          # 谁调用
            agent_id=None,
            call_type=call_type,         # chat | analyze | report
            prompt=prompt,
            response=response[:5000],     # 截断防止过大
            provider_used=provider,
            failover_triggered=failover_triggered,
            call_id=call_id,
        )

    def log_agent_submission(self, agent_id: str, operation: str,
                             params: dict, approval_id: str):
        AICallLog.objects.create(
            root_user=None,
            agent_id=agent_id,            # Agent 代发
            call_type='agent_submission',
            prompt=f"{operation}: {params}",
            response='',
            call_id=approval_id,
        )

    def log_approval(self, root_user, approval_id: str,
                     action: str, comment: str):
        """记录 root 的审批动作"""
        AIApprovalLog.objects.create(
            root_user=root_user,          # 谁审批
            approval_id=approval_id,
            action=action,               # approve | reject
            comment=comment,
        )
```

---

## 5. 前端实现要点

### 5.1 AI 类型定义

```typescript
// src/types/ai.ts

export interface AIMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: string
}

export interface AIChatRequest {
  messages: AIMessage[]
  context?: string
  stream?: boolean
  agent_mode?: boolean  // Agent 代发需审批
}

export interface AIChatResponse {
  reply: string
  provider_used: string
  failover_triggered: boolean
  call_id: string
  data?: any[]
}

export interface AIApproval {
  id: number
  agent_id: string
  operation: string
  params: object
  reason: string
  status: 'pending' | 'approved' | 'rejected'
  submitted_at: string
  approved_by?: string
  approved_at?: string
}
```

### 5.2 Root 审批看板组件

```vue
<!-- src/views/ai/AIApprovalView.vue -->

<template>
  <a-card title="Agent 操作审批">
    <a-table :data="approvals" :loading="loading">
      <a-table-column title="Agent ID" data-index="agent_id" />
      <a-table-column title="操作" data-index="operation" />
      <a-table-column title="参数" data-index="params">
        <template #cell="{ record }">
          <code>{{ JSON.stringify(record.params) }}</code>
        </template>
      </a-table-column>
      <a-table-column title="原因" data-index="reason" />
      <a-table-column title="提交时间" data-index="submitted_at" />
      <a-table-column title="操作" :width="180">
        <template #cell="{ record }">
          <a-space>
            <a-button type="primary" size="small"
                      @click="handleApprove(record.id)">
              通过
            </a-button>
            <a-button type="outline" status="danger" size="small"
                      @click="handleReject(record.id)">
              拒绝
            </a-button>
          </a-space>
        </template>
      </a-table-column>
    </a-table>
  </a-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getApprovals, reviewApproval } from '@/api/modules/ai'
import { Message } from '@arco-design/web-vue'

const approvals = ref([])
const loading = ref(false)

onMounted(async () => {
  await loadApprovals()
})

async function loadApprovals() {
  loading.value = true
  const res = await getApprovals({ status: 'pending' })
  approvals.value = res.data
  loading.value = false
}

async function handleApprove(id: number) {
  await reviewApproval(id, 'approve', '同意')
  Message.success('已通过')
  await loadApprovals()
}

async function handleReject(id: number) {
  await reviewApproval(id, 'reject', '拒绝')
  Message.warning('已拒绝')
  await loadApprovals()
}
</script>
```

### 5.3 故障告警组件

```vue
<!-- src/components/AIProviderAlert.vue -->

<template>
  <a-alert v-if="showAlert" type="warning" closable>
    <template #title>⚠️ AI Provider 故障转移</template>
    {{ message }}
  </a-alert>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getProviderStatus } from '@/api/modules/ai'

const showAlert = ref(false)
const message = ref('')

onMounted(async () => {
  const status = await getProviderStatus()
  if (status.failover_triggered) {
    showAlert.value = true
    message.value = `当前使用备用 Provider: ${status.current_provider}`
  }
})
</script>
```

---

## 6. 环境变量配置

```bash
# .env (backend)

# === AI Provider 列表（按优先级排序，故障自动切换）===
# Provider 1（主用）
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# Provider 2（备用 1）
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Provider 3（备用 2 / 兜底 N+1）
QCLAW_API_KEY=xxx
QCLAW_BASE_URL=https://api.qclaw.ai/v1
QCLAW_MODEL=pool-deepseek-v4-pro

# === 故障转移配置 ===
AI_FAILOVER_FAILURE_THRESHOLD=3     # 连续失败 N 次触发切换
AI_FAILOVER_RECOVERY_TIMEOUT=60       # 恢复探测间隔（秒）
AI_FAILOVER_ALERT_CHANNEL=notification  # 告警方式: notification|email|webhook
AI_FAILOVER_ALERT_WEBHOOK=            # 告警 Webhook URL（可选）

# === 审批流配置 ===
AI_APPROVAL_ENABLED=true               # 是否启用 Agent 审批流
AI_APPROVAL_AUTO_EXECUTE=true          # root 审批通过后是否自动执行
AI_APPROVAL_TIMEOUT_HOURS=24          # pending 超时自动拒绝（0=不超时）

# === 调用限制 ===
AI_RATE_LIMIT_PER_ROOT=100             # 每 root 每天调用次数
AI_RATE_LIMIT_PER_AGENT=20             # 每 Agent 每天提交审批次数
AI_TIMEOUT=30                          # 单次调用超时（秒）

# === 审计 ===
AI_AUDIT_RETENTION_DAYS=90            # 审计日志保留天数（0=永久）
```

---

## 7. 安全与审计

### 7.1 权限模型

```
权限层级（从严到宽）:

  root ──────── 直接调用 AI（完全权限）
    │             所有操作自动记录审计日志
    │
    └─ Agent ── root 授权后拥有同等操作权限
                但所有写操作必须 root 审批
                Agent 只能提交，不能执行

  boss / user ─ 无 AI 调用权限（403）
```

```python
# apps/ai/permissions.py

class RootOnlyAI(BasePermission):
    """只有 root 角色可以调用 AI 接口"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.roles.filter(code='root').exists()


class AgentWithRootAuth(BasePermission):
    """Agent 请求需携带有效的 root 授权 Token"""
    def has_permission(self, request, view):
        agent_token = request.headers.get('X-Agent-Token')
        if not agent_token:
            return False
        # 验证 Token 是否由 root 签发
        return AgentTokenService.verify(agent_token)
```

### 7.2 审计数据模型

```python
# apps/ai/models.py

class AICallLog(BaseModel):
    """AI 调用日志 — 记录谁在什么时候调用了什么"""
    call_id = models.UUIDField(default=uuid.uuid4, unique=True)
    root_user = models.ForeignKey(
        'rbac.User', null=True, on_delete=models.SET_NULL,
        related_name='ai_calls'
    )           # 直接调用时记录 root 账户
    agent_id = models.CharField(max_length=100, null=True)
                # Agent 代发时记录 Agent ID
    call_type = models.CharField(max_length=50)
                # chat | analyze | report | agent_submission
    prompt = models.TextField()
    response = models.TextField()
    provider_used = models.CharField(max_length=50)
    failover_triggered = models.BooleanField(default=False)
    tokens_used = models.IntegerField(null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    ip_address = models.GenericIPAddressField(null=True)


class AIApproval(BaseModel):
    """Agent 操作审批记录"""
    agent_id = models.CharField(max_length=100)
    operation = models.CharField(max_length=100)
                # create_user | update_user | delete_user | assign_roles | ...
    params = models.JSONField()
    reason = models.TextField()
    status = models.CharField(max_length=20, default='pending')
                # pending | approved | rejected | timeout | executed
    approved_by = models.ForeignKey(
        'rbac.User', null=True, on_delete=models.SET_NULL,
        related_name='ai_approvals'
    )           # 哪个 root 审批的
    approved_at = models.DateTimeField(null=True)
    approver_comment = models.TextField(blank=True)
    executed_at = models.DateTimeField(null=True)


class AIApprovalLog(BaseModel):
    """审批操作日志 — 记录 root 的每次审批动作"""
    approval = models.ForeignKey(AIApproval, on_delete=models.CASCADE)
    root_user = models.ForeignKey('rbac.User', on_delete=models.CASCADE)
    action = models.CharField(max_length=20)
                # approve | reject
    comment = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True)
```

### 7.3 审计查询 API

```
GET /api/ai/audit/?start_date=2026-06-01&end_date=2026-06-09

Response:
[
    {
        "call_id": "uuid-1",
        "root_user": "admin",         // 哪个 root 调用
        "agent_id": null,            // 直接调用
        "call_type": "chat",
        "provider_used": "deepseek",  // 故障转移后用了备用
        "failover_triggered": true,
        "created_at": "2026-06-09 14:30:00"
    },
    {
        "call_id": "uuid-2",
        "root_user": null,
        "agent_id": "audit-bot",
        "call_type": "agent_submission",
        "approved_by": "admin",      // 哪个 root 审批
        "approved_at": "2026-06-09 15:00:00",
        "status": "executed",
        "created_at": "2026-06-09 14:55:00"
    }
]
```

### 7.4 数据安全

```python
# apps/ai/services/data_formatter.py

def sanitize_data(data: dict) -> dict:
    """移除敏感字段后再发给 AI"""
    sensitive_fields = [
        'password', 'password_hash', 'token', 'secret',
        'session_key', 'session_data',  # Django Session
        'api_key', 'csrf_token',
    ]

    def _sanitize(obj):
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()
                    if k not in sensitive_fields}
        elif isinstance(obj, list):
            return [_sanitize(item) for item in obj]
        return obj

    return _sanitize(data)
```

---

## 8. 实施计划

### Phase 1 (MVP) — 2-3 天

- [ ] 创建 `apps/ai/` 应用 + 模型（CallLog / Approval / ApprovalLog）
- [ ] 实现多 Provider 加载 + 熔断器（`CircuitBreaker`）
- [ ] 实现 `AIService` 故障转移（3 个 Provider 自动切换）
- [ ] 实现 `RootOnlyAI` 权限类
- [ ] 实现 `/api/ai/chat/` 接口
- [ ] 环境变量配置（3 个 Provider API Key）


### Phase 2 — 2-3 天

- [ ] 实现 `AIApprovalService` 审批流（submit → review → execute）
- [ ] 实现 `/api/ai/approval/submit/`、`/api/ai/approval/`、`/api/ai/approval/{id}/review/`
- [ ] 实现 `AIAuditService` 完整审计日志
- [ ] 实现 `/api/ai/audit/` 查询接口
- [ ] 实现 root 告警（`NotificationService`）
- [ ] 前端 AI 对话组件（仅 root 可见）


### Phase 3 — 2-3 天

- [ ] 前端审批看板（AIApprovalView.vue）
- [ ] 仪表盘 AI 洞察卡片
- [ ] `/api/ai/analyze/` 数据分析接口
- [ ] Agent Token 授权机制（root 为 Agent 签发 Token）
- [ ] Prompt 模板优化

### Phase 4 — 3-5 天

- [ ] 自然语言 → SQL 查询
- [ ] 异常检测算法
- [ ] 报告定时生成（Celery 定时任务）
- [ ] 审计日志导出（Excel / PDF）
- [ ] 告警接入钉钉/企业微信 Webhook

---

## 9. 技术选型建议

| 项目 | 推荐 | 理由 |
|------|------|------|
| AI Provider | **OpenAI** (主) + **DeepSeek** (备) + **QClaw** (兜底) | N+1 容灾，最小化单点故障 |
| 流式返回 | Server-Sent Events (SSE) | 比 WebSocket 轻量，适合对话场景 |
| 熔断器 | 自实现 `CircuitBreaker` | 轻量，无需引入额外依赖 |
| 告警 | 站内通知 + Webhook | 支持钉钉/企业微信/飞书 |
| 审批流 | 两阶段（pending → approved/rejected → executed） | root 知情所有 Agent 写操作 |

### 9.1 故障转移流程

```
请求 → Provider[0](OpenAI)
         │
         ├─ 成功 → 返回 + 重置熔断器 + failover_triggered=false
         │
         └─ 失败 → CircuitBreaker.failures += 1
                     │
                     ├─ 连续 ≥3 次失败
                     │    ↓
                     │  标记 FAILED + 通知所有 root
                     │  自动切换 Provider[1](DeepSeek)
                     │
                     └─ <3 次 → 仍尝试当前 Provider
```

### 9.2 Agent 授权流程

```
Agent 提交写操作
    ↓
RootOnlyAI 检查 → 无 root Token → 403
    ↓
Agent 携带 root 签发的 Token → RootOnlyAI 放行
    ↓
提交审批记录 (status=pending)
    ↓
Root 在审批看板查看 (Agent ID / 操作 / 参数 / 原因)
    ↓
Root 审批 → 拒绝 → status=rejected → Agent 收到通知
         → 通过 → status=approved → 自动执行 + 记录审计
```

### 9.3 审计链路

```
AICallLog:
  root 直接调用 → root_user=admin, agent_id=null
  Agent 代发    → root_user=null,  agent_id=audit-bot, approved_by=admin

AIApprovalLog:
  Root 每次审批动作独立记录（approve/reject + comment + IP + timestamp）

审计查询:
  GET /api/ai/audit/?start_date=...&end_date=...&root_user=...
  → 完整链路：谁调用 → 调了哪个 Provider → 是否故障转移 → Agent 操作谁审批
```

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AI API Key 泄露 | 财产损失、数据泄露 | 环境变量 + `.gitignore` + 审计日志 |
| 单个 Provider 宕机 | AI 服务不可用 | N+1 故障转移 + 熔断器自动切换 |
| 全部 Provider 宕机 | AI 功能完全不可用 | 降级为本地缓存/静态分析 + root 告警 |
| AI 响应时间过长 | 用户体验差 | `AI_TIMEOUT` 超时 + 熔断 + 前端 loading |
| AI 生成内容不准确 | 错误决策 | root 审核审批 + 只读洞察不自动执行 |
| 敏感数据发送给 AI | 数据泄露 | `sanitize_data()` 过滤 + 数据脱敏 |
| Agent 未授权操作 | 越权写入 | `X-Agent-Token` 验证 + 两阶段审批 + 审计链 |
| Root 账户被盗 | 系统完全失控 | IP 记录 + 异常登录检测 + 多 root 相互审计 |

---

## 11. 下一步

1. **提供 AI API Key**：OpenAI / DeepSeek / QClaw 至少两个
2. **确认 Agent 需要哪些写操作**：create_user / assign_roles / ... ？
3. **确认告警渠道**：站内通知 / 钉钉 / 企业微信？
4. **开始 Phase 1 编码**
