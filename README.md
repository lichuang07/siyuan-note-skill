# siyuan-note

Marvis 思源笔记操作技能，通过思源笔记 HTTP API 实现笔记的增删改查、资源文件管理和隐私过滤。

## 功能

| 功能 | 说明 |
|------|------|
| 笔记本浏览 | 列出所有笔记本、查看文档树结构 |
| 文档读写 | 导出 Markdown 内容、获取块 DOM |
| 块更新 | 更新指定块的内容（Markdown / DOM） |
| 全文搜索 | 关键字搜索、正则搜索、SQL 查询 |
| 文档管理 | 创建文档、追加块、删除块 |
| 资源文件 | 上传/下载/列出/删除笔记中的图片和附件 |
| 隐私过滤 | 按笔记本或路径排除，搜索和 SQL 自动过滤 |
| 零配置 | `.env` 文件一次配置，之后无需重复传 token |

## 安装

```bash
git clone https://github.com/lichuang07/siyuan-note-skill.git ~/.marvis/skills/custom/siyuan-note/
```

或直接复制文件夹到 Marvis 技能目录：

```
C:\Users\<用户名>\AppData\Roaming\Tencent\Marvis\User\<ID>\skills\custom\siyuan-note\
```

## 配置

复制 `.env.example` 为 `.env`，填入你的思源笔记配置：

```
SIYUAN_HOST=127.0.0.1
SIYUAN_PORT=6806
SIYUAN_API_TOKEN=你的API Token

# 可选：排除不想被搜索的笔记本/路径
SIYUAN_EXCLUDE_NOTEBOOKS=
SIYUAN_EXCLUDE_PATHS=/daily note,/个人日记
```

配置完成后，Marvis 对话中无需再手动提供 token。

## 使用

在 Marvis 对话中说：

```
查看我的思源笔记 home 笔记本有哪些文档
```

```
搜索思源笔记中关于"数据库"的笔记
```

```
把网络架构文档中的拓扑图更新为包含 WSL 的版本
```

```
把这张图片上传到思源笔记：D:\screenshots\diagram.png
```

```
找到 block_id=xxx 对应的图片本地路径
```

## 前置条件

- 思源笔记运行中，API 端口 (默认 6806) 可访问
- Python 3.8+，依赖 `requests`（`pip install requests`）
- 复制 `.env.example` 为 `.env` 并填入 API Token

## 文件结构

```
siyuan-note/
├── SKILL.md                  # 技能定义文件
├── meta.json                 # 元信息
├── README.md                 # 说明文档
├── .env.example              # 环境变量模板
└── scripts/
    └── siyuan_client.py      # Python API 客户端
```

## 许可证

MIT
