#!/usr/bin/env python3
"""
添加图片链接到飞书文档
"""

import os
import requests
import json

# 飞书凭证
APP_ID = "cli_a95ca1da35f95cca"
APP_SECRET = "9CK0wKf6DI3UmJgEerk8gecLDZ4aBI4U"

# 文档ID
DOC_ID = "F0e3dQiXSok3rhxMpEdcdDGtnib"

# 图片URLs
IMAGE_URLS = {
    "skill-vetter": "https://www.coze.cn/s/q-idqI4Z7EI/",
    "markdown-proxy": "https://www.coze.cn/s/wlAT7tabMOg/",
    "follow-builders": "https://www.coze.cn/s/ZB3GdzQF9Bs/",
    "skill-creator": "https://www.coze.cn/s/ubda4N2f1E4/",
    "superpowers": "https://www.coze.cn/s/wqmcujS7kfk/",
    "agent-browser": "https://www.coze.cn/s/xIkS4EJPpvk/",
}

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

def insert_blocks(token, doc_id, blocks, index=-1):
    """插入内容块"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "children": blocks,
        "index": index
    }
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") != 0:
        print(f"插入块失败: {result}")
        return []
    
    return result.get("data", {}).get("children", [])

def create_text_with_link(text, link):
    """创建带有链接的文本块"""
    block = {
        "block_type": 2,
        "text": {
            "elements": [
                {
                    "text_run": {
                        "content": text,
                        "text_element_style": {}
                    }
                },
                {
                    "text_run": {
                        "content": link,
                        "text_element_style": {
                            "link": {
                                "url": link
                            }
                        }
                    }
                }
            ],
            "style": {}
        }
    }
    return block

def create_image_placeholder(title, image_url):
    """创建图片占位文本"""
    block = {
        "block_type": 2,
        "text": {
            "elements": [
                {
                    "text_run": {
                        "content": f"【配图: {title}】点击查看: ",
                        "text_element_style": {
                            "bold": True
                        }
                    }
                },
                {
                    "text_run": {
                        "content": image_url,
                        "text_element_style": {
                            "link": {
                                "url": image_url
                            }
                        }
                    }
                }
            ],
            "style": {}
        }
    }
    return block

def add_image_links_to_doc():
    """添加图片链接到文档"""
    token = get_tenant_access_token()
    print(f"获取token成功")
    
    # 技能标题
    skills = [
        ("skill-vetter", "第一个：skill-vetter"),
        ("markdown-proxy", "第二个：markdown-proxy"),
        ("follow-builders", "第三个：follow-builders"),
        ("skill-creator", "第四个：skill-creator"),
        ("superpowers", "第五个：superpowers"),
        ("agent-browser", "第六个：agent-browser"),
    ]
    
    # 在每个skill后面插入图片链接
    for skill_key, skill_title in skills:
        image_url = IMAGE_URLS.get(skill_key, "")
        if image_url:
            print(f"\n插入 {skill_title} 的配图链接...")
            insert_blocks(token, DOC_ID, [create_image_placeholder(skill_title, image_url)])
    
    print(f"\n所有图片链接处理完成！")
    print(f"文档链接: https://feishu.cn/docx/{DOC_ID}")

if __name__ == "__main__":
    add_image_links_to_doc()
