#!/usr/bin/env python3
"""
创建飞书文档并插入图片
"""

import os
import requests
import json

# 飞书凭证
APP_ID = "cli_a95ca1da35f95cca"
APP_SECRET = "9CK0wKf6DI3UmJgEerk8gecLDZ4aBI4U"

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

def create_document(token, title):
    """创建飞书文档"""
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"title": title}
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") != 0:
        raise Exception(f"创建文档失败: {result}")
    
    return result["data"]["document"]["document_id"]

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

def create_text_block(text):
    """创建文本块"""
    block = {
        "block_type": 2,
        "text": {
            "elements": [
                {
                    "text_run": {
                        "content": text,
                        "text_element_style": {}
                    }
                }
            ],
            "style": {}
        }
    }
    return block

def create_heading2_block(text):
    """创建h2标题块"""
    block = {
        "block_type": 4,
        "heading2": {
            "elements": [
                {
                    "text_run": {
                        "content": text,
                        "text_element_style": {}
                    }
                }
            ],
            "style": {}
        }
    }
    return block

def create_doc():
    """创建文档"""
    token = get_tenant_access_token()
    print(f"获取token成功")
    
    # 创建文档
    doc_id = create_document(token, "6个小白必备的Claude Code Skills")
    print(f"创建文档成功: {doc_id}")
    
    # 插入标题
    insert_blocks(token, doc_id, [create_text_block("6个小白必备的Claude Code Skills")])
    
    # 插入正文
    insert_blocks(token, doc_id, [create_text_block("")])
    insert_blocks(token, doc_id, [create_text_block("哈喽大家好，这里是六六~")])
    insert_blocks(token, doc_id, [create_text_block("今天推荐给大家6个使用Claude Code必须安装的skills，技术小白和开发者都适用。")])
    insert_blocks(token, doc_id, [create_text_block("")])
    
    # 第一个skill
    insert_blocks(token, doc_id, [create_heading2_block("第一个：skill-vetter")])
    insert_blocks(token, doc_id, [create_text_block("装任何skill之前，先用它审查一遍。它会出具风险报告，告诉你这个skill有没有偷权限、有没有安全隐患。我是直接让Claude Code把这个当作规则写进了claude.md文档里面，每次让它下载skill的时候，它都会先帮我审查skill的风险。安全是底线，建议必须装。")])
    insert_blocks(token, doc_id, [create_text_block("")])
    insert_blocks(token, doc_id, [create_text_block("地址：https://clawhub.ai/spclaudehome/skill-vetter")])
    insert_blocks(token, doc_id, [create_text_block("")])
    
    # 第二个skill
    insert_blocks(token, doc_id, [create_heading2_block("第二个：markdown-proxy")])
    insert_blocks(token, doc_id, [create_text_block("做内容最怕的就是看到好文章没法保存。这个可将任意URL转换为干净的Markdown格式，包括像公众号、飞书文档、推文等等需要登录的页面。看到好文章5秒存到本地方便管理和复用，不用复制粘贴。素材管理效率翻倍。")])
    insert_blocks(token, doc_id, [create_text_block("")])
    insert_blocks(token, doc_id, [create_text_block("地址：https://github.com/joeseesun/markdown-proxy")])
    insert_blocks(token, doc_id, [create_text_block("")])
    
    # 第三个skill
    insert_blocks(token, doc_id, [create_heading2_block("第三个：follow-builders")])
    insert_blocks(token, doc_id, [create_text_block("这是张咋啦把自己高质量AI信息源做成了skill，不用接任何API Key，而且完全免费。普通人最怕的就是信息闭塞，错过窗口期。它可以帮你省下每天刷信息流的时间，像我做自媒体最怕的就是闭门造车，这个能让我随时掌握行业权威风向。")])
    insert_blocks(token, doc_id, [create_text_block("")])
    insert_blocks(token, doc_id, [create_text_block("地址：https://github.com/zarazhangrui/follow-builders")])
    insert_blocks(token, doc_id, [create_text_block("")])
    
    # 第四个skill
    insert_blocks(token, doc_id, [create_heading2_block("第四个：skill-creator")])
    insert_blocks(token, doc_id, [create_text_block("零基础也能创建专属skill的skill，Anthropic官方出品，门槛极低。每次你要创建skill的时候，Claude Code会自动调用这个skill来一步步引导你梳理需求，从0开始构建属于你的工具。学会之后再也不用求人，是Claude Code生态里必须点亮的技能树。")])
    insert_blocks(token, doc_id, [create_text_block("")])
    insert_blocks(token, doc_id, [create_text_block("地址：https://github.com/anthropics/skills/tree/main/skills/skill-creator")])
    insert_blocks(token, doc_id, [create_text_block("")])
    
    # 第五个skill
    insert_blocks(token, doc_id, [create_heading2_block("第五个：superpowers")])
    insert_blocks(token, doc_id, [create_text_block("这是ADHD必备的skill了，只需要给AI一个模糊的想法，它就能帮你脑暴延伸，梳理成完整的落地方案。我每次做项目之前都会先用它过一遍，至少能少走一半弯路，效率拉满。")])
    insert_blocks(token, doc_id, [create_text_block("")])
    insert_blocks(token, doc_id, [create_text_block("地址：https://github.com/obra/superpowers")])
    insert_blocks(token, doc_id, [create_text_block("")])
    
    # 第六个skill
    insert_blocks(token, doc_id, [create_heading2_block("第六个：agent-browser")])
    insert_blocks(token, doc_id, [create_text_block("这是浏览器自动化的skill。可以帮你完成重复性的网页操作，自动操作浏览器，比如批量下载、批量填表，以前要花一天的操作，现在几分钟搞定。")])
    insert_blocks(token, doc_id, [create_text_block("")])
    insert_blocks(token, doc_id, [create_text_block("地址：https://github.com/vercel-labs/agent-browser")])
    insert_blocks(token, doc_id, [create_text_block("")])
    
    # 结尾
    insert_blocks(token, doc_id, [create_text_block("")])
    insert_blocks(token, doc_id, [create_text_block("最后，感谢大家能够看到这里🥰")])
    insert_blocks(token, doc_id, [create_text_block("")])
    insert_blocks(token, doc_id, [create_text_block("如果这篇文章对你有启发，可以顺手给六六 点赞 | 在看 | 转发 | 评论")])
    insert_blocks(token, doc_id, [create_text_block("")])
    insert_blocks(token, doc_id, [create_text_block("如果想进一步和我交流的话，可以添加: liuliuxueai66，加入我的AI交流群")])
    
    print(f"\n文档创建完成！")
    print(f"文档ID: {doc_id}")
    print(f"文档链接: https://feishu.cn/docx/{doc_id}")
    
    return doc_id

if __name__ == "__main__":
    doc_id = create_doc()
