---
name: siyuan-note
description: 通过思源笔记 HTTP API 完成笔记本浏览、文档树查看、文档读写、全文搜索、资源文件管理、块更新等操作。支持 .env 配置文件自动加载、排除/过滤指定笔记本和路径。适用于查看思源笔记内容、搜索笔记、更新文档块、管理笔记结构、上传和获取资源文件（图片/附件）等场景。关键词：思源笔记、siyuan、记笔记、搜索笔记、查看笔记、更新笔记、上传资源、获取资源文件。
version: 1.1.0
author: lichuang
trigger:
  - "思源笔记"
  - "siyuan"
  - "查看笔记"
  - "搜索笔记"
  - "更新笔记"
  - "记笔记"
  - "笔记本"
  - "文档树"
  - "上传资源"
  - "资源文件"
  - "获取资源"
---

# 思源笔记操作技能

通过思源笔记 HTTP API 完成笔记的增删改查操作，支持 .env 配置、资源文件管理和排除过滤。

## 使用场景

- 浏览笔记本目录和文档树结构
- 读取文档完整 Markdown 内容
- 更新文档中的块内容
- 全文搜索笔记内容（自动排除已配置的隐私笔记本/路径）
- 执行 SQL 查询获取结构化数据
- 创建新文档或追加块
- 删除文档或块
- 上传和管理资源文件（图片、附件等）
- 获取资源文件的本地绝对路径

## 前置要求

### 推荐方式：.env 配置文件

在项目根目录（或 skill 目录）创建 `.env` 文件：

```
SIYUAN_HOST=127.0.0.1
SIYUAN_PORT=6806
SIYUAN_API_TOKEN=your-token-here

# 可选：排除规则
SIYUAN_EXCLUDE_NOTEBOOKS=
SIYUAN_EXCLUDE_PATHS=
```

参见 `.env.example`。配置后直接使用 `SiYuanClient.from_env()` 初始化。

### 备选方式：手动传参

如果用户手动提供 token，使用构造函数传参方式初始化。

## 操作步骤

### 1. 加载 Python 客户端

使用 `scripts/siyuan_client.py` 中的 `SiYuanClient` 类：

**方式一：.env 自动加载（推荐）**
```python
import sys
sys.path.insert(0, "<skill_dir>/scripts")
from siyuan_client import SiYuanClient

client = SiYuanClient.from_env()
```

**方式二：手动传参**
```python
client = SiYuanClient(
    token="<用户提供的token>",
    base_url="http://127.0.0.1:6806",
    exclude_notebooks=["notebook_id_1"],  # 可选
    exclude_paths=["/daily note"],         # 可选
)
```

其中 `<skill_dir>` 替换为本 skill 目录的绝对路径。

### 2. 执行操作

按用户需求选择对应方法：

#### 连接验证
```python
version = client.get_version()    # 获取思源版本
ok = client.ping()                # 测试连接
```

#### 笔记本操作
```python
notebooks = client.list_notebooks()            # 所有笔记本列表（自动排除）
client.open_notebook(notebook_id)              # 打开笔记本
nb = client.get_notebook(notebook_id)          # 获取单个笔记本信息
```

#### 文档树浏览
```python
tree = client.get_annotated_doc_tree(nb_id)    # 带名称的文档树（列表）
text = client.print_doc_tree(nb_id)            # 文本格式的文档树（可直接展示）
docs = client.list_docs_by_path(nb_id, "/")    # 指定路径下的文档列表
```

#### 读取文档内容
```python
md = client.export_markdown(doc_id)            # 导出 Markdown（含 YAML front matter）
dom = client.get_block_dom(block_id)           # 获取块 DOM
info = client.get_block_info(block_id)         # 获取块元信息
children = client.get_children(block_id)       # 获取子块列表
```

#### 更新块内容
```python
client.update_block(block_id, "新内容")        # 默认 markdown 格式
client.update_block(block_id, "内容", "dom")   # DOM 格式
```

#### 全文搜索（自动排除过滤）
```python
results = client.search("关键词", method=0)    # method: 0=关键字 1=语法 2=正则 3=SQL
# 结果已自动排除 SIYUAN_EXCLUDE_NOTEBOOKS 和 SIYUAN_EXCLUDE_PATHS 中配置的内容
```

#### SQL 查询（自动注入排除条件）
```python
rows = client.sql("SELECT id, content FROM blocks WHERE type='d' ORDER BY created DESC")
# SQL 自动注入排除条件，无需手动添加 WHERE 子句

rows = client.raw_sql("SELECT id FROM blocks")  # 不注入排除条件（精确控制）
```

#### 资源文件操作
```python
# 获取资源文件本地路径
path = client.get_asset_path("block_id", "image.png")
# 返回: "C:\Users\...\data\assets\image.png"

# 上传本地文件到思源笔记
asset_path = client.upload_asset("D:/images/photo.png")
# 返回: "assets/photo-20260626120000.png"

# 列出资源目录文件
files = client.list_assets("assets/")

# 删除资源文件
client.delete_asset("assets/old-file.png")
```

#### 创建与删除
```python
new_doc = client.create_doc(notebook_id, "文档标题")
client.append_block(parent_id, "内容")
client.delete_block(block_id)
```

### 3. 呈现结果

- 文档树使用 `print_doc_tree()` 结果直接展示
- 文档内容使用 Markdown 格式展示
- 搜索结果以表格形式呈现
- 资源文件路径以绝对路径形式展示
- 操作结果简要说明成功或失败原因

## 排除过滤机制

`.env` 中配置以下字段后，所有搜索和 SQL 查询将自动过滤：

- `SIYUAN_EXCLUDE_NOTEBOOKS`：排除指定笔记本 ID，搜索和 SQL 查询都不会返回这些笔记本的结果
- `SIYUAN_EXCLUDE_PATHS`：排除指定路径及子路径下的文档（如 `/daily note` 会同时排除 `/daily note/2024-01-01`）

`raw_sql()` 方法不会注入排除条件，适用于需要精确控制的场景。

## 依赖

- Python 3.8+
- requests 库

安装命令：`pip install requests`

## 输入示例

```
查看我的思源笔记 home 笔记本有哪些文档，token 是 xxxxx
搜索思源笔记中关于"数据库"的笔记
把网络架构文档中的拓扑图更新为包含 WSL 的版本
把这张图片上传到思源笔记：D:\screenshots\diagram.png
帮我找到 block_id=xxx 的图片资源路径
```

## 输出示例

```
=== home 笔记本文档树 ===
├── homelab
│   ├── 网络管理
│   │   └── 网络架构
│   └── 数据库
│       └── PostgreSQL

共 2 个一级文档，5 个文档。
```

## 边界约束

- 仅操作思源笔记，不处理其他笔记软件
- 需要思源笔记正在运行且 API 端口可访问
- 默认 API 地址为 `http://127.0.0.1:6806`，可通过 `base_url` 参数修改或 `.env` 中 `SIYUAN_HOST`/`SIYUAN_PORT` 配置
- 不支持加密文档的读写
- 批量操作时控制频率，避免请求过快
