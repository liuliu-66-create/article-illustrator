#!/usr/bin/env python3
"""
将生成的图片插入到飞书文档 - 正确的API流程
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

# 图片文件
IMAGES = [
    ("skill-vetter", "infographic_final_01.png"),
    ("markdown-proxy", "infographic_final_02.png"),
    ("follow-builders", "infographic_final_03.png"),
    ("skill-creator", "infographic_final_04.png"),
    ("superpowers", "infographic_final_05.png"),
    ("agent-browser", "infographic_final_06.png"),
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

def create_image_block(access_token, doc_id, parent_block_id=None):
    """创建图片块"""
    # 使用文档根块创建子块
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    
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
        "index": -1
    }
    
    print(f"请求URL: {url}")
    print(f"请求数据: {json.dumps(payload)}")
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"响应状态: {response.status_code}")
    print(f"响应内容: {response.text[:500]}")
    
    try:
        result = response.json()
    except:
        raise Exception(f"JSON解析失败, 原始响应: {response.text}")
    
    if result.get("code") == 0:
        children = result.get("data", {}).get("children", [])
        if children:
            return children[0].get("block_id")
    else:
        print(f"创建图片块失败: {result}")
        raise Exception(f"创建图片块失败: {result}")

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
        raise Exception(f"上传图片素材失败: {result}")

def update_image_block(access_token, doc_id, block_id, file_token):
    """更新图片块，绑定素材token"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/batch_update"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 根据飞书文档，使用 replace_image 操作
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
    
    print(f"更新图片块请求: {json.dumps(payload)}")
    
    response = requests.patch(url, headers=headers, json=payload)
    result = response.json()
    
    print(f"更新响应: {result}")
    
    if result.get("code") == 0:
        return True
    else:
        print(f"更新图片块失败: {result}")
        raise Exception(f"更新图片块失败: {result}")

def main():
    print("=" * 60)
    print("开始将图片插入到飞书文档")
    print("=" * 60)
    
    # 获取token
    print("\n获取访问令牌...")
    access_token = get_access_token()
    print(f"✓ 获取成功")
    
    # 获取文档信息
    print(f"\n文档ID: {DOC_ID}")
    
    # 上传并插入每张图片
    for skill_name, image_file in IMAGES:
        image_path = WORKSPACE_DIR / image_file
        
        if not image_path.exists():
            print(f"✗ 图片不存在: {image_path}")
            continue
        
        print(f"\n处理: {skill_name} ({image_file})")
        
        try:
            # 步骤1：创建图片块
            print(f"  步骤1: 创建图片块...")
            block_id = create_image_block(access_token, DOC_ID)
            print(f"  ✓ 图片块已创建, block_id: {block_id}")
            
            # 步骤2：上传图片素材
            print(f"  步骤2: 上传图片素材...")
            file_token = upload_image_media(access_token, str(image_path), block_id)
            print(f"  ✓ 图片素材已上传, file_token: {file_token}")
            
            # 步骤3：更新图片块
            print(f"  步骤3: 绑定素材到图片块...")
            update_image_block(access_token, DOC_ID, block_id, file_token)
            print(f"  ✓ 素材已绑定到图片块")
            
            print(f"✓ {skill_name} 插入成功!")
            
        except Exception as e:
            print(f"✗ 处理失败: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("图片插入完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
