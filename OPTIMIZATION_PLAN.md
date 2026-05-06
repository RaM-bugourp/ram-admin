# ram-admin 优化计划

## 一、当前问题诊断

### 1.1 结构问题
- [ ] packages/core 和 packages/libcore 内容重复
- [ ] packages/backend 目录存在但未使用
- [ ] 缺少 .env 环境配置支持
- [ ] 缺少 Docker 容器化配置

### 1.2 后端问题
- [ ] 缺少 API 文档（Swagger/OpenAPI）
- [ ] 缺少测试用例覆盖
- [ ] 缺少代码生成器
- [ ] settings.py 缺少生产环境配置分离
- [ ] 缺少缓存配置（Redis）
- [ ] 缺少异步任务支持（Celery）

### 1.3 前端问题
- [ ] 路由守卫逻辑复杂，可简化
- [ ] 缺少 TypeScript 支持
- [ ] 缺少组件库按需加载
- [ ] 缺少 Mock 数据支持
- [ ] 缺少 E2E 测试
- [ ] 缺少状态持久化（vuex-persistedstate）

### 1.4 文档问题
- [ ] 缺少 API 文档
- [ ] 缺少部署文档
- [ ] 缺少贡献指南详细说明

## 二、优化目标

### 2.1 首要目标：可运行 + 易二次开发
1. 清理冗余目录结构
2. 添加一键启动脚本
3. 添加环境配置支持
4. 添加 Docker 支持
5. 完善文档

### 2.2 次要目标：交互 + 运行效率
1. 前端组件按需加载
2. 路由懒加载优化
3. API 请求缓存
4. 列表虚拟滚动
5. 骨架屏加载

## 三、优化执行计划

### Phase 1: 结构清理（优先级：高）
1. 删除 packages/libcore 重复目录
2. 整理 packages 目录结构
3. 添加 .env.example 配置模板
4. 添加 Docker 配置

### Phase 2: 后端增强（优先级：高）
1. 添加 drf-spectacular（Swagger/OpenAPI）
2. 添加 pytest 测试用例
3. 添加代码生成器
4. 分离开发/生产配置

### Phase 3: 前端优化（优先级：中）
1. 简化路由守卫逻辑
2. 添加组件按需加载
3. 添加 vuex-persistedstate
4. 添加 Mock 支持

### Phase 4: 文档完善（优先级：中）
1. 完善 API 文档
2. 添加部署文档
3. 添加开发指南

## 四、参考项目

### 4.1 django-vue-adminx
- 代码生成器设计
- Docker 配置
- 丰富的业务模块参考

### 4.2 arco_admin_template
- 前端模板结构
- 组件封装方式

### 4.3 Django 最佳实践
- django-cookiecutter 项目结构
- drf-spectacular API 文档
- pytest-django 测试

### 4.4 Vue 最佳实践
- Vue 3 Composition API
- Vite 构建优化
- Arco Design 按需加载

## 五、执行进度

| Phase | 任务 | 状态 | 完成时间 |
|-------|------|------|----------|
| 1 | 结构清理 | 🔄 进行中 | - |
| 2 | 后端增强 | ⏳ 待开始 | - |
| 3 | 前端优化 | ⏳ 待开始 | - |
| 4 | 文档完善 | ⏳ 待开始 | - |
