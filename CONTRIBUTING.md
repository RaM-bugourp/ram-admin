# 贡献指南

感谢你考虑为 RaM Admin 做贡献！

---

## 一、如何贡献

### 1.1 报告 Bug

如果你发现了 Bug，请添加作者QQ：1963561552并提交你的发现，包含：

- 问题描述
- 复现步骤
- 期望行为
- 实际行为
- 环境信息（Python 版本、Node 版本、操作系统）

### 1.2 提出新功能

如果你有新功能的想法，请添加作者QQ：1963561552讨论

- 功能描述
- 使用场景
- 实现思路（可选）

### 1.3 提交代码

```bash
# 1. Fork 仓库
# 2. 克隆你的 Fork
git clone https://github.com/your-username/ram-admin.git

# 3. 创建分支
git checkout -b feature/your-feature

# 4. 编写代码
# ...

# 5. 运行测试
cd backend && pytest
cd frontend && npm test

# 6. 提交代码
git add .
git commit -m "feat: 添加新功能"

# 7. 推送到你的 Fork
git push origin feature/your-feature

# 8. 创建 Pull Request
```

---

## 二、代码规范

### 2.1 Python 代码

- 遵循 [PEP 8](https://peps.python.org/pep-0008/)
- 使用 `black` 格式化
- 使用 `isort` 排序导入

```bash
pip install black isort
black backend/
isort backend/
```

### 2.2 JavaScript/Vue 代码

- 使用 `prettier` 格式化
- 使用 `eslint` 检查

```bash
npm install -D prettier eslint
npx prettier --write frontend/src/
npx eslint frontend/src/
```

### 2.3 提交信息

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
feat: 添加新功能
fix: 修复 Bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

示例：
```
feat(article): 添加文章批量删除功能
fix(rbac): 修复角色权限检查逻辑
docs: 更新部署文档
```

---

## 三、开发流程

### 3.1 环境设置

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 前端
cd frontend
npm install
```

### 3.2 运行测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

### 3.3 代码检查

```bash
# Python
black --check backend/
isort --check backend/
flake8 backend/

# JavaScript
npx eslint frontend/src/
```

---

## 四、Pull Request 规范

### 4.1 PR 标题

使用与提交信息相同的格式：
```
feat: 添加新功能
```

### 4.2 PR 描述

```markdown
## 变更内容
- 添加了 XXX 功能
- 修复了 YYY 问题

## 测试
- [ ] 添加了单元测试
- [ ] 手动测试通过

## 相关 Issue
Closes #123
```

### 4.3 代码审查

所有 PR 都需要至少一位维护者审查后才能合并。

---

## 五、文档贡献

### 5.1 文档位置

- `README.md` - 项目介绍
- `ARCHITECTURE.md` - 架构设计
- `docs/` - 详细文档

### 5.2 文档规范

- 使用中文编写
- 代码块指定语言
- 保持简洁清晰

---

## 六、行为准则

- 尊重所有贡献者
- 接受建设性批评
- 关注对项目最有利的事情

---

感谢你的贡献！🎉
