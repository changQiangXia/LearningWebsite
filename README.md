# LearningWebsite（全 Python 毕设项目）

一个基于 Django 的学习平台示例项目，包含：账户系统、课程学习、在线测验、论坛、站内搜索、学习分析看板。

本 README 目标是：
即使没有计算机基础，也可以按步骤在本地完整跑起来。

---

## 0. 最终效果（先看这个）

完成后可以访问：

- 首页：`http://127.0.0.1:8000/`
- 账户：`http://127.0.0.1:8000/accounts/`
- 课程：`http://127.0.0.1:8000/courses/`
- 测验：`http://127.0.0.1:8000/quiz/`
- 论坛：`http://127.0.0.1:8000/forum/`
- 搜索：`http://127.0.0.1:8000/search/`
- 分析：`http://127.0.0.1:8000/analytics/`
- Django 后台：`http://127.0.0.1:8000/admin/`

---

## 1. 环境准备（必须）

### 1.1 需要安装的软件

- `Anaconda`（推荐）或 `Miniconda`
- Windows PowerShell（系统自带即可）

### 1.2 推荐 Python 版本

- `Python 3.11`

本项目默认用 conda 隔离环境：`learningwebsite`。

---

## 2. 获取项目代码

如果是从 GitHub 下载：

1. 下载 ZIP 并解压，或 `git clone`。
2. 打开 PowerShell。
3. `cd` 到项目根目录（即有 `manage.py` 的目录）。

示例：

```powershell
cd D:\pythonProjects\LearningWebsite
```

### 2.1 验证当前目录是否正确

执行：

```powershell
dir
```

应能看到这些关键文件/目录：

- `manage.py`
- `requirements.txt`
- `config/`
- `accounts/`
- `courses/`
- `quiz/`
- `forum/`
- `search/`
- `analytics/`
- `templates/`

---

## 3. 创建并激活隔离环境（Conda 工作流）

### 3.1 创建环境

```powershell
conda create -n learningwebsite python=3.11 -y
```

### 3.2 激活环境

```powershell
conda activate learningwebsite
```

### 3.3 确认 Python 来自该环境

```powershell
python --version
where python
```

你看到的路径应包含 `...\anaconda\envs\learningwebsite\`。

---

## 4. 安装依赖

```powershell
pip install -r requirements.txt
```

### 4.1 快速校验依赖是否完整

```powershell
pip check
```

如果输出 `No broken requirements found.`，说明依赖关系正常。

---

## 5. 初始化数据库（第一次运行必做）

本项目默认数据库是 SQLite，不需要单独安装数据库软件。

```powershell
python manage.py migrate
```

成功后会在项目根目录生成（或更新）`db.sqlite3`。

---

## 6. 一键生成演示数据（强烈推荐）

为了方便直接体验所有功能，建议执行：

```powershell
python manage.py seed_demo_data
```

该命令会创建：

- 演示用户
- 演示课程/章节/课时
- 测验题目与提交记录
- 论坛帖子
- 搜索索引

### 6.1 默认演示账号

执行 `seed_demo_data` 后，可用账号：

- 教师：`demo_teacher`
- 学生：`demo_student`
- 管理员：`demo_admin`

默认密码：

- `DemoPass123!`

### 6.2 自定义密码（可选）

```powershell
python manage.py seed_demo_data --password "YourStrongPass123!"
```

### 6.3 跳过搜索索引重建（可选）

```powershell
python manage.py seed_demo_data --skip-search-index
```

---

## 7. 启动项目

```powershell
python manage.py runserver
```

看到类似输出即为启动成功：

```text
Starting development server at http://127.0.0.1:8000/
```

浏览器打开：

- `http://127.0.0.1:8000/`

### 7.1 如果 8000 端口被占用

```powershell
python manage.py runserver 8001
```

然后访问：

- `http://127.0.0.1:8001/`

---

## 8. 0 基础功能验收流程（照做即可）

按下面顺序点击，能通过则说明项目复现成功。

### 8.1 首页与导航

1. 打开首页。
2. 顶部导航能看到：首页、论坛、搜索、课程、测验、数据看板、后台管理。

### 8.2 登录

1. 打开 `http://127.0.0.1:8000/accounts/login/`
2. 用 `demo_student / DemoPass123!` 登录。
3. 进入账户中心，页面显示中文字段（用户名、邮箱、角色等）。

### 8.3 学生学习流程

