#!/usr/bin/env python3
"""
添加图片到飞书文档 - 调试API响应
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
        
        # 打印原始响应
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        print(f"响应内容: {response.text[:500]}")
        
        # 尝试解析JSON
        try:
            result = response.json()
            if result.get("code") != 0:
                print(f"上传图片到文档失败: {result}")
                return None
            return result["data"].get("token") or result["data"].get("file_token")
        except Exception as e:
            print(f"解析响应失败: {e}")
            return None

if __name__ == "__main__":
    token = get_tenant_access_token()
    print(f"获取token成功")
    upload_image_to_docx(token, DOC_ID, IMAGE_FILES[0])
