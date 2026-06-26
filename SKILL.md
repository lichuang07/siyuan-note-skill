---
name: siyuan-note
description: 通过思源笔记 HTTP API 完成笔记本浏览、文档树查看、文档读写、全文搜索、块更新等操作。适用于查看思源笔记内容、搜索笔记、更新文档块、管理笔记结构等场景。关键词：思源笔记、siyuan、记笔记、搜索笔记、查看笔记、更新笔记。
version: 1.0.0
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
---

# 思源笔记操作技能

通过思源笔记 HTTP API 完成笔记的增删改查操作。

## 使用场景

- 浏览笔记本目录和文档树结构
- 读取文档完整 Markdown 内容
- 更新文档中的块内容
- 全文搜索笔记内容
- 执行 SQL 查询获取结构化数据
- 创建新文档或追加块
- 删除文档或块

## 前置要求

用户必须提供思源笔记的 API Token。首次使用时，需验证 API 连接是否正常。

## 操作步骤

### 1. 获取 API Token

从用户输入中提取 `api_token`。如果用户未提供，必须询问用户获取。

### 2. 加载 Python 客户端

使用 `scripts/siyuan_client.py` 中的 `SiYuanClient` 类：

```python
import sys
sys.path.insert(0, "<skill_dir>/scripts")
from siyuan_client import SiYuanClient

client = SiYuanClient(token="<用户提供的token>", base_url="http://127.0.0.1:6806")
```

其中 `<skill_dir>` 替换为本 skill 目录的绝对路径。

### 3. 执行操作

按用户需求选择对应方法：

#### 连接验证
```python
version = client.get_version()    # 获取思源版本
ok = client.ping()                # 测试连接
```

#### 笔记本操作
```python
notebooks = client.list_notebooks()            # 所有笔记本列表
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

#### 全文搜索
```python
results = client.search("关键词", method=0)    # method: 0=关键字 1=语法 2=正则 3=SQL
```

#### SQL 查询
```python
rows = client.sql("SELECT id, content FROM blocks WHERE type='d' ORDER BY created DESC")
```

#### 创建与删除
```python
new_doc = client.create_doc(notebook_id, "文档标题")
client.append_block(parent_id, "内容")
client.delete_block(block_id)
```

### 4. 呈现结果

- 文档树使用 `print_doc_tree()` 结果直接展示
- 文档内容使用 Markdown 格式展示
- 搜索结果以表格形式呈现
- 操作结果简要说明成功或失败原因

## 依赖

- Python 3.8+
- requests 库

安装命令：`pip install requests`

## 输入示例

```
查看我的思源笔记 home 笔记本有哪些文档，token 是 xxxxx
搜索思源笔记中关于"数据库"的笔记
把网络架构文档中的拓扑图更新为包含 WSL 的版本
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
- 默认 API 地址为 `http://127.0.0.1:6806`，可通过 `base_url` 参数修改
- 不支持加密文档的读写
- 批量操作时控制频率，避免请求过快
