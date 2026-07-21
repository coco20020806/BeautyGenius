# Beauty Genius

基于视频解析的美妆 Agent：用户上传美妆相关视频后，Agent 完成解析，并提供知识总结与沉淀能力。

## 能力规划

- **视频理解**：URL 或本地文件 → 抽帧、字幕/语音转写、内容结构化
- **知识总结**：步骤、产品、技巧、注意事项等可检索摘要
- **知识沉淀**：长期积累用户关心的美妆知识点（待实现）

## 视频解析 Skill

本项目推荐使用 Cursor Agent Skill **watch**（[claude-video](https://github.com/bradautomates/claude-video)）作为视频解析能力基础：

```bash
npx skills add bradautomates/claude-video -g
```

Windows 上需安装 `ffmpeg`、`yt-dlp`，可选配置 Whisper API（见 `~/.config/watch/.env` 或本仓库 `.env.example`）。

## 仓库

- GitHub: https://github.com/coco20020806/BeautyGenius

## 开发

```bash
git clone https://github.com/coco20020806/BeautyGenius.git
cd BeautyGenius
cp .env.example .env   # 按需填写
```

应用代码与目录结构将随功能迭代补充。

## License

TBD
