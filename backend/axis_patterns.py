"""
Debate axis patterns for BREAK application.

Defines 21 debate axes organized by 7 categories, used by Judge AI
to select the most appropriate axis for a given topic.
"""
from typing import List, Dict, Optional


# 21 debate axes organized by 7 categories (requirements.md line 54-75)
AXIS_PATTERNS: List[Dict[str, str]] = [
    # カテゴリ1: 倫理・道徳系
    {
        "id": 1,
        "category": "倫理・道徳",
        "left": "原則主義",
        "right": "結果主義",
        "description": "普遍的原則を重視するか、実際の結果を重視するか"
    },
    {
        "id": 2,
        "category": "倫理・道徳",
        "left": "個人の自由",
        "right": "社会規範",
        "description": "個人の自由を優先するか、社会の規範を優先するか"
    },
    {
        "id": 3,
        "category": "倫理・道徳",
        "left": "権利重視",
        "right": "義務重視",
        "description": "個人の権利を優先するか、社会への義務を優先するか"
    },

    # カテゴリ2: 技術・イノベーション系
    {
        "id": 4,
        "category": "技術・イノベーション",
        "left": "技術進歩主義",
        "right": "技術慎重主義",
        "description": "技術の急速な進歩を推進するか、慎重に進めるか"
    },
    {
        "id": 5,
        "category": "技術・イノベーション",
        "left": "効率最適化",
        "right": "人間中心主義",
        "description": "効率を追求するか、人間の幸福を優先するか"
    },
    {
        "id": 6,
        "category": "技術・イノベーション",
        "left": "データ駆動",
        "right": "直感重視",
        "description": "データに基づく判断を重視するか、直感を重視するか"
    },

    # カテゴリ3: 健康・医療系
    {
        "id": 7,
        "category": "健康・医療",
        "left": "健康最優先",
        "right": "QOL優先",
        "description": "身体的健康を最優先するか、生活の質（QOL）を優先するか"
    },
    {
        "id": 8,
        "category": "健康・医療",
        "left": "科学的根拠",
        "right": "個人の体感",
        "description": "科学的エビデンスを重視するか、個人の体感を重視するか"
    },
    {
        "id": 9,
        "category": "健康・医療",
        "left": "予防原則",
        "right": "自己責任原則",
        "description": "予防的措置を重視するか、個人の自己責任を重視するか"
    },

    # カテゴリ4: 社会・公平性系
    {
        "id": 10,
        "category": "社会・公平性",
        "left": "平等主義",
        "right": "能力主義",
        "description": "全員に平等な機会を与えるか、能力に応じた配分をするか"
    },
    {
        "id": 11,
        "category": "社会・公平性",
        "left": "個人の権利",
        "right": "公共の安全",
        "description": "個人の権利を優先するか、公共の安全を優先するか"
    },
    {
        "id": 12,
        "category": "社会・公平性",
        "left": "現実主義",
        "right": "理想主義",
        "description": "現実的な解決策を優先するか、理想的なビジョンを追求するか"
    },

    # カテゴリ5: 恋愛・人間関係系
    {
        "id": 13,
        "category": "恋愛・人間関係",
        "left": "希望尊重",
        "right": "現実認識",
        "description": "相手の希望を尊重するか、現実的な問題を認識するか"
    },
    {
        "id": 14,
        "category": "恋愛・人間関係",
        "left": "自由恋愛",
        "right": "社会規範",
        "description": "自由な恋愛を尊重するか、社会規範に従うか"
    },
    {
        "id": 15,
        "category": "恋愛・人間関係",
        "left": "信頼基盤",
        "right": "疑念対応",
        "description": "相手への信頼を基盤とするか、疑念に対応するか"
    },

    # カテゴリ6: キャリア・経済系
    {
        "id": 16,
        "category": "キャリア・経済",
        "left": "キャリア投資",
        "right": "リスク回避",
        "description": "キャリアへの投資を優先するか、リスクを回避するか"
    },
    {
        "id": 17,
        "category": "キャリア・経済",
        "left": "経済的自由",
        "right": "社会貢献",
        "description": "個人の経済的自由を優先するか、社会への貢献を優先するか"
    },
    {
        "id": 18,
        "category": "キャリア・経済",
        "left": "短期最適",
        "right": "長期最適",
        "description": "短期的な利益を優先するか、長期的な持続可能性を優先するか"
    },

    # カテゴリ7: 規制・政策系
    {
        "id": 19,
        "category": "規制・政策",
        "left": "規制強化",
        "right": "市場自由",
        "description": "規制を強化するか、市場の自由に任せるか"
    },
    {
        "id": 20,
        "category": "規制・政策",
        "left": "保護主義",
        "right": "自己責任",
        "description": "保護政策を推進するか、自己責任を重視するか"
    },
    {
        "id": 21,
        "category": "規制・政策",
        "left": "事前規制",
        "right": "事後対処",
        "description": "事前に規制するか、問題発生後に対処するか"
    },
]


def get_axis_by_id(axis_id: int) -> Optional[Dict[str, str]]:
    """
    Get debate axis by ID.

    Args:
        axis_id: Axis ID (1-21)

    Returns:
        Axis dictionary if found, None otherwise.
        Dictionary contains: id, category, left, right, description

    Example:
        >>> axis = get_axis_by_id(1)
        >>> axis["left"]
        '原則主義'
        >>> axis["right"]
        '結果主義'
    """
    for axis in AXIS_PATTERNS:
        if axis["id"] == axis_id:
            return axis
    return None


def get_axes_by_category(category: str) -> List[Dict[str, str]]:
    """
    Get all debate axes in a specific category.

    Args:
        category: Category name (e.g., "倫理・道徳", "技術・イノベーション")

    Returns:
        List of axis dictionaries in the specified category.

    Example:
        >>> axes = get_axes_by_category("倫理・道徳")
        >>> len(axes)
        3
        >>> axes[0]["left"]
        '原則主義'
    """
    return [axis for axis in AXIS_PATTERNS if axis["category"] == category]


def format_axes_for_prompt() -> str:
    """
    Format all debate axes into a string suitable for Judge AI prompt.

    Returns a formatted list of all 21 axes with ID, left/right sides,
    and description, ready to be included in the axis selection prompt.

    Returns:
        Formatted string with all axes.

    Example:
        >>> prompt_text = format_axes_for_prompt()
        >>> "1. 原則主義 vs 結果主義" in prompt_text
        True
    """
    lines = ["以下の21種類の対立軸から、トピックに最も適した軸を1つ選んでください：\n"]

    for axis in AXIS_PATTERNS:
        lines.append(
            f"{axis['id']}. {axis['left']} vs {axis['right']} "
            f"({axis['description']})"
        )

    return "\n".join(lines)
