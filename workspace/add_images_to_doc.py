#!/usr/bin/env python3
"""
添加图片到飞书文档 - 尝试使用文档图片上传接口
"""

import os
import requests
import json

# 飞书凭证
APP_ID = "cli_a95ca1da35f95cca"
APP_SECRET = "9CK0wKf6DI3UmJgEerk8gecLDZ4aBI4U"

# 文档ID
DOC_ID = "F0e3dQiXSok3rhxMpEdcdDGtnib"

# 图片路径 (绝对路径)
BASE_DIR = "/app/data/所有对话/主对话"
IMAGE_FILES = [
    f"{BASE_DIR}/.skills/article-illustrator/workspace/infographic_01.png",
    f"{BASE_DIR}/.skills/article-illustrator/workspace/infographic_02.png",
    f"{BASE_DIR}/.skills/article-illustrator/workspace/infographic_03.png",
    f"{BASE_DIR}/.skills/article-illustrator/workspace/infographic_04.png",
    f"{BASE_DIR}/.skills/article-illustrator/workspace/infographic_05.png",
    f"{BASE_DIR}/.skills/article-illustrator/workspace/infographic_06.png",
]

def get_tenant_access_token():
    """获取 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") != 0:
        raise Exception(f"获取token失败: {result}")
    
    return result["tenant_access_token"]

def upload_image_to_docx(token, doc_id, image_path):
    """使用文档图片上传接口"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/media"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(image_path, 'rb') as f:
        files = {
            'file': ('image.png', f.read(), 'image/png')
        }
        
        response = requests.post(url, headers=headers, files=files)
        result = response.json()
        
        if result.get("code") != 0:
            print(f"上传图片到文档失败: {result}")
            return None
        
        return result["data"].get("token") or result["data"].get("file_token")

def insert_image_block(token, doc_id, image_token, index=-1):
    """在文档中插入图片块"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 使用docx图片上传接口返回的token
    data = {
        "children": [
            {
                "block_type": 27,
                "image": {
                    "token": image_token,
                    "width": 640,
                    "height": 360
                }
            }
        ],
        "index": index
    }
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") != 0:
        print(f"插入图片块失败: {result}")
        return False
    
    return True

def add_images_to_doc():
    """添加图片到文档"""
    token = get_tenant_access_token()
    print(f"获取token成功")
    
    # 上传并插入每张图片
    for i, image_path in enumerate(IMAGE_FILES):
        print(f"\n处理图片 {i+1}: {image_path}")
        
        # 使用文档图片上传接口
        image_token = upload_image_to_docx(token, DOC_ID, image_path)
        if not image_token:
            print(f"跳过图片 {i+1}")
            continue
        
        print(f"上传成功, token: {image_token}")
        
        # 插入图片块到文档
        success = insert_image_block(token, DOC_ID, image_token)
        if success:
            print(f"插入图片块成功")
        else:
            print(f"插入图片块失败")
    
    print(f"\n所有图片处理完成！")
    print(f"文档链接: https://feishu.cn/docx/{DOC_ID}")

if __name__ == "__main__":
    add_images_to_doc()
