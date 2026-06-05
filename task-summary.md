# RaM-AdminX 分层 Prompt 文档（v2.0 重构版）

**日期**：2026-06-04（原始）/ 2026-06-04（重构）
**目标**：以技术栈对齐 + 架构轻量化为原则重构开发 Prompt，AI 喂入即可逐层开发。

## v2.0 重构要点

| 重构维度 | v1.0 | v2.0 |
|---------|------|------|
| Django 版本 | 4.2 | 5.2 |
| 认证方式 | Bearer Token（矛盾） | Session 认证（统一） |
| 前端 UI 库 | Element Plus / Ant Design（待定） | Arco Design Vue（确定） |
| 状态管理 | Pinia | Vuex 4 |
| Repository 层 | ABC+Generic+DI（Java风格） | Django Manager（Django风格） |
| 跨领域调用 | 强制 Orchestrator | 允许 Service 间调用 |
| 错误处理 | 散落魔法字符串 | ErrorCode 枚举集中管理 |
| Token 存储 | localStorage vs sessionStorage（矛盾） | Session Cookie httpOnly |

## 文档清单（23 份）

### Backend（15 份）
| 编号 | 文档 | 对应原则 | 核心产出 |
|------|------|---------|---------|
| 01 | 项目初始化与配置 | 6/10 | Django 5.2 骨架、Session认证、四环境配置、JSON日志 |
| 02 | Model 层开发 | 1/3/7 | RBAC Model体系、BaseManager、索引策略、ER关系 |
| 03 | 数据访问层（Manager） | 1/3 | BaseManager 软删除过滤、查询方法封装、链式调用 |
| 04 | Service 层开发 | 1/3/7 | 业务逻辑、@transaction.atomic、ErrorCode 异常、Service间依赖 |
| 05 | Serializer 契约层 | 2/5 | Create/Update/Output 三类、版本管理、TS类型映射 |
| 06 | ViewSet 接口层 | 3/6 | REST API、统一响应 {data}/{error}、permission per action |
| 07 | 权限与安全 | 5/6 | RBAC权限类、Session安全配置、CORS精确控制 |
| 08 | 中间件 | 3/10 | RequestId/日志/耗时/限流中间件、顺序规范 |
| 09 | 审计与日志 | 10/7 | AuditLog模型、JSON日志、敏感脱敏、结构化记录 |
| 10 | 测试 | 8 | 测试金字塔70/20/10、unit/integration、conftest工厂 |
| 11 | 代码生成器 | 3/2 | Django command 生成 CRUD 脚手架 |
| 17 | 文件管理与存储 | 5/6 | 文件类型白名单、MIME检测、S3切换、鉴权访问 |
| 19 | 数据导出与报表 | 5/6 | ExportMixin流式CSV、权限独立、异步导出 |
| 20 | 错误码体系 | 5 | ErrorCode枚举、BusinessError、前后端统一映射 |
| 21 | 数据权限设计 | 6 | MPTT部门树、行级权限、字段级脱敏、与DRF组合 |
| 22 | 国际化方案 | — | Django i18n + vue-i18n、ErrorCode多语言 |

### Frontend（6 份）
| 编号 | 文档 | 核心产出 |
|------|------|---------|
| 12 | 前端基础架构 | Axios+CSRF封装、Vuex 4 Store、路由守卫、useRequest |
| 13 | API 层与 TypeScript 类型 | 从 Serializer 生成 TS、运行时校验、契约映射 |
| 14 | 页面与组件 | Arco Design列表页/表单模板、三态处理、useTable |
| 15 | 安全与优化 | XSS防护、Session认证安全、路由懒加载、Vite分包 |
| 18 | 动态路由与菜单管理 | Menu Model、菜单树API、import.meta.glob动态注册 |

### DevOps（2 份）
| 编号 | 文档 | 核心产出 |
|------|------|---------|
| 16 | 部署与 CI/CD | Docker Compose、Nginx、CI流水线、pre-commit、**迁移策略** |
| 23 | 可观测性与监控 | 健康检查、Sentry、慢请求告警、Flower |

## 每份文档的标准结构（六段式，不变）
1. 适用场景（什么时候用）
2. 关联原则（对应十诫中的哪几条）
3. 核心规则（3-5 条铁律）
4. 开发步骤（分步骤 + 完整代码模板）
5. 反模式（禁止做法 + 原因）
6. 自检清单（checkbox 验收）

## 关键设计决策
- **Django 5.2 + Session 认证**：与用户现有项目技术栈一致
- **Django Manager 替代 Repository**：减77%样板代码，Django原生风格
- **允许 Service 间调用**：Orchestrator 仅在 ≥4 Service 时使用
- **ErrorCode 枚举集中管理**：前后端统一错误码映射
- **动态路由方案**：数据库存菜单 → API返回树 → import.meta.glob动态注册
- **所有 Prompt 含可运行代码模板**，AI 只需填充业务逻辑
