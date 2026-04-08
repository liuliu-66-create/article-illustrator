---
name: article-illustrator
description: "公众号文章配图生成器。输入人物照片，生成卡通IP形象三视图，再根据文章内容生成带IP形象的信息图。使用阿里云百炼 wan2.7-image 模型，输出 16:9 尺寸图片。触发关键词：'公众号配图'、'文章插图'、'IP形象生成'、'卡通三视图'、'信息图生成'、'飞书文章'。"
---

# 公众号文章配图生成器

将人物照片转换为可爱的卡通IP形象三视图，再根据公众号文章内容生成带IP形象的信息图。

## 前置条件

1. **config.json 配置**：确认 `.skills/dresscast/config.json` 中 `dashscope.api_key` 已填入阿里云百炼 API Key
2. **飞书凭证**：确认 `SECRET.md` 中飞书应用凭证（app_id 和 app_secret）已配置
3. **Python 依赖**：`requests`

## 工作流程

### Step 1: 检查/获取IP形象（一次性设置）

**优先使用已保存的 IP 形象**：

```bash
# 检查是否有保存的 IP 形象
python scripts/generate_image.py --check-ip
```

**如果没有保存的 IP 形象**，需要先生成：

**方式 A：上传已有照片生成**
```bash
python scripts/generate_image.py --mode triple_view --input photo.jpg --output workspace/ip_triple_view.png
```

**方式 B：生成全新 IP 形象**
请提供一张清晰的人物照片，AI 将根据 `references/triple_view_prompt.md` 的提示词生成卡通三视图。

**保存 IP 形象**（生成三视图后必须执行）：
```bash
python scripts/generate_image.py --save-ip --input workspace/ip_triple_view.png
```

> 💡 提示：IP 形象只需生成一次，之后生成所有信息图都会自动使用保存的 IP 形象。

### Step 2: 读取文章

支持两种方式：

**方式 A：本地文件**
```bash
# 将文章保存为 Markdown 文件
# 然后使用 analyze_article.py 分析
python scripts/analyze_article.py --input article.md --output workspace/analysis.json
```

**方式 B：飞书文档链接**
```bash
python scripts/fetch_feishu_doc.py --url "https://www.feishu.cn/docx/xxxxx" --output workspace/article.md
```

> 💡 支持从飞书文档自动读取内容并转换为 Markdown 格式。

### Step 3: 分析文章并生成信息图

**分析文章**（识别适合配图的位置，提取核心文本）：
```bash
python scripts/analyze_article.py --input workspace/article.md --output workspace/analysis.json
```

**生成信息图**（必须使用 IP 形象作为参考图）：
```bash
# 根据分析的每个配图点生成信息图
# 会自动使用保存的 IP 形象作为参考图
python scripts/generate_image.py \
  --mode infographic \
  --text "从文章中总结的核心文本内容..." \
  --output workspace/infographic_01.png

# 或显式指定参考图
python scripts/generate_image.py \
  --mode infographic \
  --text "从文章中总结的核心文本内容..." \
  --reference workspace/saved_ip_image.png \
  --output workspace/infographic_01.png
```

> 💡 **重要**：信息图风格将与 IP 形象参考图保持一致。每张信息图只能出现一个人物形象。

#### 信息图生成流程

```
1. 从文章中总结一段核心文本（不是整篇文章）
2. 传入 IP 形象作为参考图（保持人物和风格一致）
3. 调用 wan2.7-image API 生成信息图
4. 信息图包含：手写标题 + 3-5个关键点 + 卡通人物
```

#### 信息图特点（参考 infographic_prompt.md）

| 特点 | 说明 |
|------|------|
| 风格 | 100%手绘卡通，与IP形象参考图风格一致 |
| 尺寸 | 16:9 横版 |
| 背景 | 米色速写纸，大量留白 |
| 文字 | 手写体效果，关键词化 |
| 人物 | 固定IP形象，每张图只有一人 |

### Step 4: 上传到飞书文档（可选）

将文章和配图上传到飞书云文档。

**使用 feishu_doc 技能**：
```bash
python ../skill_feishu_doc/scripts/create_doc.py \
  --title "文章标题" \
  --markdown "$(cat workspace/article_formatted.md)"
```

## 技术参数

| 项目 | 模型 | 说明 |
|------|------|------|
| 三视图生成 | wan2.7-image | 16:9 尺寸 |
| 信息图生成 | wan2.7-image | 16:9 尺寸 |

