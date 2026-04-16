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
- 实践训练：`http://127.0.0.1:8000/practice/`
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

## 5. 配置本地环境变量（推荐）

本项目支持用项目根目录下的 `.env` 文件读取本地配置。

这一步不是必须的，但如果想启用“AI 对话体验”和“图像识别体验”的真实大模型能力，必须配置 Qwen API Key。

### 5.1 新建 `.env` 文件

项目根目录中已经提供了模板文件：`.env.example`

直接复制一份：

```powershell
copy .env.example .env
```

如果提示是否覆盖，输入 `N` 或按实际情况处理即可。

### 5.2 用记事本打开 `.env`

```powershell
notepad .env
```

### 5.3 至少需要关注这些字段

```env
DJANGO_SECRET_KEY=replace-with-a-secure-random-string
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DB_ENGINE=sqlite

QWEN_API_KEY=这里替换成自己的Qwen API Key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_CHAT_MODEL=qwen3.6-plus
QWEN_VL_MODEL=qwen3-vl-plus
QWEN_TIMEOUT=45
```

说明：

- `QWEN_API_KEY`：最关键，填自己的 key
- `QWEN_BASE_URL`：通常保持默认即可
- `QWEN_CHAT_MODEL`：用于 AI 对话体验
- `QWEN_VL_MODEL`：用于图像识别体验
- `QWEN_TIMEOUT`：接口超时时间，单位秒

### 5.4 重要提醒

- 不要把自己的 API Key 写进 `README.md`、代码文件或 Git 提交记录
- `.env` 已被 `.gitignore` 忽略，不会上传到 GitHub
- 即使不配置 Qwen，本项目也仍然可以运行，只是：
  - AI 对话页会走本地兜底回复
  - 图像识别页会只显示基础分析结果

### 5.5 如何判断 Qwen 配置成功

启动项目后访问：

- `http://127.0.0.1:8000/practice/dialogue/`
- `http://127.0.0.1:8000/practice/image/`

如果配置成功：

- AI 对话页会返回真实模型回复
- 图像识别页会出现“AI 识别结论”

如果配置失败：

- 页面仍能打开
- 系统会自动回退到本地演示模式，不会直接报错

---

## 6. 初始化数据库（第一次运行必做）

本项目默认数据库是 SQLite，不需要单独安装数据库软件。

```powershell
python manage.py migrate
```

成功后会在项目根目录生成（或更新）`db.sqlite3`。

---

## 7. 一键生成演示数据（强烈推荐）

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

### 7.1 默认演示账号

执行 `seed_demo_data` 后，可用账号：

- 教师：`demo_teacher`
- 学生：`demo_student`
- 管理员：`demo_admin`

默认密码：

- `DemoPass123!`

### 7.2 自定义密码（可选）

```powershell
python manage.py seed_demo_data --password "YourStrongPass123!"
```

### 7.3 跳过搜索索引重建（可选）

```powershell
python manage.py seed_demo_data --skip-search-index
```

---

## 8. 启动项目

```powershell
python manage.py runserver
```

看到类似输出即为启动成功：

```text
Starting development server at http://127.0.0.1:8000/
```

浏览器打开：

- `http://127.0.0.1:8000/`

### 8.1 如果 8000 端口被占用

```powershell
python manage.py runserver 8001
```

然后访问：

- `http://127.0.0.1:8001/`

---

## 9. 0 基础功能验收流程（照做即可）

按下面顺序点击，能通过则说明项目复现成功。

### 9.1 首页与导航

1. 打开首页。
2. 顶部导航能看到：首页、论坛、搜索、课程、测验、数据看板、后台管理。

### 9.2 登录

1. 打开 `http://127.0.0.1:8000/accounts/login/`
2. 用 `demo_student / DemoPass123!` 登录。
3. 进入账户中心，页面显示中文字段（用户名、邮箱、角色等）。

### 9.3 学生学习流程

1. 打开课程页：`/courses/`
2. 进入任意课程和课时。
3. 点击“标记为已完成”。
4. 在课时页点击“开始测验”，提交后应看到“测验结果”和“提交编号”。
5. 打开 `quiz/history/` 与 `quiz/wrong-questions/`，应看到历史与错题记录。

### 9.4 实践训练

