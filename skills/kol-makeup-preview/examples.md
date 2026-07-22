# 示例

Skill 目录：`<repo-root>/skills/kol-makeup-preview/`

## 1. 个人预览（上传正脸）

```powershell
cd "C:\Users\fei.kong\Desktop\Beauty Genius"
$env:DASHSCOPE_API_KEY = "sk-..."
python scripts/run_makeup_preview.py `
  --parse-run "outputs/runs/20260721_225221" `
  --user-photo "D:\Photos\selfie_front.jpg"
```

## 2. 平均脸底图（不上传）

女性（默认）：

```powershell
python scripts/run_makeup_preview.py `
  --parse-run "outputs/runs/20260721_225221" `
  --use-baseline
```

男性：

```powershell
python scripts/run_makeup_preview.py `
  --parse-run "outputs/runs/20260721_225221" `
  --use-baseline --baseline male
```

底图文件：`skills/kol-makeup-preview/female_average_face.png`、`male_average_face.png`（见 [baselines.md](baselines.md)）。

## 3. 手动参考图 + 底图

```powershell
python scripts/run_makeup_preview.py `
  --reference-image "D:\refs\kol_final.jpg" `
  --use-baseline
```

## 4. Agent 对话流

1. 用户：「我想看这套妆在我脸上什么样」  
2. Agent：加载 `skills/kol-makeup-preview/SKILL.md`，发送上传话术。  
3. 用户提供路径 → 跑质检 → 成功则生成并返回 `outputs/makeup-preview/runs/.../preview_01.jpg`。  
4. 用户：「不上传，先看效果」→ `--use-baseline`，并说明非本人脸型。

## 5. 安装 Skill 到 Cursor

```text
# junction（Windows 管理员或开发者模式）
mklink /J ".cursor\skills\kol-makeup-preview" "skills\kol-makeup-preview"
```

或复制 `skills/kol-makeup-preview` → `.cursor/skills/kol-makeup-preview`。

## 6. 仅校验照片

```powershell
python scripts/run_makeup_preview.py --validate-only --user-photo "D:\Photos\test.jpg"
```

## 7. 调试（不调用生成）

```powershell
python scripts/run_makeup_preview.py --parse-run outputs/runs/20260721_225221 --use-baseline --skip-transfer
```

## 8. 串联 parse + preview

```powershell
python scripts/run_beauty_replicate.py --parse-run outputs/runs/20260721_225221 --use-baseline --skip-transfer
# 或从视频开始：
# python scripts/run_beauty_replicate.py --video "D:\tutorial.mp4" --use-baseline
```

产物：`outputs/jobs/<timestamp>/manifest.json` 链接 parse 与 preview run。见 [docs/REPLICATE_PIPELINE.md](../../docs/REPLICATE_PIPELINE.md)。

## 9. 局部教程（scoped transfer）

当 parse run 的 `taxonomy-coverage.json` 中 `present_primaries` 仅含少量主类（如 `["唇妆"]`）时，preview 应写入 `transfer.prompt_mode: scoped`，并在 `transfer_prompt.txt` 末尾追加「教程范围约束」段落（见 [transfer-scope.md](transfer-scope.md)）。全脸对比仍使用 `target_display.jpg` / `preview_display.jpg`。
