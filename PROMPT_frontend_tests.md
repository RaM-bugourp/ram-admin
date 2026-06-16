# Prompt: 为 ram-adminx 前端编写测试套件

> 将此 prompt 交给 Agent 执行，目标是为 Vue 3 + TypeScript 前端添加 Vitest 测试。

## 1. 环境准备

在 `frontend/` 目录下操作：

```bash
cd C:/Users/19635/Desktop/ram-adminx/frontend
```

安装测试依赖：

```bash
npm install -D vitest @vue/test-utils happy-dom
```

## 2. Vite 配置更新

编辑 `frontend/vite.config.ts`，在现有配置基础上添加 test 配置：

```typescript
/// <reference types="vitest" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: { '@': resolve(__dirname, 'src') },
    },
    server: {
        port: 5173,
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
            },
        },
    },
    build: {
        rollupOptions: {
            output: {
                manualChunks: {
                    vendor: ['vue', 'vue-router', 'vuex'],
                    arcoDesign: ['@arco-design/web-vue'],
                },
            },
        },
        chunkSizeWarningLimit: 500,
    },
    test: {
        // Vitest 配置
        environment: 'happy-dom',
        globals: true,
        include: ['src/**/*.{test,spec}.{ts,js}'],
        coverage: {
            provider: 'v8',
            include: ['src/**/*.{ts,vue}'],
            exclude: [
                'src/main.ts',
                'src/env.d.ts',
                'src/**/*.d.ts',
                'src/**/*.{test,spec}.ts',
            ],
        },
    },
})
```

同时更新 `frontend/tsconfig.json`，在 `compilerOptions` 中添加：

```json
{
  "compilerOptions": {
    "types": ["vitest/globals"]
  }
}
```

在 `frontend/package.json` 的 `scripts` 中添加测试命令：

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

## 3. 测试目录结构

创建以下目录结构：

```
frontend/src/
├── __tests__/
│   ├── setup.ts                  # 测试全局 setup（mock Vue Router、Vuex Store）
│   ├── stores/
│   │   ├── user.store.test.ts    # user store 单元测试
│   │   └── ai.store.test.ts      # ai store 单元测试
│   ├── api/
│   │   ├── client.test.ts        # Axios 拦截器测试
│   │   ├── auth.api.test.ts      # auth API 模块测试
│   │   ├── user.api.test.ts      # user API 模块测试
│   │   └── ai.api.test.ts        # ai API 模块测试
│   ├── router/
│   │   └── index.test.ts         # 导航守卫测试
│   ├── views/
│   │   ├── LoginView.test.ts     # 登录页组件测试
│   │   ├── DashboardView.test.ts # 仪表盘组件测试
│   │   ├── UserListView.test.ts  # 用户列表页组件测试
│   │   └── AIChatView.test.ts    # AI 对话页组件测试
│   └── components/
│       └── AIProviderAlert.test.ts # Provider 告警组件测试
```

## 4. 测试 Setup 文件

创建 `frontend/src/__tests__/setup.ts`：

```typescript
import { config } from '@vue/test-utils'

// Mock Vue Router
vi.mock('vue-router', () => ({
    useRouter: () => ({
        push: vi.fn(),
        replace: vi.fn(),
    }),
    useRoute: () => ({
        path: '/',
        meta: {},
    }),
    createRouter: vi.fn(),
    createWebHistory: vi.fn(),
}))

// Mock Vuex
vi.mock('vuex', () => ({
    useStore: () => ({
        state: {
            user: { currentUser: null, roles: [], permissions: [] },
            ai: { providerStatus: null, unreadNotifications: 0 },
        },
        getters: {},
        dispatch: vi.fn(),
        commit: vi.fn(),
    }),
}))

// Mock axios
vi.mock('axios', () => ({
    default: {
        create: vi.fn(() => ({
            get: vi.fn(),
            post: vi.fn(),
            put: vi.fn(),
            delete: vi.fn(),
            interceptors: {
                request: { use: vi.fn(), eject: vi.fn() },
                response: { use: vi.fn(), eject: vi.fn() },
            },
            defaults: {
                baseURL: '/api',
                headers: { common: {} },
            },
        })),
        get: vi.fn(),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
    },
}))

// 全局 stub Arco Design 组件
config.global.stubs = {
    'a-button': true,
    'a-table': true,
    'a-input': true,
    'a-form': true,
    'a-form-item': true,
    'a-card': true,
    'a-modal': true,
    'a-layout': true,
    'a-layout-sider': true,
    'a-layout-header': true,
    'a-layout-content': true,
    'a-menu': true,
    'a-menu-item': true,
    'a-badge': true,
    'a-statistic': true,
    'a-space': true,
    'a-tag': true,
    'a-select': true,
    'a-switch': true,
    'a-popconfirm': true,
    'a-alert': true,
    'a-spin': true,
    'a-empty': true,
    'a-typography-title': true,
    'a-typography-text': true,
}
```

