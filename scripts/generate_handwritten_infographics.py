#!/usr/bin/env python3
"""
生成手绘风格信息图脚本 - 使用阿里云百炼wan2.7-image模型
正确格式调用API
"""

import sys
import os
import json
import base64
import time
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 配置
SKILL_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = SKILL_DIR / "workspace"
CONFIG_PATH = SKILL_DIR.parent / "dresscast" / "config.json"
SAVED_IP_IMAGE = WORKSPACE_DIR / "saved_ip_image.png"

# API配置 - 同步端点
API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

# 中文字体路径
FONT_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    "/usr/share/fonts/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]

def load_config():
    """加载配置"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_api_key():
    config = load_config()
    key = config.get("dashscope", {}).get("api_key", "")
    if key:
        return key
    return os.environ.get("DASHSCOPE_API_KEY", "")

def find_available_font(size=60):
    """找到可用的中文字体"""
    for font_path in FONT_PATHS:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, size)
                print(f"使用字体: {font_path}")
                return font_path, size
            except Exception as e:
                print(f"字体 {font_path} 加载失败: {e}")
                continue
    
    try:
        font = ImageFont.load_default()
        return None, 20
    except:
        return None, 20

def generate_image_with_wan(prompt, ref_image_path=None):
    """调用 wan2.7-image 模型生成图片"""
    api_key = get_api_key()
    if not api_key:
        raise ValueError("未找到 API Key")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建content数组
    content = [{"text": prompt}]
    
    # 如果有参考图片，添加参考图像
    if ref_image_path and os.path.exists(ref_image_path):
        with open(ref_image_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")
        content.append({"image": f"data:image/png;base64,{img_data}"})
    
    # 构建请求体 - 正确的格式
    payload = {
        "model": "wan2.7-image",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ]
        }
    }
    
    print(f"正在调用 wan2.7-image API...")
    print(f"Prompt长度: {len(prompt)} 字符")
    
    response = requests.post(API_URL, headers=headers, json=payload, timeout=180)
    
    print(f"响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"API响应: {json.dumps(result, ensure_ascii=False)[:500]}")
        
        # 同步接口直接返回结果
        if "output" in result:
            if "choices" in result["output"]:
                # 图片响应格式: result["output"]["choices"][0]["message"]["content"][0]["image"]
                choices = result["output"]["choices"]
                if choices and "message" in choices[0]:
                    content = choices[0]["message"].get("content", [])
                    for item in content:
                        if item.get("type") == "image":
                            return item["image"]
                # 备用：尝试直接获取text
                if "text" in choices[0]:
                    return choices[0]["text"]
        
        raise Exception(f"API返回格式异常: {result}")
    else:
        print(f"错误响应: {response.text}")
        raise Exception(f"API调用失败: {response.status_code}")

def download_image(url, output_path):
    """下载图片"""
    response = requests.get(url, timeout=60)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        return output_path
    else:
        raise Exception(f"图片下载失败: {response.status_code}")

def add_handwritten_text(image_path, title, subtitle, description, output_path):
    """在图片底部添加手写风格的中文文字"""
    # 打开图片
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    img_width, img_height = img.size
    
    # 查找可用字体
    font_path, _ = find_available_font(60)
    
    if font_path:
        try:
            title_font = ImageFont.truetype(font_path, 72)
            subtitle_font = ImageFont.truetype(font_path, 48)
            desc_font = ImageFont.truetype(font_path, 36)
        except Exception as e:
            print(f"字体加载失败: {e}")
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()
    else:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
    
    # 绘制半透明背景条
    padding = 50
    bar_height = 220
    bar_top = img_height - bar_height - padding
    
    # 创建背景
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [(0, bar_top), (img_width, img_height)],
        fill=(255, 255, 255, 220)
    )
    
    # 合成
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # 绘制文字
    x = padding
    y = bar_top + 30
    
    # 标题 - 使用较深的颜色
    draw.text((x, y), title, font=title_font, fill=(40, 40, 40))
    y += 80
    
    # 副标题
    draw.text((x, y), subtitle, font=subtitle_font, fill=(80, 80, 80))
    y += 60
    
    # 描述
    draw.text((x, y), description, font=desc_font, fill=(100, 100, 100))
    
    # 保存
    img.save(output_path, quality=95)
    print(f"✓ 文字已添加: {output_path}")

# 6个skill的信息
SKILLS = [
    {
        "name": "skill-vetter",
        "title": "安全审查",
        "subtitle": "skill-vetter",
        "description": "装任何skill之前先用它审查一遍，出具风险报告，排除安全隐患",
        "prompt": """Create a 16:9 horizontal infographic poster in hand-drawn cartoon style. The background is cream-colored with a subtle paper texture. Include a cute anime girl character with brown curly hair and black-framed glasses, wearing casual clothes. 

The character should be demonstrating a "security check" concept - perhaps holding a magnifying glass or shield, with a checkmark symbol nearby. 