## 命令行使用示例

### 完整工作流

```bash
# 1. 检查 IP 形象
python scripts/generate_image.py --check-ip

# 2. 如果没有，生成三视图并保存
python scripts/generate_image.py --mode triple_view --input photo.jpg --output workspace/ip_triple_view.png
python scripts/generate_image.py --save-ip --input workspace/ip_triple_view.png

# 3. 读取飞书文档
python scripts/fetch_feishu_doc.py --url "https://www.feishu.cn/docx/xxxxx" --output workspace/article.md

# 4. 分析文章
python scripts/analyze_article.py --input workspace/article.md --output workspace/analysis.json

# 5. 生成信息图
python scripts/generate_image.py --mode infographic --text "第一个配图点的文案..." --output workspace/infographic_01.png
python scripts/generate_image.py --mode infographic --text "第二个配图点的文案..." --output workspace/infographic_02.png
```

## 配置说明

### 阿里云百炼配置
- 配置路径：`.skills/dresscast/config.json`
- 需要填入 `dashscope.api_key`

### 飞书应用配置
- 凭证位置：`SECRET.md` 中的飞书应用凭证
- 权限要求：需要开通「读取文档」权限

## IP 形象管理

### 核心功能
- `generate_image.py --check-ip`：检查是否有保存的 IP 形象
- `generate_image.py --save-ip --input <path>`：保存 IP 形象到 `workspace/saved_ip_image.png`
- 信息图生成时自动使用保存的 IP 形象

### 风格一致性（重要）

**信息图风格 = IP 形象参考图的风格**

生成信息图时，会自动读取保存的 IP 形象作为参考图，确保：
1. 人物形象与 IP 形象一致
2. 画风（彩铅/蜡笔/手绘等）与 IP 形象一致
3. 每张信息图只出现一个人物

### Skill 复用性

此 skill 可分享给他人使用。不同用户可能有不同的 IP 形象：

| 用户场景 | 处理方式 |
|---------|---------|
| 用户有自己的 IP 形象 | 上传并保存为 `saved_ip_image.png`，信息图自动适配风格 |
| 用户没有 IP 形象 | 先生成三视图，保存后再生成信息图 |
| 用户想换风格 | 删除 `saved_ip_image.png`，上传新的 IP 形象 |

### 人物姿势适配
根据内容情绪，信息图中的卡通人物会自动适配不同姿势：
| 情绪类型 | 关键词示例 | 适用姿势 |
|---------|-----------|---------|
| 思考/困惑 | 思考、为什么、如何、疑问 | 手托下巴或挠头 |
| 开心/推荐 | 开心、高兴、推荐、赞 | 挥手或竖大拇指 |
| 讲解/教学 | 讲解、方法、步骤 | 指向内容或手持道具 |
| 总结/收尾 | 总之、总结、关键点 | 双手摊开或做OK手势 |
| 提醒/注意 | 注意、提醒、小心 | 食指立于嘴唇前 |
| 加油/鼓励 | 加油、努力、坚持 | 握拳举起 |

> ⚠️ 同一个信息图中只允许出现同一个固定角色的不同姿势，严禁出现两个外观完全相同的分身。

## 文件结构

```
article-illustrator/
├── SKILL.md                    # 技能定义
├── references/
│   ├── triple_view_prompt.md   # 三视图生成提示词模板
│   └── infographic_prompt.md   # 信息图生成提示词模板（含姿势适配）
├── scripts/
│   ├── generate_image.py       # 图片生成脚本（含 IP 管理）
│   ├── analyze_article.py      # 文章分析脚本
│   ├── fetch_feishu_doc.py     # 飞书文档读取脚本（新增）
│   └── upload_to_feishu.py     # 飞书文档上传脚本
└── workspace/                  # 输出目录
    ├── saved_ip_image.png      # 保存的 IP 形象（生成后）
    ├── ip_triple_view.png      # 三视图输出
    ├── article.md              # 文章内容
    ├── analysis.json           # 分析结果
    └── infographic_*.png       # 生成的信息图
```

## 注意事项

1. **IP 形象只需生成一次**，之后会自动复用
2. 三视图生成需要清晰的人物正面照片
3. 信息图生成会根据内容情绪自动适配人物姿势
4. 所有图片输出为 16:9 比例
5. 飞书文档读取需要应用有相应权限
