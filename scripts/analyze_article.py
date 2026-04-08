#!/usr/bin/env python3
"""
文章分析脚本。
分析公众号文章，识别适合插入配图的位置，提取关键信息。

Usage:
    python analyze_article.py --input <文章路径> [--max-images <数量>]

Returns:
    JSON: {
        "success": true,
        "title": "文章标题",
        "positions": [
            {
                "index": 0,
                "type": "intro",
                "paragraph": "段落内容...",
                "suggested_theme": "配图主题建议",
                "keywords": ["关键词1", "关键词2"]
            },
            ...
        ]
    }
"""

import argparse
import io
import json
import re
import sys
from pathlib import Path
from typing import List, Dict

# Windows 终端 UTF-8 输出
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def read_article(path: str) -> str:
    """读取文章内容"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_title(content: str) -> str:
    """提取文章标题"""
    lines = content.strip().split("\n")
    for line in lines[:5]:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        if line and len(line) < 50:
            return line
    return "未命名文章"


def split_paragraphs(content: str) -> List[str]:
    """拆分段落"""
    # 先按空行分割
    paragraphs = re.split(r'\n\s*\n', content)
    
    result = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # 如果段落太长（超过500字），按句子拆分
        if len(p) > 500:
            sentences = re.split(r'[。！？\n]', p)
            current = ""
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                if len(current) + len(s) < 400:
                    current += s + "。"
                else:
                    if current:
                        result.append(current)
                    current = s + "。"
            if current:
                result.append(current)
        else:
            result.append(p)
    
    return result


def classify_paragraph(paragraph: str, index: int, total: int) -> Dict:
    """分析段落类型和内容"""
    p = paragraph.lower()
    
    # 判断段落类型
    if index == 0:
        ptype = "intro"
        theme = "引入/开篇配图"
    elif index == total - 1:
        ptype = "conclusion"
        theme = "总结/结尾配图"
    elif any(kw in p for kw in ["首先", "第一", "1.", "①", "一是"]):
        ptype = "list_start"
        theme = "要点列举配图"
    elif any(kw in p for kw in ["其次", "第二", "2.", "②", "二是"]):
        ptype = "list_item"
        theme = "要点配图"
    elif any(kw in p for kw in ["最后", "第三", "3.", "③", "三是"]):
        ptype = "list_item"
        theme = "要点配图"
    elif any(kw in p for kw in ["因此", "所以", "总之", "综上所述"]):
        ptype = "transition"
        theme = "过渡/总结配图"
    elif any(kw in p for kw in ["数据", "显示", "统计", "%", "增长", "下降"]):
        ptype = "data"
        theme = "数据展示配图"
    elif any(kw in p for kw in ["重要", "关键", "核心", "注意"]):
        ptype = "highlight"
        theme = "重点强调配图"
    elif any(kw in p for kw in ["例如", "比如", "案例", "故事"]):
        ptype = "example"
        theme = "案例说明配图"
    else:
        ptype = "content"
        theme = "内容配图"
    
    # 提取关键词
    keywords = extract_keywords(paragraph)
    
    return {
        "type": ptype,
        "theme": theme,
        "keywords": keywords
    }


def extract_keywords(text: str) -> List[str]:
    """提取关键词（简单实现）"""
    # 移除标点符号
    text = re.sub(r'[，。！？、；：""''【】（）\s]+', ' ', text)
    
    # 简单的关键词提取：提取名词性的词汇
    # 这里用一个简化版本，实际可以用 NLP 库
    stop_words = {"的", "了", "是", "在", "和", "与", "或", "这", "那", "有", "为", "以", "及", "等", "中", "上", "下", "不", "就", "也", "都", "而", "且", "但", "如果", "因为", "所以", "虽然", "但是", "可以", "需要", "应该", "可能", "能够"}
    
    words = text.split()
    keywords = []
    
    for word in words:
        word = word.strip()
        if len(word) >= 2 and word not in stop_words:
            keywords.append(word)
    
    # 去重并保留前5个
    seen = set()
    result = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            result.append(kw)
            if len(result) >= 5:
                break
    
    return result


def analyze_article(content: str, max_images: int = 5) -> Dict:
    """分析文章，返回配图位置建议"""
    title = extract_title(content)
    paragraphs = split_paragraphs(content)
    total = len(paragraphs)
    
    positions = []
    
    # 总是包含开头
    if total > 0:
        info = classify_paragraph(paragraphs[0], 0, total)
        positions.append({
            "index": 0,
            "type": info["type"],
            "paragraph": paragraphs[0][:200] + ("..." if len(paragraphs[0]) > 200 else ""),
            "suggested_theme": info["theme"],
            "keywords": info["keywords"]
        })
    
    # 中间段落：选择最重要的几个
    middle_positions = []
    for i in range(1, total - 1):
        info = classify_paragraph(paragraphs[i], i, total)
        # 优先选择有特殊类型的段落
        if info["type"] in ["list_item", "data", "highlight", "example", "transition"]:
            middle_positions.append({
                "index": i,
                "type": info["type"],
                "paragraph": paragraphs[i][:200] + ("..." if len(paragraphs[i]) > 200 else ""),
                "suggested_theme": info["theme"],
                "keywords": info["keywords"],
                "priority": 2
            })
        else:
            middle_positions.append({
                "index": i,
                "type": info["type"],
                "paragraph": paragraphs[i][:200] + ("..." if len(paragraphs[i]) > 200 else ""),
                "suggested_theme": info["theme"],
                "keywords": info["keywords"],
                "priority": 1
            })
    
    # 按优先级排序，选择最高优先级的
    middle_positions.sort(key=lambda x: x["priority"], reverse=True)
    
    # 计算可以添加多少中间段落
    remaining = max_images - 1  # 减去开头
    if total > 1:  # 还有结尾
        remaining -= 1
    
    positions.extend(middle_positions[:remaining])
    
    # 总是包含结尾
    if total > 1:
        info = classify_paragraph(paragraphs[-1], total - 1, total)
        positions.append({
            "index": total - 1,
            "type": info["type"],
            "paragraph": paragraphs[-1][:200] + ("..." if len(paragraphs[-1]) > 200 else ""),
            "suggested_theme": info["theme"],
            "keywords": info["keywords"]
        })
    
    # 按段落顺序排序
    positions.sort(key=lambda x: x["index"])
    
    return {
        "success": True,
        "title": title,
        "total_paragraphs": total,
        "positions": positions
    }


def main():
    parser = argparse.ArgumentParser(description="文章分析工具")
    parser.add_argument("--input", required=True, help="文章文件路径")
    parser.add_argument("--max-images", type=int, default=5, help="最大配图数量")
    parser.add_argument("--output", help="输出 JSON 文件路径（可选）")
    
    args = parser.parse_args()
    
    content = read_article(args.input)
    result = analyze_article(content, args.max_images)
    
    output = json.dumps(result, ensure_ascii=False, indent=2)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
