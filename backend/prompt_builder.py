"""
Prompt builder for BREAK debate system.

Generates prompts for each phase of the debate:
1. Axis selection (Judge AI)
2. Round 1 arguments (AI_A and AI_B)
3. Round 2 counter-arguments (AI_A and AI_B)
4. Final judgment + synthesis (Judge AI)
"""
from typing import Dict, List, Any


def build_axis_prompt(topic: str) -> str:
    """
    Build prompt for axis selection by Judge AI.

    Args:
        topic: Debate topic entered by user

    Returns:
        Prompt string requesting Judge AI to select the most appropriate
        debate axis from 21 available axes.

    Example:
        >>> prompt = build_axis_prompt("AIによる雇用代替は良いことか？")
        >>> "21種類の対立軸" in prompt
        True
    """
    return f"""以下のトピックについて、最も適切な対立軸を21種類から1つ選んでください。

【トピック】
{topic}

【対立軸の選択肢（21種類）】
1. 原則主義 vs 結果主義 (普遍的原則を重視するか、実際の結果を重視するか)
2. 個人の自由 vs 社会規範 (個人の自由を優先するか、社会の規範を優先するか)
3. 権利重視 vs 義務重視 (個人の権利を優先するか、社会への義務を優先するか)
4. 技術進歩主義 vs 技術慎重主義 (技術の急速な進歩を推進するか、慎重に進めるか)
5. 効率最適化 vs 人間中心主義 (効率を追求するか、人間の幸福を優先するか)
6. データ駆動 vs 直感重視 (データに基づく判断を重視するか、直感を重視するか)
7. 健康最優先 vs QOL優先 (身体的健康を最優先するか、生活の質（QOL）を優先するか)
8. 科学的根拠 vs 個人の体感 (科学的エビデンスを重視するか、個人の体感を重視するか)
9. 予防原則 vs 自己責任原則 (予防的措置を重視するか、個人の自己責任を重視するか)
10. 平等主義 vs 能力主義 (全員に平等な機会を与えるか、能力に応じた配分をするか)
11. 個人の権利 vs 公共の安全 (個人の権利を優先するか、公共の安全を優先するか)
12. 現実主義 vs 理想主義 (現実的な解決策を優先するか、理想的なビジョンを追求するか)
13. 希望尊重 vs 現実認識 (相手の希望を尊重するか、現実的な問題を認識するか)
14. 自由恋愛 vs 社会規範 (自由な恋愛を尊重するか、社会規範に従うか)
15. 信頼基盤 vs 疑念対応 (相手への信頼を基盤とするか、疑念に対応するか)
16. キャリア投資 vs リスク回避 (キャリアへの投資を優先するか、リスクを回避するか)
17. 経済的自由 vs 社会貢献 (個人の経済的自由を優先するか、社会への貢献を優先するか)
18. 短期最適 vs 長期最適 (短期的な利益を優先するか、長期的な持続可能性を優先するか)
19. 規制強化 vs 市場自由 (規制を強化するか、市場の自由に任せるか)
20. 保護主義 vs 自己責任 (保護政策を推進するか、自己責任を重視するか)
21. 事前規制 vs 事後対処 (事前に規制するか、問題発生後に対処するか)

【出力形式】
必ず以下のJSON形式で出力してください：
{{
  "axis_id": 0-21の整数,
  "axis_left": "選択した軸の左側",
  "axis_right": "選択した軸の右側",
  "ai_a_stance": "トピックに対するAI_Aの具体的立場（axis_leftの視点から50-80字で明確に記述）",
  "ai_b_stance": "トピックに対するAI_Bの具体的立場（axis_rightの視点から50-80字で明確に記述）",
  "reasoning": "この軸を選んだ理由を50-80字で説明"
}}

【重要】
- **トピックが議論に適さない場合（挨拶、単語、質問、意味不明など）は、axis_id: 0を返してください**
- axis_id: 0の場合、axis_left/axis_right/ai_a_stance/ai_b_stance/reasoningは空文字列""でOKです
- 例: 「こんにちは」「今日の天気」「ありがとう」などは議論不可なのでaxis_id: 0

【ai_a_stance と ai_b_stance の生成ルール】
- **トピックに対する具体的な立場を明確に記述すること**（抽象的な軸の説明ではない）
- **2つの立場は必ず相反する内容にすること**（両方とも賛成や両方とも反対は禁止）
- **立場は議論の方向性を明確に定めるものであること**
- 例（トピック「AIによる雇用代替は良いことか？」+ 軸「効率最適化 vs 人間中心主義」）:
  - ai_a_stance: "AIは効率化により経済成長を促進するため積極的に導入すべき"
  - ai_b_stance: "AIは人間の雇用を奪い存在意義を脅かすため導入を慎重にすべき"

【注意】
- トピックの本質的な対立構造を最もよく表現する軸を選んでください
- reasoningでは、なぜこの軸が議論を深めるのに適しているか説明してください
- **議論可能なトピックかどうかを最初に判断してください**
- **ai_a_stanceとai_b_stanceは必ず相反する立場になるよう設定してください**
"""