1. 打开 `http://127.0.0.1:8000/practice/`
2. 点击“AI 智能对话体验”
3. 输入 `什么是人工智能？`
4. 如果已配置 Qwen API Key，应看到真实模型回复
5. 点击“图像识别体验”，上传一张图片
6. 页面应显示“基础分析”，若已配置 Qwen，还会显示“AI 识别结论”

### 9.5 论坛

1. 打开 `http://127.0.0.1:8000/forum/`
2. 发布帖子。
3. 进入帖子详情并发表评论。

### 9.6 搜索

1. 打开 `http://127.0.0.1:8000/search/`
2. 输入关键词（如 `Django`）。
3. 页面应返回课程/课时/论坛/题目的分区结果。

### 9.7 分析看板

1. 用 `demo_student` 访问 `http://127.0.0.1:8000/analytics/`，看到“个人概览”。
2. 退出后用 `demo_admin` 登录，访问同一地址，看到“平台概览”。

---

## 10. 管理端（可选）

如果需要 Django 原生后台：

```powershell
python manage.py createsuperuser
```

然后访问：

- `http://127.0.0.1:8000/admin/`

---

## 11. 质量检查命令

### 11.1 Django 配置检查

```powershell
python manage.py check
```

### 11.2 运行测试

```powershell
python manage.py test
```

如果看到 `OK`，说明测试通过。

### 11.3 重建搜索索引

```powershell
python manage.py rebuild_search_index
```

---

## 12. MySQL（可选，高阶）

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

## 13. 常见问题与解决

### 13.1 `conda activate learningwebsite` 失败

可能是 conda 初始化未完成，执行：

```powershell
conda init powershell
```

关闭并重新打开 PowerShell 后再试。

### 13.2 `pip install -r requirements.txt` 失败

先确认是否已激活环境：

```powershell
conda activate learningwebsite
```

再升级 pip 后重试：

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 13.3 `python manage.py migrate` 报错

先执行：

```powershell
python manage.py check
```

若是数据库文件权限问题，关闭占用 `db.sqlite3` 的程序后重试。

### 13.4 浏览器打不开 `127.0.0.1:8000`

检查是否已启动服务端：

```powershell
python manage.py runserver
```

若端口冲突改用：

```powershell
python manage.py runserver 8001
```

### 13.5 页面没有演示数据

重新执行：

```powershell
python manage.py seed_demo_data
python manage.py rebuild_search_index
```

---

### 13.6 AI 对话或图像识别没有真实模型效果

先检查：

```powershell
type .env
```

确认是否存在下面这些字段：

- `QWEN_API_KEY`
- `QWEN_BASE_URL`
- `QWEN_CHAT_MODEL`
- `QWEN_VL_MODEL`

如果刚修改过 `.env`，要先重启开发服务器：

```powershell
python manage.py runserver
```

如果仍不生效，优先检查：

- API Key 是否填写错误
- 当前网络是否可以访问 Qwen 接口
- 账号额度是否正常

---

## 14. 项目结构（简版）

- `config/`：Django 全局配置（settings、urls）
- `accounts/`：注册登录、个人资料
- `courses/`：课程、章节、课时、学习进度、内容工作台
- `quiz/`：题库、测验提交、错题本
- `forum/`：帖子、评论、置顶/已解决/状态管理
- `search/`：站内搜索与索引文档
- `analytics/`：学生/平台统计看板 + CSV 导出
- `core/`：首页、健康检查、演示数据命令
- `practice/`：语音识别、AI 对话、图像识别实践训练模块
- `templates/`：前端页面模板（当前为中文界面）
- `docs/`：答辩材料、演示脚本、讲稿

---

## 15. 答辩相关文档入口

- 演示流程：`docs/DEMO_WALKTHROUGH.md`
- 答辩总材料：`docs/DEFENSE_MATERIALS_CN.md`
- PPT 大纲：`docs/PPT_OUTLINE_CN.md`
- 逐页讲稿：`docs/PPT_SPEAKER_NOTES_CN.md`
- 截图执行清单：`docs/DEFENSE_SCREENSHOT_RUNBOOK_CN.md`

---

## 16. 一条命令版（给熟悉用户）

```powershell
conda create -n learningwebsite python=3.11 -y; conda activate learningwebsite; pip install -r requirements.txt; python manage.py migrate; python manage.py seed_demo_data; python manage.py runserver
```

如果是第一次复现，建议按前文分步骤执行，不要直接一条命令跑到底。
