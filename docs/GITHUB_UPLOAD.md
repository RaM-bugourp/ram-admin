# GitHub 上传完整流程

## 一、准备工作

### 1.1 创建 .gitignore

```bash
# 在项目根目录创建 .gitignore
```

### 1.2 检查敏感文件

确保以下文件不会被提交：
- .env（环境配置，含密码）
- *.pem（证书文件）
- venv/（虚拟环境）
- node_modules/
- __pycache__/
- *.pyc
- db.sqlite3（开发数据库）

## 二、GitHub 仓库创建

### 2.1 在 GitHub 网站创建仓库

1. 登录 https://github.com
2. 点击右上角 "+" → "New repository"
3. 填写信息：
   - Repository name: `ram-admin`
   - Description: `企业级后台管理框架 | Django 5 + Vue 3 + Arco Design`
   - Public（开源）
   - ❌ 不要勾选 "Add a README"（我们已有）
   - ❌ 不要勾选 "Add .gitignore"（我们已有）
   - License: MIT（我们已有）
4. 点击 "Create repository"

### 2.2 记录仓库地址

```
https://github.com/你的用户名/ram-admin.git
```

## 三、本地 Git 配置

### 3.1 初始化 Git（如果还没有）

```bash
cd C:\Users\19635\Desktop\框架模板\ram-admin

# 初始化
git init

# 配置用户信息（如果还没配置）
git config user.name "你的名字"
git config user.email "你的邮箱"
```

### 3.2 创建 .gitignore

```bash
# Windows PowerShell
@"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
env/
.venv/
*.egg-info/
dist/
build/

# Django
*.log
local_settings.py
db.sqlite3
media/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
dist/

# IDE
.idea/
.vscode/
*.swp
*.swo

# 环境配置（敏感）
.env
.env.local
*.pem
*.key

# 系统文件
.DS_Store
Thumbs.db

# 测试覆盖率
htmlcov/
.coverage
.pytest_cache/

# 构建产物
*.egg
.eggs/
"@ | Out-File -FilePath .gitignore -Encoding utf8
```

### 3.3 添加所有文件

```bash
# 查看将要提交的文件
git status

# 添加所有文件
git add .

# 查看暂存区
git status
```

### 3.4 创建首次提交

```bash
git commit -m "feat: 初始化项目

- Django 5 + DRF 后端
- Vue 3 + Arco Design 前端
- RBAC 权限模型
- 动态路由
- API 文档（Swagger）
- Docker 支持
- 完整文档"
```

## 四、推送到 GitHub

### 4.1 添加远程仓库

```bash
# 替换为你的 GitHub 用户名
git remote add origin https://github.com/你的用户名/ram-admin.git

# 或使用 SSH（推荐）
git remote add origin git@github.com:你的用户名/ram-admin.git
```

### 4.2 推送代码

```bash
# 推送到 main 分支
git branch -M main
git push -u origin main
```

### 4.3 如果需要认证

**方式一：Personal Access Token（推荐）**

1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. 勾选 `repo` 权限
4. 复制 token
5. 推送时使用 token 作为密码

```bash
git push -u origin main
# Username: 你的用户名
# Password: ghp_xxxx（token）
```

**方式二：SSH Key**

```bash
# 生成 SSH Key
ssh-keygen -t ed25519 -C "你的邮箱"

# 查看公钥
cat ~/.ssh/id_ed25519.pub

# 复制公钥到 GitHub → Settings → SSH and GPG keys → New SSH key

# 测试连接
ssh -T git@github.com
```

## 五、后续维护

### 5.1 日常提交流程

```bash
# 1. 查看修改
git status
git diff

# 2. 添加修改
git add .

# 3. 提交
git commit -m "feat: 添加新功能"

# 4. 推送
git push
```

### 5.2 分支管理

```bash
# 创建功能分支
git checkout -b feature/新功能

# 开发完成后合并
git checkout main
git merge feature/新功能

# 推送
git push
```

### 5.3 版本发布

```bash
# 打标签
git tag v1.0.0
git push origin v1.0.0

# 在 GitHub 创建 Release
# Releases → Draft a new release
```

## 六、GitHub 配置优化

### 6.1 添加 Topics

在仓库页面添加标签：
- django
- vue
- admin
- dashboard
- rbac
- arco-design

### 6.2 添加徽章

在 README.md 顶部添加：

```markdown
![GitHub stars](https://img.shields.io/github/stars/你的用户名/ram-admin)
![GitHub forks](https://img.shields.io/github/forks/你的用户名/ram-admin)
![GitHub issues](https://img.shields.io/github/issues/你的用户名/ram-admin)
![GitHub license](https://img.shields.io/github/license/你的用户名/ram-admin)
```

### 6.3 启用 GitHub Pages（可选）

如果需要文档网站：
1. Settings → Pages
2. Source: main 分支
3. Folder: /docs

### 6.4 添加 CI/CD（推荐）

创建 `.github/workflows/ci.yml`：

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: |
          cd backend
          pip install -r requirements.txt
          pytest

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '22'
      - run: |
          cd frontend
          npm ci
          npm run build
```

## 七、常见问题

### Q1: 推送被拒绝

```bash
# 强制推送（慎用）
git push -f origin main

# 或先拉取再推送
git pull origin main --rebase
git push origin main
```

### Q2: 文件太大

```bash
# 使用 Git LFS
git lfs install
git lfs track "*.psd"
git add .gitattributes
```

### Q3: 敏感文件已提交

```bash
# 从历史中删除
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送
git push origin --force --all
```

## 八、检查清单

推送前确认：

- [ ] .gitignore 已创建
- [ ] .env 未包含在提交中
- [ ] venv/ 未包含在提交中
- [ ] node_modules/ 未包含在提交中
- [ ] db.sqlite3 未包含在提交中
- [ ] README.md 已更新
- [ ] LICENSE 已添加
- [ ] CONTRIBUTING.md 已添加
- [ ] 所有测试通过（pytest）
- [ ] 前端构建成功（npm run build）
