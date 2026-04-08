#!/usr/bin/env python3
"""
图片生成脚本。
调用阿里云百炼 wan2.7-image API，生成三视图和信息图。
支持 IP 形象保存和复用功能。

Usage:
    # 检查是否有保存的 IP 形象
    python generate_image.py --check-ip
    
    # 保存 IP 形象（生成三视图后调用）
    python generate_image.py --save-ip --input workspace/ip_triple_view.png
    
    # 生成三视图
    python generate_image.py --mode triple_view --input <人物照片> --output <输出路径>
    
    # 生成信息图（自动使用保存的 IP 形象）
    python generate_image.py --mode infographic --text "<文案内容>" --output <输出路径>

Returns:
    JSON: {"success": true, "output_path": "...", "image_url": "..."}
"""

import argparse
import base64
import io
import json
import os
import sys
import time
import requests
from pathlib import Path

# Windows 终端 UTF-8 输出
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 共用 dresscast 的配置
DRESSCAST_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "dresscast" / "config.json"
SKILL_DIR = Path(__file__).resolve().parent.parent
TRIPLE_VIEW_PROMPT_PATH = SKILL_DIR / "references" / "triple_view_prompt.md"
INFOGRAPHIC_PROMPT_PATH = SKILL_DIR / "references" / "infographic_prompt.md"
WORKSPACE_DIR = SKILL_DIR / "workspace"
SAVED_IP_IMAGE = WORKSPACE_DIR / "saved_ip_image.png"

# DashScope API 端点
SYNC_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
ASYNC_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"
TASK_QUERY_URL = "https://dashscope.aliyuncs.com/api/v1/tasks/"


def load_config() -> dict:
    """加载 dresscast 的配置"""
    if DRESSCAST_CONFIG_PATH.exists():
        with open(DRESSCAST_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_api_key() -> str:
    config = load_config()
    key = config.get("dashscope", {}).get("api_key", "")
    if key:
        return key
    return os.environ.get("DASHSCOPE_API_KEY", "")


def get_image_model() -> str:
    config = load_config()
    return config.get("dashscope", {}).get("image_model", "wan2.7-image")


def check_saved_ip_image() -> dict:
    """检查是否有保存的 IP 形象"""
    if SAVED_IP_IMAGE.exists():
        return {
            "exists": True,
            "path": str(SAVED_IP_IMAGE),
            "message": "已保存 IP 形象，将自动使用"
        }
    else:
        return {
            "exists": False,
            "message": "未找到保存的 IP 形象，请先生成或上传"
        }


def save_ip_image(source_path: str) -> dict:
    """保存 IP 形象"""
    source = Path(source_path)
    if not source.exists():
        return {"success": False, "error": f"源文件不存在: {source_path}"}
    
    # 确保 workspace 目录存在
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 复制文件
    import shutil
    shutil.copy2(source, SAVED_IP_IMAGE)
    
    return {
        "success": True,
        "path": str(SAVED_IP_IMAGE),
        "message": f"IP 形象已保存到 {SAVED_IP_IMAGE}"
    }


def get_saved_ip_image_path() -> str | None:
    """获取保存的 IP 形象路径（如果存在）"""
    if SAVED_IP_IMAGE.exists():
        return str(SAVED_IP_IMAGE)
    return None


def encode_image_base64(image_path: str) -> str:
    """将图片编码为 Base64 data URI"""
    path = Path(image_path)
    if not path.exists():
        print(f"Error: 图片不存在: {image_path}", file=sys.stderr)
        sys.exit(1)

    suffix = path.suffix.lower().lstrip(".")
    mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "bmp": "bmp", "webp": "webp"}
    mime = f"image/{mime_map.get(suffix, 'jpeg')}"

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime};base64,{data}"


def download_image(url: str, output_path: str) -> bool:
    """下载图片到本地"""
    try:
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except requests.RequestException as e:
        print(f"Error: 下载图片失败: {e}", file=sys.stderr)
        return False


def load_prompt_template(mode: str) -> str:
    """加载提示词模板"""
    if mode == "triple_view":
        path = TRIPLE_VIEW_PROMPT_PATH
    else:
        path = INFOGRAPHIC_PROMPT_PATH
    
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            # 提取提示词部分
            if "## 提示词" in content:
                return content.split("## 提示词")[1].split("##")[0].strip()
            elif "## 系统提示词" in content:
                return content.split("## 系统提示词")[1].split("### ")[0].strip()
    return ""


