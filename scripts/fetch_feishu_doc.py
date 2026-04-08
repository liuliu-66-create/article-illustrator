#!/usr/bin/env python3
"""
飞书文档读取脚本。
通过飞书开放 API 读取文档内容，转换为 Markdown 格式。

Usage:
    python fetch_feishu_doc.py --url "https://www.feishu.cn/docx/xxxxx"
    python fetch_feishu_doc.py --url "https://www.feishu.cn/docx/xxxxx" --output article.md

Returns:
    Markdown 格式的文档内容
"""

import argparse
import base64
import io
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

import requests

# Windows 终端 UTF-8 输出
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 飞书 API 配置
FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"

# 从 SECRET.md 或环境变量获取凭证
# 尝试多个可能的路径
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

# 尝试向上查找 SECRET.md (最多3层)
SECRET_PATHS = []
current = SCRIPT_DIR
for _ in range(4):
    SECRET_PATHS.append(current / "SECRET.md")
    parent = current.parent
    if parent == current:  # 到达根目录
        break
    current = parent


def load_feishu_credentials() -> dict:
    """从 SECRET.md 加载飞书凭证"""
    # 尝试多个路径
    for secret_path in SECRET_PATHS:
        if secret_path.exists():
            content = secret_path.read_text(encoding="utf-8")
            # 解析飞书应用凭证部分，支持 Markdown 加粗格式 **key:** value
            app_id_match = re.search(r'\*\*app_id[：:]\*\*\s*([^\s\n]+)', content)
            app_secret_match = re.search(r'\*\*app_secret[：:]\*\*\s*([^\s\n]+)', content)
            
            # 也尝试非加粗格式
            if not app_id_match:
                app_id_match = re.search(r'app_id[：:]\s*([^\s\n]+)', content)
            if not app_secret_match:
                app_secret_match = re.search(r'app_secret[：:]\s*([^\s\n]+)', content)
            
            if app_id_match and app_secret_match:
                return {
                    "app_id": app_id_match.group(1).strip(),
                    "app_secret": app_secret_match.group(1).strip()
                }
    
    # 尝试从环境变量获取
    return {
        "app_id": os.environ.get("FEISHU_APP_ID", ""),
        "app_secret": os.environ.get("FEISHU_APP_SECRET", "")
    }


def get_access_token(credentials: dict) -> Optional[str]:
    """获取飞书 access_token"""
    url = f"{FEISHU_BASE_URL}/auth/v3/tenant_access_token/internal"
    
    payload = {
        "app_id": credentials["app_id"],
        "app_secret": credentials["app_secret"]
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=30)
        result = resp.json()
        
        if result.get("code") == 0:
            return result.get("tenant_access_token")
        else:
            print(f"Error: 获取 access_token 失败: {result.get('msg')}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Error: 请求 access_token 异常: {e}", file=sys.stderr)
        return None


