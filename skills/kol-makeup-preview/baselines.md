# 平均脸底图（不上传用户照时使用）

底图文件位于 **Skill 根目录**（与 `SKILL.md` 同级），随 Skill 一起分发。

## 路径

| 用途 | 相对路径（`<repo-root>` 起） | Windows 示例 |
|------|------------------------------|--------------|
| 女性平均脸 | `skills/kol-makeup-preview/female_average_face.png` | `C:\Users\fei.kong\Desktop\Beauty Genius\skills\kol-makeup-preview\female_average_face.png` |
| 男性平均脸 | `skills/kol-makeup-preview/male_average_face.png` | `C:\Users\fei.kong\Desktop\Beauty Genius\skills\kol-makeup-preview\male_average_face.png` |

实现层默认解析：

```text
{skill_dir}/female_average_face.png
{skill_dir}/male_average_face.png
```

其中 `skill_dir` = `<repo-root>/skills/kol-makeup-preview/`。

## 选择规则

| 场景 | 使用文件 |
|------|----------|
| 用户不上传且选择/默认 **女性** 底图 | `female_average_face.png` |
| 用户不上传且选择 **男性** 底图 | `male_average_face.png` |
| CLI `--use-baseline female`（或省略，默认 `female`） | `female_average_face.png` |
| CLI `--use-baseline male` | `male_average_face.png` |

Agent：在用户明确「不上传」后，若未说明性别，可简短询问「女性或男性平均脸底图」；无回复时默认 **female**。

## 契约字段

底图分支写入 `preview.json`：

- `target.type`: `"average_baseline"`
- `target.baseline`: `"female"` \| `"male"`
- `target.skill_asset`: `"female_average_face.png"` \| `"male_average_face.png"`

## 说明

- 底图 **不跑** [face-validation.md](face-validation.md) 用户质检。
- 对用户须说明：**平均脸预览不代表本人脸型，仅作妆效参考**。