def call_sync_with_reference(api_key: str, model: str, reference_image_b64: str, prompt: str) -> dict:
    """同步调用 wan2.7-image API（带参考图）"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "input": {
            "messages": [{
                "role": "user",
                "content": [
                    {"image": reference_image_b64},
                    {"text": prompt},
                ]
            }]
        },
        "parameters": {
            "size": "1920*1080",  # 16:9
            "n": 1,
            "watermark": False,
        }
    }
    
    try:
        resp = requests.post(SYNC_URL, headers=headers, json=payload, timeout=300)
        resp.raise_for_status()
        result = resp.json()
        
        # 检查错误
        if "code" in result and "output" not in result:
            return {"success": False, "error": f"API 错误: {result.get('code')} - {result.get('message')}"}
        
        # 提取图片 URL（同步格式）
        choices = result.get("output", {}).get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", [])
            for item in content:
                if item.get("type") == "image" and item.get("image"):
                    return {"success": True, "image_url": item["image"]}
        
        # 兼容 results 格式
        if result.get("output", {}).get("results"):
            return {"success": True, "results": result["output"]["results"], "image_url": result["output"]["results"][0].get("url", "")}
        
        return {"success": False, "error": "未返回图片", "response": result}
    except requests.Timeout:
        return {"success": False, "error": "同步调用超时", "timeout": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def call_sync_text_only(api_key: str, model: str, prompt: str) -> dict:
    """同步调用 wan2.7-image API（纯文本）"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "input": {
            "messages": [{
                "role": "user",
                "content": [
                    {"text": prompt},
                ]
            }]
        },
        "parameters": {
            "size": "1920*1080",  # 16:9
            "n": 1,
            "watermark": False,
        }
    }
    
    try:
        resp = requests.post(SYNC_URL, headers=headers, json=payload, timeout=300)
        resp.raise_for_status()
        result = resp.json()
        
        # 检查错误
        if "code" in result and "output" not in result:
            return {"success": False, "error": f"API 错误: {result.get('code')} - {result.get('message')}"}
        
        # 提取图片 URL
        choices = result.get("output", {}).get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", [])
            for item in content:
                if item.get("type") == "image" and item.get("image"):
                    return {"success": True, "image_url": item["image"]}
        
        # 兼容 results 格式
        if result.get("output", {}).get("results"):
            return {"success": True, "results": result["output"]["results"], "image_url": result["output"]["results"][0].get("url", "")}
        
        return {"success": False, "error": "未返回图片", "response": result}
    except requests.Timeout:
        return {"success": False, "error": "同步调用超时", "timeout": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def call_async(api_key: str, model: str, prompt: str, reference_image_b64: str = None) -> dict:
    """异步调用 API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }
    
    input_data = {"prompt": prompt}
    if reference_image_b64:
        input_data["images"] = [reference_image_b64]
    
    payload = {
        "model": model,
        "input": input_data,
        "parameters": {
            "size": "1920*1080",
            "n": 1
        }
    }
    
    try:
        resp = requests.post(ASYNC_URL, headers=headers, json=payload, timeout=60)
        result = resp.json()
        
        if "output" in result and "task_id" in result["output"]:
            return {"success": True, "task_id": result["output"]["task_id"]}
        else:
            return {"success": False, "error": result.get("message", str(result))}
    except Exception as e:
        return {"success": False, "error": str(e)}


def poll_task(api_key: str, task_id: str, timeout: int = 300) -> dict:
    """轮询异步任务状态"""
    headers = {"Authorization": f"Bearer {api_key}"}
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            resp = requests.get(f"{TASK_QUERY_URL}{task_id}", headers=headers, timeout=30)
            result = resp.json()
            
            status = result.get("output", {}).get("task_status", "")
            
            if status == "SUCCEEDED":
                results = result.get("output", {}).get("results", [])
                return {"success": True, "results": results}
            elif status == "FAILED":
                return {"success": False, "error": result.get("output", {}).get("message", "Task failed")}
            elif status in ["PENDING", "RUNNING"]:
                time.sleep(5)
            else:
                return {"success": False, "error": f"Unknown status: {status}"}
        except Exception as e:
            time.sleep(5)
    
    return {"success": False, "error": "Timeout"}


def generate_triple_view(input_path: str, output_path: str) -> dict:
    """生成三视图"""
    api_key = get_api_key()
    model = get_image_model()
    
    if not api_key:
        return {"success": False, "error": "未配置 API Key"}
    
    # 编码输入图片
    image_b64 = encode_image_base64(input_path)
    
    # 加载提示词
    prompt = load_prompt_template("triple_view")
    if not prompt:
        return {"success": False, "error": "未找到三视图提示词模板"}
    
    print(f"正在生成三视图...", file=sys.stderr)
    
    # 调用 API
    result = call_sync_with_reference(api_key, model, image_b64, prompt)
    
    if result.get("success") and result.get("image_url"):
        if download_image(result["image_url"], output_path):
            return {"success": True, "output_path": output_path, "image_url": result["image_url"]}
        else:
            return {"success": False, "error": "下载图片失败"}
    
    return result


def generate_infographic(text: str, output_path: str, reference_path: str = None) -> dict:
    """生成信息图"""
    api_key = get_api_key()
    model = get_image_model()
    
    if not api_key:
        return {"success": False, "error": "未配置 API Key"}
    
    # 加载提示词模板
    prompt_template = load_prompt_template("infographic_prompt")
    if not prompt_template:
        return {"success": False, "error": "未找到信息图提示词模板"}
    
    # 组合提示词
    prompt = f"{prompt_template}\n\n现在开始执行：\n\n用户输入文本如下（请根据文本生成信息图）：\n{text}"
    
    print(f"正在生成信息图...", file=sys.stderr)
    
    # 调用 API
    if reference_path:
        image_b64 = encode_image_base64(reference_path)
        result = call_sync_with_reference(api_key, model, image_b64, prompt)
    else:
        result = call_sync_text_only(api_key, model, prompt)
    
    if result.get("success") and result.get("image_url"):
        if download_image(result["image_url"], output_path):
            return {"success": True, "output_path": output_path, "image_url": result["image_url"]}
        else:
            return {"success": False, "error": "下载图片失败"}
    
    return result


def main():
    parser = argparse.ArgumentParser(description="图片生成工具")
    parser.add_argument("--mode", choices=["triple_view", "infographic"], help="生成模式")
    parser.add_argument("--input", help="输入图片路径（三视图模式）")
    parser.add_argument("--text", help="文本内容（信息图模式）")
    parser.add_argument("--output", help="输出图片路径")
    parser.add_argument("--reference", help="参考图片路径（信息图模式可选）")
    
    # IP 形象管理参数
    parser.add_argument("--check-ip", action="store_true", help="检查是否有保存的 IP 形象")
    parser.add_argument("--save-ip", action="store_true", help="保存 IP 形象到 workspace")
    
    args = parser.parse_args()
    
    # 检查 IP 形象
    if args.check_ip:
        result = check_saved_ip_image()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 保存 IP 形象
    if args.save_ip:
        if not args.input:
            print("Error: --save-ip 需要 --input 参数指定源文件", file=sys.stderr)
            sys.exit(1)
        result = save_ip_image(args.input)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 生成模式
    if args.mode == "triple_view":
        if not args.input:
            print("Error: 三视图模式需要 --input 参数", file=sys.stderr)
            sys.exit(1)
        result = generate_triple_view(args.input, args.output)
    elif args.mode == "infographic":
        if not args.text:
            print("Error: 信息图模式需要 --text 参数", file=sys.stderr)
            sys.exit(1)
        
        # 优先使用指定的参考图，其次使用保存的 IP 形象
        ref_path = args.reference
        if not ref_path:
            ref_path = get_saved_ip_image_path()
            if ref_path:
                print(f"使用保存的 IP 形象: {ref_path}", file=sys.stderr)
        
        result = generate_infographic(args.text, args.output, ref_path)
    else:
        print("Error: 请指定 --mode 或使用 --check-ip / --save-ip", file=sys.stderr)
        sys.exit(1)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
