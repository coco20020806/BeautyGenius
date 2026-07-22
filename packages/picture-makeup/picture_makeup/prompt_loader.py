"""Load prompt text from skill markdown."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from picture_makeup.config import PROMPT_TEXT_VERSION_DEFAULT

_DIAGRAM_FENCE = re.compile(r"```prompt-diagram\s*\n(.*?)```", re.DOTALL)
_TEXT_VERSION_RE = re.compile(r"prompt_text_version:\s*([a-zA-Z0-9_-]+)")
_SYSTEM_TEXT_BLOCK = re.compile(
    r"## System（固定）\s*\n\s*```text\s*\n(.*?)```",
    re.DOTALL,
)

BASE_PROMPT_SYSTEM_FALLBACK = """你是美妆跟练图示文案助手。根据教程步骤的结构化字段，生成一句中文 base_prompt，用于后续在固定人脸底图上用色块标注化妆范围。

只输出合法 JSON：
{
  "step_id": "与输入相同",
  "base_prompt": "一句完整中文"
}

base_prompt 写作规则：
1. 先描述本步手法与部位（扫、点、晕染、填色等），再描述颜色/质感（若有 visual_layer.color 或 product 信息）。
2. 必须包含 visual_layer.position 或从 instruction 推断出的等价位置描述（中文地标：颧骨、苹果肌、眼睑、唇线等）。
3. 句末必须以「请在原始图片上用色块标注着色范围」结尾（或「请在原始图片上用色块标注作用区域」——仅 prep/base/护肤类步骤可用「作用区域」替代「着色范围」）。
4. 长度建议 30–120 字；不要编号列表；不要 markdown。
5. visual_layer 缺 color 或 position 时，从 instruction、part、product 推断，仍须满足规则 3。
6. part 为 prep/base/set 等无典型彩妆色块时：描述涂抹/打底区域，句末仍用「作用区域」+ 色块标注要求，或说明用浅色半透明块标注全脸/分区。
7. 不要编造教程未出现的色号名称；opacity/shape 可融入描述（如「柔和椭圆」「低透明度」）。"""

ENRICH_SYSTEM_FALLBACK = """你是美妆步骤视觉校对助手。你会看到教程步骤的关键帧，以及已经写好的 base_prompt（不可修改）。

只输出合法 JSON：
{
  "step_id": "与输入相同",
  "appendix": "仅补充中文，可为空字符串",
  "conflict": false,
  "notes": "简短说明校对结论；无冲突可空字符串",
  "keyframe_roles_used": ["makeup_detail", ...]
}

规则：
1. 禁止输出新的 base_prompt 或 paraphrase base_prompt；禁止在 appendix 中重复 base_prompt 全文。
2. appendix 只补充：边界细节、晕染方向、工具痕迹、可见色感强弱、与 sub_step label 一致的区域名等。
3. 若画面与 base_prompt 部位/动作明显矛盾，conflict=true，appendix 留空或只写不矛盾的细节，notes 说明矛盾点。
4. appendix 直接接在 base_prompt 后阅读应通顺；不要以句号开头重复句末「请在原始图片上…」（该句已在 base_prompt 末尾）。
5. 总长度 appendix 建议 0–80 字。"""

DIAGRAM_STATIC_FALLBACK = """任务：在固定人脸底图上，为个性化后的美妆教程步骤生成跟练示意图。底图的人物身份、五官比例、脸型、发型、表情、姿态、皮肤纹理、光线和拍摄角度必须保持不变；只允许添加用于教学的半透明范围标注。

图像说明：
- 图1：原始示意底图/模板脸，是唯一的几何与身份来源。

标注要求：
- 根据「本步骤优化图示要求」在对应面部区域叠加半透明色块、柔和色区或必要的极简方向箭头。
- 色块要表达上妆范围，不要生成完整真实妆面。
- 边缘需要柔和，贴近真实晕染范围，但边界仍能让用户看懂。
- 标注颜色默认保持原始产品色系；在接近产品颜色的基础上，可向同色系深浅、冷暖或邻近色相做小幅扩展，让多个标注层之间有清晰对比度。
- 当同一步或同一底图存在多个相近颜色图层时，应通过明度、饱和度、冷暖或透明度区分层级，避免腮红、修容、高光、眼影等标注混成一片。
- 不确定产品颜色时，用低饱和粉、棕、香槟或肤色调作为基础，并为不同部位选择可辨认的邻近变化；不要跨到明显不属于原妆容的色系。
- 若要求缩短中庭，腮红应以横向平铺为主，最低边界不低于鼻翼线附近；修容起点相对原教程降低但保持柔和。
- 若要求眼部精讲，所有眼影、眼线、卧蚕、睫毛、眼头提亮、下至、眉眼距离标注必须集中在同一眼部底图上。

成片要求：
- 真实人像底图风格，勿卡通化，勿换脸。
- 保持底图原有脸廓、眼鼻嘴比例、发型与背景。
- 图示是教学标注，不是医学检测图或热力图。

禁止：
- 不得改变骨相、五官大小、年龄感、表情或肤色。
- 不得添加教程未要求的完整眼妆/唇妆成妆效果。
- 不得过度磨皮、加滤镜或添加无关装饰。
- 不得出现评价用户长相的文字。"""


@dataclass(frozen=True)
class DiagramPromptLoadResult:
    static_text: str
    prompt_text_version: str
    used_fallback: bool


def _load_system_from_md(path: Path, *, fallback: str) -> str:
    if not path.is_file():
        return fallback
    md = path.read_text(encoding="utf-8")
    m = _SYSTEM_TEXT_BLOCK.search(md)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return fallback


def load_base_prompt_system(skill_dir: Path) -> str:
    return _load_system_from_md(skill_dir / "step-prompt-qwen.md", fallback=BASE_PROMPT_SYSTEM_FALLBACK)


def load_enrich_system(skill_dir: Path) -> str:
    return _load_system_from_md(skill_dir / "keyframe-enrich-qwen.md", fallback=ENRICH_SYSTEM_FALLBACK)


def load_diagram_prompt(skill_dir: Path) -> DiagramPromptLoadResult:
    path = skill_dir / "diagram-prompt-wan.md"
    version = PROMPT_TEXT_VERSION_DEFAULT
    if path.is_file():
        md = path.read_text(encoding="utf-8")
        vm = _TEXT_VERSION_RE.search(md)
        if vm:
            version = vm.group(1).strip()
        m = _DIAGRAM_FENCE.search(md)
        if m and m.group(1).strip():
            return DiagramPromptLoadResult(
                static_text=m.group(1).strip(),
                prompt_text_version=version,
                used_fallback=False,
            )
    return DiagramPromptLoadResult(
        static_text=DIAGRAM_STATIC_FALLBACK,
        prompt_text_version=version,
        used_fallback=True,
    )


def compose_diagram_full_text(static: str, final_prompt: str) -> str:
    return f"{static.strip()}\n\n本步骤优化图示要求：\n{final_prompt.strip()}"
