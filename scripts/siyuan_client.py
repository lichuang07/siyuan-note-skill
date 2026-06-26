"""
思源笔记 Python 客户端 v1.1.0
==============================
封装了思源笔记的常用 API，支持 .env 配置、资源文件操作、排除过滤。

用法:
    # 方式一：从 .env 加载（推荐）
    client = SiYuanClient.from_env()

    # 方式二：手动传参
    client = SiYuanClient(token="your_token", base_url="http://127.0.0.1:6806")

    # 测试连接
    version = client.get_version()

    # 笔记本
    notebooks = client.list_notebooks()

    # 文档树
    tree = client.get_doc_tree(notebook_id)

    # 读取文档内容 (Markdown)
    md = client.export_markdown(doc_id)

    # 更新块
    client.update_block(block_id, "新内容")

    # 搜索（自动排除过滤）
    results = client.search("关键词")

    # 资源文件
    path = client.get_asset_path("block_id", "image.png")
"""

import os
import requests
import json
from pathlib import Path
from typing import Optional


def _load_env(env_path: Optional[str] = None) -> dict:
    """手动解析 .env 文件，无需 python-dotenv 依赖"""
    if env_path is None:
        # 查找当前目录及上级目录的 .env
        search_dir = Path(__file__).resolve().parent
        for _ in range(3):
            candidate = search_dir / ".env"
            if candidate.exists():
                env_path = str(candidate)
                break
            search_dir = search_dir.parent

    if env_path is None or not os.path.isfile(env_path):
        return {}

    config = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                config[key] = value
    return config