Use warm pastel colors with hand-drawn outlines. Keep the bottom area (about 1/4 of the image) clear and light-colored for text overlay."""
    },
    {
        "name": "markdown-proxy",
        "title": "文章保存",
        "subtitle": "markdown-proxy",
        "description": "任意URL转换为干净Markdown格式，方便管理和复用",
        "prompt": """Create a 16:9 horizontal infographic poster in hand-drawn cartoon style. The background is cream-colored with a subtle paper texture. Include a cute anime girl character with brown curly hair and black-framed glasses, wearing casual clothes.

The character should be saving/organizing content - perhaps holding documents or a folder, with URLs or text documents floating around her.

Use warm pastel colors with hand-drawn outlines. Keep the bottom area (about 1/4 of the image) clear and light-colored for text overlay."""
    },
    {
        "name": "follow-builders",
        "title": "信息源追踪",
        "subtitle": "follow-builders",
        "description": "张咋啦高质量AI信息源，做自媒体必备",
        "prompt": """Create a 16:9 horizontal infographic poster in hand-drawn cartoon style. The background is cream-colored with a subtle paper texture. Include a cute anime girl character with brown curly hair and black-framed glasses, wearing casual clothes.

The character should be reading news or following information streams - perhaps holding a newspaper or looking at floating news feeds, with RSS or update icons around her.

Use warm pastel colors with hand-drawn outlines. Keep the bottom area (about 1/4 of the image) clear and light-colored for text overlay."""
    },
    {
        "name": "skill-creator",
        "title": "创建技能",
        "subtitle": "skill-creator",
        "description": "零基础创建专属skill，Anthropic官方出品",
        "prompt": """Create a 16:9 horizontal infographic poster in hand-drawn cartoon style. The background is cream-colored with a subtle paper texture. Include a cute anime girl character with brown curly hair and black-framed glasses, wearing casual clothes.

The character should be creating or building something - perhaps holding tools or gears, with lightbulb or building blocks around her, symbolizing skill creation.

Use warm pastel colors with hand-drawn outlines. Keep the bottom area (about 1/4 of the image) clear and light-colored for text overlay."""
    },
    {
        "name": "superpowers",
        "title": "脑暴方案",
        "subtitle": "superpowers",
        "description": "ADHD必备，从模糊想法生成完整落地方案",
        "prompt": """Create a 16:9 horizontal infographic poster in hand-drawn cartoon style. The background is cream-colored with a subtle paper texture. Include a cute anime girl character with brown curly hair and black-framed glasses, wearing casual clothes.

The character should be brainstorming or thinking creatively - perhaps with thought bubbles, lightbulbs, or mind map elements around her, showing the AI helping organize scattered ideas.

Use warm pastel colors with hand-drawn outlines. Keep the bottom area (about 1/4 of the image) clear and light-colored for text overlay."""
    },
    {
        "name": "agent-browser",
        "title": "浏览器自动化",
        "subtitle": "agent-browser",
        "description": "自动操作浏览器，批量下载填表，省时省力",
        "prompt": """Create a 16:9 horizontal infographic poster in hand-drawn cartoon style. The background is cream-colored with a subtle paper texture. Include a cute anime girl character with brown curly hair and black-framed glasses, wearing casual clothes.

The character should be controlling or automating a browser - perhaps with a laptop screen showing browser automation, robot hands, or multiple browser windows floating around her.

Use warm pastel colors with hand-drawn outlines. Keep the bottom area (about 1/4 of the image) clear and light-colored for text overlay."""
    }
]

def main():
    print("=" * 60)
    print("开始生成6张手绘风格信息图")
    print("=" * 60)
    
    # 检查IP形象
    if not SAVED_IP_IMAGE.exists():
        print(f"警告: 未找到保存的IP形象 {SAVED_IP_IMAGE}")
        ref_image = None
    else:
        ref_image = str(SAVED_IP_IMAGE)
        print(f"使用IP形象: {ref_image}")
    
    # 生成每张信息图
    for i, skill in enumerate(SKILLS, 1):
        print(f"\n[{i}/6] 正在生成: {skill['name']}")
        
        ai_output = WORKSPACE_DIR / f"ai_gen_{i:02d}.png"
        final_output = WORKSPACE_DIR / f"infographic_final_{i:02d}.png"
        
        try:
            # 调用API生成图片
            image_url = generate_image_with_wan(
                prompt=skill["prompt"],
                ref_image_path=ref_image
            )
            
            # 下载图片
            print(f"下载图片: {image_url[:80]}...")
            download_image(image_url, str(ai_output))
            
            # 添加文字
            add_handwritten_text(
                str(ai_output),
                skill["title"],
                skill["subtitle"],
                skill["description"],
                str(final_output)
            )
            
            print(f"✓ {skill['name']} 完成!")
            
        except Exception as e:
            print(f"✗ {skill['name']} 失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 60)
    print("所有图片生成完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
