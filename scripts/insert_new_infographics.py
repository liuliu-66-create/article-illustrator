#!/usr/bin/env python3
"""
将生成的图片插入到飞书文档
1. 创建图片块
2. 上传图片素材
3. 更新图片块绑定素材
"""

import os
import json
import requests
from pathlib import Path

# 飞书配置
APP_ID = "cli_a95ca1da35f95cca"
APP_SECRET = "9CK0wKf6DI3UmJgEerk8gecLDZ4aBI4U"

# 工作空间
SKILL_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = SKILL_DIR / "workspace"
DOC_ID = "RhbudCW3qox4N8xKTMiccFfEnif"

# 图片文件 - 新生成的信息图
IMAGES = [
    ("skill功能介绍", "infographic_01.png", 3),  # 在第3个段落后插入
    ("五步流程", "infographic_02.png", 10),  # 在第10个段落后插入
    ("安装使用", "infographic_03.png", 36),  # 在第36个段落后插入
]

def get_access_token():
    """获取tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    else:
        raise Exception(f"获取token失败: {result}")

def get_document_blocks(access_token, doc_id):
    """获取文档所有块"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    all_blocks = []
    page_token = None
    
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        
        response = requests.get(url, headers=headers, params=params)
        result = response.json()
        
        if result.get("code") == 0:
            items = result.get("data", {}).get("items", [])
            all_blocks.extend(items)
            page_token = result.get("data", {}).get("page_token")
            if not page_token or not result.get("data", {}).get("has_more", False):
                break
        else:
            raise Exception(f"获取文档块失败: {result}")
    
    return all_blocks

def create_image_block(access_token, doc_id, parent_block_id, index=-1):
    """创建图片块"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{parent_block_id}/children"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "children": [
            {
                "block_type": 27,  # Image block
                "image": {}
            }
        ],
        "index": index
    }
    
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    
    if result.get("code") == 0:
        children = result.get("data", {}).get("children", [])
        if children:
            return children[0].get("block_id")
    else:
        print(f"创建图片块失败: {result}")
        return None

def upload_image_media(access_token, image_path, block_id):
    """上传图片素材到图片块"""
    url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    files = {
        "file": (Path(image_path).name, image_data, "image/png")
    }
    data = {
        "file_name": Path(image_path).name,
        "parent_type": "docx_image",
        "parent_node": block_id,
        "size": len(image_data)
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.post(url, headers=headers, files=files, data=data)
    result = response.json()
    
    if result.get("code") == 0:
        return result.get("data", {}).get("file_token")
    else:
        print(f"上传图片素材失败: {result}")
        return None

def update_image_block(access_token, doc_id, block_id, file_token):
    """更新图片块，绑定素材token"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/batch_update"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "requests": [
            {
                "block_id": block_id,
                "replace_image": {
                    "token": file_token
                }
            }
        ]
    }
    
    response = requests.patch(url, headers=headers, json=payload)
    result = response.json()
    
    if result.get("code") == 0:
        return True
    else:
        print(f"更新图片块失败: {result}")
        return False

def main():
    print("=" * 60)
    print("开始将信息图插入到飞书文档")
    print("=" * 60)
    
    # 获取token
    print("\n获取访问令牌...")
    access_token = get_access_token()
    print(f"✓ 获取成功")
    
    # 获取文档块
    print(f"\n获取文档结构...")
    blocks = get_document_blocks(access_token, DOC_ID)
    print(f"文档共 {len(blocks)} 个块")
    
    # 找到各段落对应的块ID
    text_blocks = []
    for i, block in enumerate(blocks):
        block_id = block.get("block_id", "")
        block_type = block.get("block_type", 0)
        text = ""
        if "paragraph" in block:
            para = block.get("paragraph", {})
            for elem in para.get("elements", []):
                if "text_run" in elem:
                    text += elem["text_run"].get("content", "")
        if text.strip():
            text_blocks.append((i, block_id, text.strip()[:50]))
    
    print(f"\n文本块列表:")
    for i, bid, txt in text_blocks:
        print(f"  {i}: [{bid}] {txt}")
    
    # 定义插入位置
    insert_positions = {
        3: ("skill功能介绍", "infographic_01.png"),
        8: ("五步流程", "infographic_02.png"),
        35: ("安装使用", "infographic_03.png"),
    }
    
    # 上传并插入每张图片
    for pos, (name, image_file) in insert_positions.items():
        image_path = WORKSPACE_DIR / image_file
        
        if not image_path.exists():
            print(f"\n✗ 图片不存在: {image_path}")
            continue
        
        # 获取插入点
        if pos < len(blocks):
            parent_block_id = blocks[pos].get("block_id", DOC_ID)
            print(f"\n处理: {name} ({image_file})")
            print(f"  插入位置: {pos}, parent_block_id: {parent_block_id}")
        else:
            parent_block_id = DOC_ID
            print(f"\n处理: {name} ({image_file})")
            print(f"  位置超出范围，使用根块")
        
        try:
            # 步骤1：创建图片块
            print(f"  步骤1: 创建图片块...")
            block_id = create_image_block(access_token, DOC_ID, parent_block_id)
            if not block_id:
                print(f"  ✗ 创建图片块失败")
                continue
            print(f"  ✓ 图片块已创建, block_id: {block_id}")
            
            # 步骤2：上传图片素材
            print(f"  步骤2: 上传图片素材...")
            file_token = upload_image_media(access_token, str(image_path), block_id)
            if not file_token:
                print(f"  ✗ 上传图片素材失败")
                continue
            print(f"  ✓ 图片素材已上传, file_token: {file_token}")
            
            # 步骤3：更新图片块
            print(f"  步骤3: 绑定素材到图片块...")
            if update_image_block(access_token, DOC_ID, block_id, file_token):
                print(f"  ✓ 素材已绑定到图片块")
                print(f"✓ {name} 插入成功!")
            else:
                print(f"  ✗ 绑定失败")
            
        except Exception as e:
            print(f"✗ 处理失败: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("图片插入完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