def extract_doc_id(url: str) -> Optional[str]:
    """从飞书文档 URL 提取文档 ID"""
    # 支持格式:
    # https://www.feishu.cn/docx/xxxxx
    # https://.feishu.cn/docx/xxxxx
    # https://bytedance.larkoffice.com/docx/xxxxx
    patterns = [
        r'/docx/([a-zA-Z0-9]+)',
        r'/docs/([a-zA-Z0-9]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def fetch_document_content(doc_id: str, access_token: str) -> Optional[dict]:
    """获取文档内容"""
    url = f"{FEISHU_BASE_URL}/docx/v1/documents/{doc_id}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        result = resp.json()
        
        if result.get("code") == 0:
            return result.get("data", {})
        else:
            print(f"Error: 获取文档信息失败: {result.get('msg')}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Error: 请求文档信息异常: {e}", file=sys.stderr)
        return None


def fetch_document_blocks(doc_id: str, access_token: str) -> Optional[list]:
    """获取文档所有块内容"""
    url = f"{FEISHU_BASE_URL}/docx/v1/documents/{doc_id}/blocks"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    all_blocks = []
    page_token = None
    
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            result = resp.json()
            
            if result.get("code") == 0:
                items = result.get("data", {}).get("items", [])
                all_blocks.extend(items)
                
                # 检查是否有下一页
                page_token = result.get("data", {}).get("page_token")
                if not page_token or not result.get("data", {}).get("has_more", False):
                    break
            else:
                print(f"Error: 获取文档块失败: {result.get('msg')}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Error: 请求文档块异常: {e}", file=sys.stderr)
            return None
    
    return all_blocks


def block_to_markdown(block: dict, children: list = None) -> str:
    """将单个块转换为 Markdown 格式"""
    block_type = block.get("block_type", 0)
    block_id = block.get("block_id", "")
    
    # 获取文本内容
    text_content = ""
    elements = []
    
    # 从 text 字段获取文本
    if "text" in block:
        text_field = block["text"]
        if isinstance(text_field, dict):
            elements = text_field.get("elements", [])
        elif isinstance(text_field, list):
            elements = text_field
    
    # 从富文本格式获取
    if "rich_text" in block:
        elements = block["rich_text"].get("elements", [])
    
    # 解析元素
    for elem in elements:
        if "text" in elem:
            text = elem["text"].get("content", "")
            
            # 处理文本样式
            text_run = elem.get("text_run", {})
            if text_run.get("bold"):
                text = f"**{text}**"
            if text_run.get("italic"):
                text = f"*{text}*"
            if text_run.get("code"):
                text = f"`{text}`"
            if text_run.get("link"):
                url = text_run["link"].get("url", "#")
                text = f"[{text}]({url})"
            
            text_content += text
        elif "image" in elem:
            # 图片元素
            image_id = elem.get("image", {}).get("token", "")
            if image_id:
                text_content += f"\n![image](feishu_image:{image_id})\n"
    
    # 根据块类型处理
    result = ""
    
    # heading 类型 (1-3)
    if 1 <= block_type <= 3:
        level = block_type
        result = f"{'#' * level} {text_content}\n"
    # paragraph
    elif block_type == 0 or block_type == 2:
        if text_content.strip():
            result = text_content + "\n"
    # bullet
    elif block_type == 3:
        result = f"- {text_content}\n"
    # ordered_list
    elif block_type == 4:
        result = f"1. {text_content}\n"
    # code
    elif block_type == 5:
        language = block.get("code", {}).get("language", "")
        result = f"```{language}\n{text_content}\n```\n"
    # quote
    elif block_type == 6:
        result = f"> {text_content}\n"
    # divider
    elif block_type == 7:
        result = "---\n"
    # table
    elif block_type == 8:
        # 表格需要特殊处理
        pass
    # todo
    elif block_type == 9:
        checked = block.get("todo", {}).get("done", False)
        checkbox = "[x]" if checked else "[ ]"
        result = f"- {checkbox} {text_content}\n"
    
    # 处理子块
    if children:
        for child in children:
            child_md = block_to_markdown(child)
            if child_md:
                result += child_md
    
    return result


def convert_blocks_to_markdown(blocks: list, block_map: dict = None) -> str:
    """将所有块转换为 Markdown"""
    if not block_map:
        block_map = {b.get("block_id", ""): b for b in blocks}
    
    markdown_lines = []
    
    # 构建块树
    root_blocks = []
    children_map = {}
    
    for block in blocks:
        parent_id = block.get("parent_id", "")
        block_id = block.get("block_id", "")
        
        if parent_id not in children_map:
            children_map[parent_id] = []
        children_map[parent_id].append(block)
    
    # 递归处理块
    def process_block(block: dict, indent: int = 0) -> str:
        block_type = block.get("block_type", 0)
        block_id = block.get("block_id", "")
        children = children_map.get(block_id, [])
        
        # 处理自身
        md = block_to_markdown(block, children)
        return md
    
    # 找到根块
    for block in blocks:
        parent_id = block.get("parent_id", "")
        if not parent_id or parent_id not in block_map:
            md = process_block(block)
            if md:
                markdown_lines.append(md)
    
    return "\n".join(markdown_lines)


def fetch_feishu_doc(url: str, output_path: str = None) -> dict:
    """读取飞书文档并转换为 Markdown"""
    # 提取文档 ID
    doc_id = extract_doc_id(url)
    if not doc_id:
        return {"success": False, "error": "无法从 URL 提取文档 ID"}
    
    # 获取凭证
    credentials = load_feishu_credentials()
    if not credentials.get("app_id") or not credentials.get("app_secret"):
        return {"success": False, "error": "未配置飞书应用凭证，请在 SECRET.md 中配置 app_id 和 app_secret"}
    
    # 获取 access_token
    access_token = get_access_token(credentials)
    if not access_token:
        return {"success": False, "error": "获取 access_token 失败"}
    
    # 获取文档信息
    doc_info = fetch_document_content(doc_id, access_token)
    title = doc_info.get("title", "未命名文档") if doc_info else "未命名文档"
    
    # 获取文档块
    blocks = fetch_document_blocks(doc_id, access_token)
    if blocks is None:
        return {"success": False, "error": "获取文档内容失败"}
    
    # 转换为 Markdown
    markdown_content = f"# {title}\n\n"
    markdown_content += convert_blocks_to_markdown(blocks)
    
    # 输出结果
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        return {
            "success": True,
            "title": title,
            "output_path": output_path,
            "block_count": len(blocks)
        }
    else:
        # 输出到 stdout
        print(markdown_content)
        return {
            "success": True,
            "title": title,
            "block_count": len(blocks)
        }


def main():
    parser = argparse.ArgumentParser(description="飞书文档读取工具")
    parser.add_argument("--url", required=True, help="飞书文档链接")
    parser.add_argument("--output", help="输出 Markdown 文件路径（可选，不指定则输出到 stdout）")
    
    args = parser.parse_args()
    
    result = fetch_feishu_doc(args.url, args.output)
    
    if not result.get("success"):
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)
    else:
        if args.output:
            print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