def build_round1_prompt(topic: str, stance: str, opponent_stance: str) -> str:
    """
    Build prompt for Round 1 initial argument.

    Args:
        topic: Debate topic
        stance: This AI's stance (axis left or right)
        opponent_stance: Opponent AI's stance

    Returns:
        Prompt string requesting structured Round 1 argument with claim,
        rationale, and preemptive counter-argument.

    Example:
        >>> prompt = build_round1_prompt(
        ...     "AIによる雇用代替は良いことか？",
        ...     "効率最適化",
        ...     "人間中心主義"
        ... )
        >>> "claim" in prompt
        True
    """
    return f"""以下のトピックについて、あなたの立場から議論してください。

【トピック】
{topic}

【あなたの立場】
{stance}

【対立する立場】
{opponent_stance}

【Round 1の目的】
- あなたの立場からの初期主張を明確に提示する
- 論拠を3つ挙げ、主張を論理的に裏付ける
- 相手の反論を先読みし、先制的に反論する

【出力形式】
必ず以下のJSON形式で出力してください：
{{
  "claim": "あなたの立場からの主張を50-80字で明確に述べる",
  "rationale": [
    "論拠1: 主張を支える根拠を80-120字で説明",
    "論拠2: 主張を支える根拠を80-120字で説明",
    "論拠3: 主張を支える根拠を80-120字で説明"
  ],
  "preemptive_counter": "相手からの予想される反論に対する先制的反論を80-120字で述べる",
  "confidence_level": "high" または "low" (任意: 自信度が特に高い/低い場合のみ指定)
}}

【注意】
- 対立する立場を明確に意識し、あなたの立場を強く主張してください
- 論拠は具体的で説得力のあるものにしてください
- 重要なフレーズは<critical>タグで囲んでください（例: <critical>効率は経済成長の基盤</critical>）
- **confidence_levelは基本的に省略してください。出力しないのがデフォルトです。**
- **"high"は、論理的に完璧で相手の反論の余地がほぼなく絶対に勝てる自信がある場合のみ**
- **"low"は、論拠が弱く勝算が極めて低いと自覚している場合のみ**
- **普通の自信度なら confidence_level フィールド自体を出力しないでください**
"""


def build_round2_prompt(
    topic: str,
    stance: str,
    opponent_stance: str,
    opponent_round1: Dict[str, Any]
) -> str:
    """
    Build prompt for Round 2 counter-arguments.

    Args:
        topic: Debate topic
        stance: This AI's stance
        opponent_stance: Opponent AI's stance
        opponent_round1: Opponent's Round 1 data containing claim,
                        rationale, and preemptive_counter

    Returns:
        Prompt string requesting structured Round 2 counter-arguments
        and final statement.

    Example:
        >>> opponent_data = {
        ...     "claim": "効率最優先で経済成長を最大化すべき",
        ...     "rationale": ["論拠1", "論拠2", "論拠3"],
        ...     "preemptive_counter": "公平性は二の次でよい"
        ... }
        >>> prompt = build_round2_prompt(
        ...     "AIによる雇用代替は良いことか？",
        ...     "人間中心主義",
        ...     "効率最適化",
        ...     opponent_data
        ... )
        >>> "counter_arguments" in prompt
        True
    """
    return f"""以下のトピックについて、相手の主張に反論してください。

【トピック】
{topic}

【あなたの立場】
{stance}

【相手の立場】
{opponent_stance}

【相手のRound 1主張】
主張: {opponent_round1.get('claim', '')}

論拠:
{chr(10).join(f"- {r}" for r in opponent_round1.get('rationale', []))}

先制的反論:
{opponent_round1.get('preemptive_counter', '')}

【Round 2の目的】
- 相手の主張の弱点を3つ指摘し、反論する
- あなたの立場からの最終主張を提示する
- 議論を建設的な方向に導く

【出力形式】
必ず以下のJSON形式で出力してください：
{{
  "counters": [
    "反論1: 相手の主張の弱点を指摘し、60-100字で反論",
    "反論2: 相手の主張の弱点を指摘し、60-100字で反論",
    "反論3: 相手の主張の弱点を指摘し、60-100字で反論"
  ],
  "final_statement": "あなたの立場からの最終主張を100-150字で述べる（反論を踏まえた総括）",
  "confidence_level": "high" または "low" (任意: 自信度が特に高い/低い場合のみ指定)
}}

【注意】
- 相手の具体的な論拠に対して鋭く反論してください
- 反論は論理的で説得力のあるものにしてください
- final_statementでは、反論を踏まえてあなたの立場を再度強調してください
- 決定的な論点は<critical>タグで囲んでください（例: <critical>効率だけでは格差が拡大</critical>）
- **confidence_levelは基本的に省略してください。出力しないのがデフォルトです。**
- **"high"は、相手の論理を完全に論破でき絶対に勝てる自信がある場合のみ**
- **"low"は、反論が弱く勝算が極めて低いと自覚している場合のみ**
- **普通の自信度なら confidence_level フィールド自体を出力しないでください**
"""


