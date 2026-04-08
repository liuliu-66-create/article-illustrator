# Article Illustrator - 公众号文章配图生成器

将人物照片转换为可爱的卡通IP形象三视图，再根据公众号文章内容生成带IP形象的信息图。

## 功能特点

- 🎨 **IP形象生成**：上传人物照片，自动生成卡通三视图
- 📊 **信息图生成**：根据文章内容自动生成配图
- 🤖 **AI驱动**：使用阿里云百炼 wan2.7-image 模型
- 📐 **16:9标准尺寸**：适配公众号文章排版

## 前置条件

1. **阿里云百炼 API Key**：配置在 `config.json` 中的 `dashscope.api_key`
2. **飞书凭证**：在 `SECRET.md` 中配置飞书应用凭证
3. **Python 依赖**：`requests`

## 使用方法

详见 [SKILL.md](./SKILL.md)

## 目录结构

```
article-illustrator/
├── SKILL.md           # 技能说明文档
├── fonts/             # 字体资源
├── references/        # 参考提示词
├── scripts/           # Python 脚本
└── workspace/         # 工作目录
```

## License

MIT
