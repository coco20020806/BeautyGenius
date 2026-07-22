# 用户流程（user-flow）

## 状态

```text
AwaitingPhoto → Validating → Transferring → Done
                  ↓ fail
              AwaitingPhoto（带 reason + 拍摄指引）
```

| 状态 | 含义 |
|------|------|
| `AwaitingPhoto` | 已展示上传话术；等待路径或明确「不上传」 |
| `Validating` | 仅 `--user-photo`；跑 L0/L1/L2 |
| `Transferring` | 调用 `wan2.7-image-pro`（默认三图：妆后 + 教程妆前 + 目标脸；见 [transfer-prompt.md](transfer-prompt.md)） |
| `Done` | run 目录就绪 |

## 分支

### A. 用户上传照片

1. 收到本地路径或聊天附件落盘路径。
2. 执行质检（见 [face-validation.md](face-validation.md)）。
3. **通过** → `target.type = user_photo`，进入 Transferring。
4. **失败** → 返回 `reason`（优先 L2 中文）+ 下方「拍摄指引」，回到 AwaitingPhoto。

### B. 用户不上传

1. 用户明确跳过，或未在合理轮次内提供图。
2. 按 [baselines.md](baselines.md) 选用：
   - 女性：`skills/kol-makeup-preview/female_average_face.png`
   - 男性：`skills/kol-makeup-preview/male_average_face.png`（未指定时默认女性）
3. `target.type = average_baseline`，`target.baseline = female | male`；**不跑**用户图 L1/L2。
4. 生成前/后回复中须含：**此为平均脸底图预览，不代表你的脸型**。

### C. 仅有 reference、无 parse run

允许 `--reference-image <path>`；仍走 A 或 B。

## 拍摄指引（校验失败时原文模板）

请重新拍摄一张符合要求的照片：

- 正对镜头，眼睛平视看镜头，下巴不要明显抬高或压低  
- 摘掉口罩与墨镜，头发不要遮挡眉眼  
- 光线尽量均匀，避免强逆光或脸部过曝  
- 画面中仅你一人，脸不要太远或只拍半脸  
- 建议素颜或极淡妆，便于还原教程/KOL 的整妆效果  

## Agent 对话注意

- 不要替用户选择「不上传」除非用户明确拒绝或仅需快速看妆效。  
- 底图预览与 personal preview 在 `preview.json` 中必须可区分。
