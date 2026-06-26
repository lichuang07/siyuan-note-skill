# siyuan-note

Marvis 思源笔记操作技能，通过思源笔记 HTTP API 实现笔记的增删改查。

## 功能

| 功能 | 说明 |
|------|------|
| 笔记本浏览 | 列出所有笔记本、查看文档树结构 |
| 文档读写 | 导出 Markdown 内容、获取块 DOM |
| 块更新 | 更新指定块的内容（Markdown / DOM） |
| 全文搜索 | 关键字搜索、正则搜索、SQL 查询 |
| 文档管理 | 创建文档、追加块、删除块 |

## 安装

将本目录放置于 Marvis 技能目录下：

```
git clone https://github.com/<your-username>/siyuan-note.git ~/.marvis/skills/custom/siyuan-note/
```

或直接复制文件夹到 Marvis 技能目录：

```
C:\Users\<用户名>\AppData\Roaming\Tencent\Marvis\User\<ID>\skills\custom\siyuan-note\
```

Marvis 会自动识别并加载。

## 使用

在 Marvis 对话中说：

```
查看我的思源笔记 home 笔记本有哪些文档，token 是 xxxxx
```

```
搜索思源笔记中关于"数据库"的笔记
```

```
把网络架构文档中的拓扑图更新为包含 WSL 的版本
```

## 前置条件

- 思源笔记运行中，API 端口 (默认 6806) 可访问
- 提供 API Token（在思源笔记设置中生成）
- Python 3.8+，依赖 `requests`

## 文件结构

```
siyuan-note/
├── SKILL.md                  # 技能定义文件
├── meta.json                 # 元信息
├── README.md                 # 说明文档
└── scripts/
    └── siyuan_client.py      # Python API 客户端
```

## 许可证

MIT