def build_judgment_prompt(all_data: Dict[str, Any]) -> str:
    """
    Build prompt for final judgment and synthesis by Judge AI.

    Args:
        all_data: Dictionary containing all debate data:
            {
                "topic": str,
                "axis_left": str,
                "axis_right": str,
                "ai_a_round1": Dict (claim, rationale, preemptive_counter),
                "ai_a_round2": Dict (counter_arguments, final_statement),
                "ai_b_round1": Dict,
                "ai_b_round2": Dict
            }

    Returns:
        Prompt string requesting structured judgment with scores,
        break shot, reasoning, and synthesis.

    Evaluation criteria (requirements.md line 83-84):
    - Logic consistency: 40%
    - Sharpness of attack: 30%
    - Constructiveness: 30%

    Example:
        >>> data = {
        ...     "topic": "AIによる雇用代替は良いことか？",
        ...     "axis_left": "効率最適化",
        ...     "axis_right": "人間中心主義",
        ...     "ai_a_round1": {"claim": "...", "rationale": [...], "preemptive_counter": "..."},
        ...     "ai_a_round2": {"counter_arguments": [...], "final_statement": "..."},
        ...     "ai_b_round1": {"claim": "...", "rationale": [...], "preemptive_counter": "..."},
        ...     "ai_b_round2": {"counter_arguments": [...], "final_statement": "..."}
        ... }
        >>> prompt = build_judgment_prompt(data)
        >>> "論理的整合性" in prompt
        True
    """
    # Extract Round 1 text
    ai_a_r1_text = f"主張: {all_data['ai_a_round1'].get('claim', '')}\n"
    ai_a_r1_text += "論拠:\n"
    ai_a_r1_text += "\n".join(f"- {r}" for r in all_data['ai_a_round1'].get('rationale', []))
    ai_a_r1_text += f"\n先制的反論: {all_data['ai_a_round1'].get('preemptive_counter', '')}"

    ai_b_r1_text = f"主張: {all_data['ai_b_round1'].get('claim', '')}\n"
    ai_b_r1_text += "論拠:\n"
    ai_b_r1_text += "\n".join(f"- {r}" for r in all_data['ai_b_round1'].get('rationale', []))
    ai_b_r1_text += f"\n先制的反論: {all_data['ai_b_round1'].get('preemptive_counter', '')}"

    # Extract Round 2 text
    ai_a_r2_text = "反論:\n"
    ai_a_r2_text += "\n".join(f"- {c}" for c in all_data['ai_a_round2'].get('counters', []))
    ai_a_r2_text += f"\n最終主張: {all_data['ai_a_round2'].get('final_statement', '')}"

    ai_b_r2_text = "反論:\n"
    ai_b_r2_text += "\n".join(f"- {c}" for c in all_data['ai_b_round2'].get('counters', []))
    ai_b_r2_text += f"\n最終主張: {all_data['ai_b_round2'].get('final_statement', '')}"

    return f"""以下の議論を評価し、勝者を判定してください。

【議題】
{all_data['topic']}

【対立軸】
{all_data['axis_left']} vs {all_data['axis_right']}

【AI_A ({all_data['axis_left']})の主張】
Round 1:
{ai_a_r1_text}

Round 2:
{ai_a_r2_text}

【AI_B ({all_data['axis_right']})の主張】
Round 1:
{ai_b_r1_text}

Round 2:
{ai_b_r2_text}

【評価基準】
1. 論理的整合性（40%）: 主張と論拠の一貫性、論理の飛躍がないか
2. 攻撃の鋭さ（30%）: 相手の弱点を突く反論の鋭さ
3. 建設性（30%）: 実現可能性、建設的な提案

【出力形式】
必ず以下のJSON形式で出力してください：
{{
  "winner": "AI_A" または "AI_B",
  "scores": {{
    "ai_a": {{
      "logic": 0-10の整数,
      "attack": 0-10の整数,
      "construct": 0-10の整数,
      "total": 0-30の整数
    }},
    "ai_b": {{
      "logic": 0-10の整数,
      "attack": 0-10の整数,
      "construct": 0-10の整数,
      "total": 0-30の整数
    }}
  }},
  "break_shot": {{
    "ai": "AI_A" または "AI_B",
    "category": "LOGIC" | "ATTACK" | "CONSTRUCT",
    "score": 0-10の整数,
    "quote": "決定的発言を50字以内で引用"
  }},
  "reasoning": "判定理由を100字以内で説明",
  "synthesis": "両論を踏まえた建設的な結論を100字程度で記述"
}}

【注意】
- 必ず点差をつけてください（同点禁止）
- scoresのtotalは各カテゴリの合計（logic + attack + construct）
- **break_shotは必ずwinnerに指定したAIの発言から選んでください**（勝者側の最も決定的だった発言を選ぶ）
- **break_shotのaiフィールドは必ずwinnerと一致させてください**
- **break_shotのscoreは、該当AIの該当カテゴリのスコアと必ず一致させてください**（例: AI_AのLOGICをbreak_shotに選んだ場合、scoreはai_a.logicと同じ値にする）
- synthesisは対立を統合した「第三の道」を示してください（どちらかの主張をそのまま採用するのではなく、両方の視点を活かした新しい視点を提示）
"""