## 5. 各测试文件内容

### 5.1 `frontend/src/__tests__/stores/user.store.test.ts`

测试目标（直接测试 user store 的 mutations 和 actions）：

**test_initial_state**:
- Store 初始状态：`currentUser == null`, `roles == []`, `permissions == []`

**test_set_user_mutation**:
- 调用 `SET_USER` → `state.currentUser` 更新

**test_set_roles_mutation**:
- 调用 `SET_ROLES` → `state.roles` 更新

**test_clear_mutation**:
- 调用 `CLEAR` → 所有字段重置为初始值

**test_is_authenticated_getter**:
- `currentUser` 非 null → `isAuthenticated == true`

**test_is_admin_getter**:
- roles 包含 root 或 boss → `isAdmin == true`

**test_is_root_getter**:
- roles 包含 root → `isRoot == true`

**test_login_action_success**:
- `login()` 成功后 → `SET_USER` + `SET_ROLES` 被调用

**test_logout_action**:
- `logout()` → `CLEAR` 被调用

### 5.2 `frontend/src/__tests__/stores/ai.store.test.ts`

测试目标：

**test_initial_state**:
- `providerStatus == null`, `unreadNotifications == 0`, `providerStatusLoaded == false`

**test_set_provider_status**:
- `SET_PROVIDER_STATUS` → `state.providerStatus` 更新

**test_is_failover_active_getter**:
- provider 有 failed/degraded 状态 → `isFailoverActive == true`

**test_is_mock_mode_getter**:
- provider 是 mock → `isMockMode == true`

**test_has_unread_getter**:
- `unreadNotifications > 0` → `hasUnread == true`

### 5.3 `frontend/src/__tests__/api/client.test.ts`

测试目标（测试 axios 拦截器逻辑）：

**test_response_interceptor_extracts_data**:
- 拦截器正确提取 `response.data`

**test_401_redirects_to_login**:
- 401 响应 → 调用 logout + 跳转 /login

**test_403_redirects_to_forbidden**:
- 403 响应且已登录 → 跳转 /403

### 5.4 `frontend/src/__tests__/router/index.test.ts`

测试目标（测试导航守卫）：

**test_redirect_to_login_if_unauthenticated**:
- 未登录用户访问任意页面（/dashboard）→ 重定向 /login

**test_allow_login_page**:
- 未登录用户访问 /login → 放行

**test_redirect_to_403_if_not_root**:
- 非 root 用户访问 /ai/chat（requireRoot=true）→ 重定向 /403

**test_allow_root_to_ai_pages**:
- root 用户访问 /ai/chat → 放行

### 5.5 `frontend/src/__tests__/views/LoginView.test.ts`

测试目标：

**test_renders_login_form**:
- LoginView 渲染登录表单（用户名输入框、密码输入框、登录按钮）

**test_successful_login_navigates_to_dashboard**:
- 模拟登录 API 成功 → router.push('/dashboard') 被调用

**test_failed_login_shows_error**:
- 模拟登录 API 失败 → 显示错误消息

### 5.6 `frontend/src/__tests__/views/DashboardView.test.ts`

测试目标：

**test_renders_stats_cards**:
- DashboardView 渲染统计卡片

**test_fetches_stats_on_mount**:
- onMounted 时调用 dashboard API

### 5.7 `frontend/src/__tests__/views/UserListView.test.ts`

测试目标：

**test_renders_user_table**:
- UserListView 渲染用户表格

**test_shows_role_tags**:
- 用户行显示角色标签

**test_admin_can_see_create_button**:
- isAdmin=true → 新建按钮可见

**test_normal_user_cannot_see_create_button**:
- isAdmin=false → 新建按钮不可见

### 5.8 `frontend/src/__tests__/components/AIProviderAlert.test.ts`

测试目标：

**test_hidden_when_all_healthy**:
- 所有 Provider healthy → 组件隐藏

**test_shows_when_failover_active**:
- 有 Provider failed → 显示告警横幅

**test_shows_when_mock_mode**:
- mock_mode=true → 显示"Mock 模式"提示

## 6. 执行与验证

```bash
cd C:/Users/19635/Desktop/ram-adminx/frontend

# 运行全部测试
npx vitest run

# 查看覆盖率
npx vitest run --coverage

# 监听模式开发测试
npx vitest
```

## 7. 验收标准

- [ ] 全部测试通过（`npx vitest run` 无 FAILED）
- [ ] 覆盖率 ≥ 70%（行覆盖率，排除 stubs/类型定义）
- [ ] Store 的所有 mutations + actions + getters 覆盖
- [ ] 路由守卫的三种状态（未登录/普通用户/root）全部覆盖
- [ ] 关键视图组件（Login/Dashboard/UserList）渲染测试通过
- [ ] API 拦截器的 401/403 处理逻辑覆盖
- [ ] Arco Design 组件使用 stub 避免真实 UI 渲染