1. 打开课程页：`/courses/`
2. 进入任意课程和课时。
3. 点击“标记为已完成”。
4. 在课时页点击“开始测验”，提交后应看到“测验结果”和“提交编号”。
5. 打开 `quiz/history/` 与 `quiz/wrong-questions/`，应看到历史与错题记录。

### 8.4 论坛

1. 打开 `http://127.0.0.1:8000/forum/`
2. 发布帖子。
3. 进入帖子详情并发表评论。

### 8.5 搜索

1. 打开 `http://127.0.0.1:8000/search/`
2. 输入关键词（如 `Django`）。
3. 页面应返回课程/课时/论坛/题目的分区结果。

### 8.6 分析看板

1. 用 `demo_student` 访问 `http://127.0.0.1:8000/analytics/`，看到“个人概览”。
2. 退出后用 `demo_admin` 登录，访问同一地址，看到“平台概览”。

---

## 9. 管理端（可选）

如果需要 Django 原生后台：

```powershell
python manage.py createsuperuser
```

然后访问：

- `http://127.0.0.1:8000/admin/`

---

## 10. 质量检查命令

### 10.1 Django 配置检查

```powershell
python manage.py check
```

### 10.2 运行测试

```powershell
python manage.py test
```

如果看到 `OK`，说明测试通过。

### 10.3 重建搜索索引

```powershell
python manage.py rebuild_search_index
```

---

## 11. MySQL（可选，高阶）

默认不需要 MySQL；SQLite 已能完整运行项目。

如果要切换 MySQL，请先准备好 MySQL 服务和数据库，再在当前终端设置环境变量。

PowerShell 示例：

```powershell
$env:DB_ENGINE="mysql"
$env:DB_NAME="learningwebsite"
$env:DB_USER="root"
$env:DB_PASSWORD="你的密码"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"
```

然后执行：

```powershell
python manage.py migrate
python manage.py runserver
```

说明：

- 本项目 MySQL 驱动使用 `mysqlclient`。
- 目前默认推荐仍是 SQLite，最省心。

---

## 12. 常见问题与解决

### 12.1 `conda activate learningwebsite` 失败

可能是 conda 初始化未完成，执行：

```powershell
conda init powershell
```

关闭并重新打开 PowerShell 后再试。

### 12.2 `pip install -r requirements.txt` 失败

先确认是否已激活环境：

```powershell
conda activate learningwebsite
```

再升级 pip 后重试：

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 12.3 `python manage.py migrate` 报错

先执行：

```powershell
python manage.py check
```

若是数据库文件权限问题，关闭占用 `db.sqlite3` 的程序后重试。

### 12.4 浏览器打不开 `127.0.0.1:8000`

检查是否已启动服务端：

```powershell
python manage.py runserver
```

若端口冲突改用：

```powershell
python manage.py runserver 8001
```

### 12.5 页面没有演示数据

重新执行：

```powershell
python manage.py seed_demo_data
python manage.py rebuild_search_index
```

---

## 13. 项目结构（简版）

- `config/`：Django 全局配置（settings、urls）
- `accounts/`：注册登录、个人资料
- `courses/`：课程、章节、课时、学习进度、内容工作台
- `quiz/`：题库、测验提交、错题本
- `forum/`：帖子、评论、置顶/已解决/状态管理
- `search/`：站内搜索与索引文档
- `analytics/`：学生/平台统计看板 + CSV 导出
- `core/`：首页、健康检查、演示数据命令
- `templates/`：前端页面模板（当前为中文界面）
- `docs/`：答辩材料、演示脚本、讲稿

---

## 14. 答辩相关文档入口

- 演示流程：`docs/DEMO_WALKTHROUGH.md`
- 答辩总材料：`docs/DEFENSE_MATERIALS_CN.md`
- PPT 大纲：`docs/PPT_OUTLINE_CN.md`
- 逐页讲稿：`docs/PPT_SPEAKER_NOTES_CN.md`
- 截图执行清单：`docs/DEFENSE_SCREENSHOT_RUNBOOK_CN.md`

---

## 15. 一条命令版（给熟悉用户）

```powershell
conda create -n learningwebsite python=3.11 -y; conda activate learningwebsite; pip install -r requirements.txt; python manage.py migrate; python manage.py seed_demo_data; python manage.py runserver
```

如果是第一次复现，建议按前文分步骤执行，不要直接一条命令跑到底。
