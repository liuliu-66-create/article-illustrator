#!/usr/bin/env python3
"""
飞书文档上传脚本。
将文章和配图上传到飞书云文档。

Usage:
    python upload_to_feishu.py --article article.md --images img1.png img2.png --output doc_url.txt
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import requests

# 添加 feishu_mcp 路径
FEISHU_SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skill_feishu_doc"
sys.path.insert(0, str(FEISHU_SKILL_DIR / "scripts"))

from feishu_mcp import get_tenant_access_token, FeishuMcpClient

WORKSPACE_DIR = Path(__file__).resolve().parent.parent / "workspace"


def upload_image_to_feishu(image_path: str, tat: str) -> str:
    """上传图片到飞书素材库，返回 file_token"""
    with open(image_path, "rb") as f:
        files = {"file": f}
        data = {"file_type": "stream", "file_name": Path(image_path).name}
        
        resp = requests.post(
            "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all",
            headers={"Authorization": f"Bearer {tat}"},
            files=files,
            data=data,
            timeout=120,
        )
        
    result = resp.json()
    if result.get("code") != 0:
        raise Exception(f"上传图片失败: {result}")
    
    return result["data"]["file_token"]


def create_doc_with_images(title: str, article_path: str, image_paths: List[str], folder_token: Optional[str] = None) -> dict:
    """创建飞书文档并插入图片"""
    
    # 设置环境变量
    app_id = "cli_a95ca1da35f95cca"
    app_secret = "9CK0wKf6DI3UmJgEerk8gecLDZ4aBI4U"
    os.environ["FEISHU_APP_ID_7619631245038764095"] = app_id
    os.environ["FEISHU_APP_SECRET_7619631245038764095"] = app_secret
    
    # 获取 access token
    tat = get_tenant_access_token()
    
    # 读取文章
    with open(article_path, "r", encoding="utf-8") as f:
        article_content = f.read()
    
    # 上传所有图片
    print("正在上传图片...")
    image_tokens = []
    for i, img_path in enumerate(image_paths):
        print(f"  上传图片 {i+1}/{len(image_paths)}: {Path(img_path).name}")
        token = upload_image_to_feishu(img_path, tat)
        image_tokens.append(token)
        print(f"    ✓ file_token: {token[:20]}...")
    
    # 分析文章结构，插入图片
    # 简单策略：将图片均匀插入到文章段落中
    paragraphs = article_content.split("\n\n")
    
    # 构建带图片的 Markdown
    markdown_parts = []
    img_index = 0
    
    for i, para in enumerate(paragraphs):
        markdown_parts.append(para)
        
        # 每隔几个段落插入一张图片
        if img_index < len(image_tokens) and i > 0 and i % 3 == 0:
            token = image_tokens[img_index]
            markdown_parts.append(f"\n![配图{img_index + 1}](file_token:{token})\n")
            img_index += 1
    
    # 如果还有剩余图片，加到末尾
    while img_index < len(image_tokens):
        token = image_tokens[img_index]
        markdown_parts.append(f"\n![配图{img_index + 1}](file_token:{token})\n")
        img_index += 1
    
    final_markdown = "\n\n".join(markdown_parts)
    
    # 创建飞书文档
    print("\n正在创建飞书文档...")
    
    client = FeishuMcpClient(use_tat=True)
    
    # 构建请求参数
    arguments = {
        "title": title,
        "markdown": final_markdown,
    }
    
    if folder_token:
        arguments["folder_token"] = folder_token
    
    result = client.call_tool("create-doc", arguments)
    
    print(f"✓ 文档创建成功！")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="上传文章和图片到飞书文档")
    parser.add_argument("--article", required=True, help="文章文件路径")
    parser.add_argument("--images", nargs="+", required=True, help="图片文件路径列表")
    parser.add_argument("--title", default="公众号文章", help="文档标题")
    parser.add_argument("--folder-token", help="飞书文件夹 token")
    parser.add_argument("--output", help="输出文件（保存文档 URL）")
    
    args = parser.parse_args()
    
    try:
        result = create_doc_with_images(
            title=args.title,
            article_path=args.article,
            image_paths=args.images,
            folder_token=args.folder_token,
        )
        
        # 输出结果
        print(f"\n文档链接: {result.get('doc_url', 'N/A')}")
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        
        return 0
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