class SiYuanClient:
    """思源笔记 API 客户端"""

    def __init__(
        self,
        token: str,
        base_url: str = "http://127.0.0.1:6806",
        exclude_notebooks: Optional[list[str]] = None,
        exclude_paths: Optional[list[str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }
        self.exclude_notebooks = exclude_notebooks or []
        self.exclude_paths = exclude_paths or []

    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "SiYuanClient":
        """从 .env 文件加载配置并创建客户端"""
        config = _load_env(env_path)

        host = config.get("SIYUAN_HOST", "127.0.0.1")
        port = config.get("SIYUAN_PORT", "6806")
        token = config.get("SIYUAN_API_TOKEN", "")

        if not token:
            raise ValueError("未在 .env 中找到 SIYUAN_API_TOKEN，请先配置")

        exclude_notebooks = [
            n.strip() for n in config.get("SIYUAN_EXCLUDE_NOTEBOOKS", "").split(",") if n.strip()
        ]
        exclude_paths = [
            p.strip() for p in config.get("SIYUAN_EXCLUDE_PATHS", "").split(",") if p.strip()
        ]

        return cls(
            token=token,
            base_url=f"http://{host}:{port}",
            exclude_notebooks=exclude_notebooks,
            exclude_paths=exclude_paths,
        )

    def _post(self, endpoint: str, data: Optional[dict] = None, timeout: int = 10) -> dict:
        """发送 POST 请求"""
        url = f"{self.base_url}{endpoint}"
        r = requests.post(url, json=data or {}, headers=self.headers, timeout=timeout)
        try:
            return r.json()
        except Exception:
            return {"code": -1, "msg": r.text[:200], "raw": r}

    def _should_exclude(self, box: str = "", hpath: str = "") -> bool:
        """判断指定笔记本或路径是否应被排除"""
        if box and box in self.exclude_notebooks:
            return True
        if hpath and self.exclude_paths:
            for p in self.exclude_paths:
                if hpath == p or hpath.startswith(p + "/"):
                    return True
        return False

    def _filter_search_results(self, results: list[dict]) -> list[dict]:
        """从搜索结果中移除被排除的笔记本/路径"""
        if not self.exclude_notebooks and not self.exclude_paths:
            return results
        return [
            r for r in results
            if not self._should_exclude(
                box=r.get("box", ""),
                hpath=r.get("hpath", ""),
            )
        ]

    def _inject_exclude_clause(self, stmt: str) -> str:
        """在 SQL 查询的 WHERE 子句中注入排除条件"""
        if not self.exclude_notebooks and not self.exclude_paths:
            return stmt

        conditions = []
        for nb in self.exclude_notebooks:
            conditions.append(f"box != '{nb}'")
        for p in self.exclude_paths:
            conditions.append(f"hpath NOT LIKE '{p}%'")

        if not conditions:
            return stmt

        exclude_clause = " AND ".join(conditions)

        # 在 WHERE 之后注入
        stmt_upper = stmt.upper()
        if "WHERE" in stmt_upper:
            where_pos = stmt_upper.index("WHERE") + 5
            return stmt[:where_pos] + " " + exclude_clause + " AND" + stmt[where_pos:]
        else:
            # 没有 WHERE，在 FROM 之后添加
            for keyword in ["ORDER BY", "GROUP BY", "LIMIT", "HAVING"]:
                if keyword in stmt_upper:
                    pos = stmt_upper.index(keyword)
                    return stmt[:pos] + f" WHERE {exclude_clause} " + stmt[pos:]
            return stmt + f" WHERE {exclude_clause}"

    # ─── 系统 ───────────────────────────────────────

    def get_version(self) -> str:
        """获取思源笔记版本号"""
        resp = self._post("/api/system/version")
        return resp.get("data", "")

    def ping(self) -> bool:
        """测试连接是否正常"""
        try:
            resp = self._post("/api/system/version", timeout=3)
            return resp.get("code") == 0
        except Exception:
            return False

    # ─── 笔记本 ─────────────────────────────────────

    def list_notebooks(self) -> list[dict]:
        """获取所有笔记本列表（自动排除已配置的笔记本）"""
        resp = self._post("/api/notebook/lsNotebooks")
        notebooks = resp.get("data", {}).get("notebooks", [])
        if self.exclude_notebooks:
            notebooks = [n for n in notebooks if n["id"] not in self.exclude_notebooks]
        return notebooks

    def get_notebook(self, notebook_id: str) -> Optional[dict]:
        """获取指定笔记本信息"""
        notebooks = self.list_notebooks()
        for nb in notebooks:
            if nb["id"] == notebook_id:
                return nb
        return None

    def open_notebook(self, notebook_id: str) -> dict:
        """打开笔记本"""
        return self._post("/api/notebook/openNotebook", {"notebook": notebook_id})

    # ─── 文档 / 文件树 ──────────────────────────────

    def list_docs_by_path(self, notebook_id: str, path: str = "/") -> list[dict]:
        """获取指定路径下的文档列表（含名称和元信息）"""
        resp = self._post(
            "/api/filetree/listDocsByPath",
            {"notebook": notebook_id, "path": path},
        )
        return resp.get("data", {}).get("files", [])

    def get_doc_tree(self, notebook_id: str, path: str = "/") -> list[dict]:
        """获取文档树（含子文档嵌套结构，仅 ID）"""
        resp = self._post(
            "/api/filetree/listDocTree",
            {"notebook": notebook_id, "path": path},
        )
        return resp.get("data", {}).get("tree", [])

    # ─── 读取 ──────────────────────────────────────

    def export_markdown(self, doc_id: str) -> str:
        """导出文档为 Markdown 文本（含 YAML front matter）"""
        resp = self._post("/api/export/exportMdContent", {"id": doc_id})
        return resp.get("data", {}).get("content", "")

    def get_block_info(self, block_id: str) -> dict:
        """获取块的详细信息"""
        resp = self._post("/api/block/getBlockInfo", {"id": block_id})
        return resp.get("data", {})

    def get_block_dom(self, block_id: str) -> str:
        """获取块的 DOM 字符串"""
        resp = self._post("/api/block/getBlockDOM", {"id": block_id})
        return resp.get("data", {}).get("dom", "")

    def get_children(self, block_id: str) -> list[dict]:
        """获取块的子块列表"""
        resp = self._post("/api/block/getChildrenBlocks", {"id": block_id})
        return resp.get("data", [])

    # ─── 更新 ──────────────────────────────────────

    def update_block(self, block_id: str, data: str, data_type: str = "markdown") -> dict:
        """更新块内容（支持 markdown 和 dom）"""
        return self._post("/api/block/updateBlock", {
            "id": block_id,
            "dataType": data_type,
            "data": data,
        })

    def update_block_markdown(self, block_id: str, markdown: str) -> dict:
        """以 Markdown 格式更新块内容（便捷方法）"""
        return self.update_block(block_id, markdown, "markdown")

    # ─── 创建 ──────────────────────────────────────

    def create_doc(self, notebook_id: str, title: str, path: str = "/") -> dict:
        """在指定笔记本中创建新文档"""
        return self._post("/api/filetree/createDoc", {
            "notebook": notebook_id,
            "path": f"{path}/{title}",
        })

    def append_block(self, parent_id: str, markdown: str, data_type: str = "markdown") -> dict:
        """在父块下追加子块"""
        return self._post("/api/block/appendBlock", {
            "parentID": parent_id,
            "dataType": data_type,
            "data": markdown,
        })

    def prepend_block(self, parent_id: str, markdown: str, data_type: str = "markdown") -> dict:
        """在父块下前置插入子块"""
        return self._post("/api/block/prependBlock", {
            "parentID": parent_id,
            "dataType": data_type,
            "data": markdown,
        })

    # ─── 删除 ──────────────────────────────────────

    def delete_block(self, block_id: str) -> dict:
        """删除块"""
        return self._post("/api/block/deleteBlock", {"id": block_id})

    # ─── 搜索 ──────────────────────────────────────

    def search(self, keyword: str, method: int = 0) -> list[dict]:
        """
        全文搜索文档（自动排除已配置的笔记本/路径）
        method: 0=关键字, 1=查询语法, 2=正则, 3=SQL
        """
        resp = self._post("/api/search/fullTextSearchBlock",
                          {"query": keyword, "method": method})
        results = resp.get("data", {}).get("blocks", [])
        return self._filter_search_results(results)

    def sql(self, stmt: str) -> list[dict]:
        """执行 SQL 查询（自动注入排除条件）"""
        safe_stmt = self._inject_exclude_clause(stmt)
        resp = self._post("/api/query/sql", {"stmt": safe_stmt})
        return resp.get("data", [])

    def raw_sql(self, stmt: str) -> list[dict]:
        """执行原始 SQL 查询（不注入排除条件，用于需要精确控制的场景）"""
        resp = self._post("/api/query/sql", {"stmt": stmt})
        return resp.get("data", [])

    # ─── 资源文件 ──────────────────────────────────

    def get_asset_path(self, block_id: str, asset_name: str) -> Optional[str]:
        """
        获取资源文件（图片、附件等）的本地绝对路径。
        例如：get_asset_path("block_id", "image.png")
        返回：C:\Users\...\data\assets\image.png
        """
        resp = self._post("/api/asset/resolveAssetPath", {
            "id": block_id,
            "name": asset_name,
        })
        data = resp.get("data", {})
        return data.get("path") or data.get("localPath") or None

    def upload_asset(self, local_path: str) -> Optional[str]:
        """
        上传本地文件到思源笔记资源目录。
        返回资源文件的相对路径，如 assets/uploaded-image-xxx.png
        """
        if not os.path.isfile(local_path):
            return None

        filename = os.path.basename(local_path)

        # 读取文件内容并转为 data URI
        with open(local_path, "rb") as f:
            raw = f.read()

        import base64
        ext = os.path.splitext(filename)[1].lstrip(".").lower()
        mime_map = {
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml",
            "pdf": "application/pdf", "zip": "application/zip",
        }
        mime = mime_map.get(ext, "application/octet-stream")
        data_uri = f"data:{mime};base64,{base64.b64encode(raw).decode()}"

        resp = self._post("/api/asset/upload", {
            "assetsDirPath": "",
            "file": [data_uri],
        })
        data = resp.get("data", {})
        files = data.get("succMap", {})

        # 返回上传后的文件名路径
        for key in files:
            return f"assets/{key}"
        return None

    def list_assets(self, path: str = "") -> list[dict]:
        """列出资源目录下的文件"""
        resp = self._post("/api/asset/listAssetDir", {"path": path})
        return resp.get("data", [])

    def delete_asset(self, asset_path: str) -> dict:
        """删除资源文件"""
        return self._post("/api/asset/removeAsset", {"path": asset_path})

    # ─── 批量查询 ──────────────────────────────────

    def get_doc_name_map(self, notebook_id: str) -> dict[str, str]:
        """获取笔记本内所有文档 ID → 名称 的映射"""
        docs = self.sql(
            f"SELECT id, content FROM blocks "
            f"WHERE box = '{notebook_id}' AND type = 'd' "
            f"ORDER BY created DESC"
        )
        return {d["id"]: d.get("content", "") for d in docs if isinstance(d, dict)}

    # ─── 高级：获取完整文档树（带名称） ──────────────

    def get_annotated_doc_tree(self, notebook_id: str) -> list[dict]:
        """
        获取带名称的完整文档树。
        先拿 ID 树，再批量查名称，组装成带名称的树。
        """
        id_tree = self.get_doc_tree(notebook_id)
        name_map = self.get_doc_name_map(notebook_id)
        return self._annotate_tree(id_tree, name_map)

    def _annotate_tree(self, tree: list[dict], name_map: dict) -> list[dict]:
        """递归给文档树节点加上名称"""
        result = []
        for node in tree:
            item = {
                "id": node["id"],
                "name": name_map.get(node["id"], node["id"]),
            }
            if "children" in node:
                item["children"] = self._annotate_tree(node["children"], name_map)
            result.append(item)
        return result

    def print_doc_tree(self, notebook_id: str) -> str:
        """将带名称的文档树格式化为缩进文本"""
        tree = self.get_annotated_doc_tree(notebook_id)

        def _render(nodes: list[dict], indent: int = 0) -> list[str]:
            lines = []
            prefix = "│   " * indent
            for i, node in enumerate(nodes):
                is_last = (i == len(nodes) - 1)
                branch = "└── " if is_last else "├── "
                lines.append(f"{prefix}{branch}{node['name']}")
                if "children" in node:
                    lines.extend(_render(node["children"], indent + 1))
            return lines

        return "\n".join(_render(tree))


# ─── 快捷使用 ────────────────────────────────────────

if __name__ == "__main__":
    # 演示：从 .env 加载并打印 home 笔记本文档树
    try:
        client = SiYuanClient.from_env()
    except ValueError as e:
        print(f"配置错误：{e}")
        print("请先复制 .env.example 为 .env 并填入 SIYUAN_API_TOKEN")
        exit(1)

    if client.ping():
        print(f"思源笔记 {client.get_version()} 连接成功\n")

        notebooks = client.list_notebooks()
        for nb in notebooks:
            print(f"📓 {nb['name']} ({nb['id']})")
            print(client.print_doc_tree(nb["id"]))
            print()
    else:
        print("连接失败，请检查 token 和思源笔记是否运行")
