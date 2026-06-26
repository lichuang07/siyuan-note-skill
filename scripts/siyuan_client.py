"""
思源笔记 Python 客户端
======================
封装了思源笔记的常用 API，传入 api_token 即可操作。

用法:
    from siyuan_client import SiYuanClient

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

    # 搜索
    results = client.search("关键词")
"""

import requests
import json
from typing import Optional


class SiYuanClient:
    """思源笔记 API 客户端"""

    def __init__(self, token: str, base_url: str = "http://127.0.0.1:6806"):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

    def _post(self, endpoint: str, data: Optional[dict] = None, timeout: int = 10) -> dict:
        """发送 POST 请求"""
        url = f"{self.base_url}{endpoint}"
        r = requests.post(url, json=data or {}, headers=self.headers, timeout=timeout)
        try:
            return r.json()
        except Exception:
            return {"code": -1, "msg": r.text[:200], "raw": r}

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
        """获取所有笔记本列表"""
        resp = self._post("/api/notebook/lsNotebooks")
        return resp.get("data", {}).get("notebooks", [])

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
        全文搜索文档
        method: 0=关键字, 1=查询语法, 2=正则, 3=SQL
        """
        resp = self._post("/api/search/fullTextSearchBlock",
                          {"query": keyword, "method": method})
        return resp.get("data", {}).get("blocks", [])

    def sql(self, stmt: str) -> list[dict]:
        """执行 SQL 查询"""
        resp = self._post("/api/query/sql", {"stmt": stmt})
        return resp.get("data", [])

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
    # 演示：连接并打印 home 笔记本文档树
    TOKEN = "your_api_token_here"
    client = SiYuanClient(token=TOKEN)

    if client.ping():
        print(f"思源笔记 {client.get_version()} 连接成功\n")

        notebooks = client.list_notebooks()
        for nb in notebooks:
            print(f"📓 {nb['name']} ({nb['id']})")
            print(client.print_doc_tree(nb["id"]))
            print()
    else:
        print("连接失败，请检查 token 和思源笔记是否运行")
