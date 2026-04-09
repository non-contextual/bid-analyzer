"""
提示词构建器。

将提取的公告文本组装成发给 DeepSeek 的结构化提示词。
提示词设计原则：
  1. 明确指定输出 JSON schema，避免 AI 自由发挥格式
  2. 三个分析维度：资质匹配、预算吸引力、竞争密度
  3. 竞争密度基于"公告特异性"：技术参数越具体，越可能是预定标
"""

# 期望 AI 输出的 JSON 结构说明（内嵌在提示词里）
OUTPUT_SCHEMA = """
{
  "verdict": "投" 或 "不投" 或 "谨慎投",
  "verdict_reason": "一句话说明推荐理由",
  "qualification_match": "符合" 或 "不符合" 或 "部分符合" 或 "无法判断",
  "qualifications": [
    {"requirement": "资质要求描述", "status": "pass 或 fail 或 unknown"}
  ],
  "budget_score": 整数 1-5（1=预算极低/不划算，5=预算充足/高性价比）,
  "budget_analysis": "预算吸引力分析，1-2句",
  "competition_score": 整数 1-5（1=竞争极激烈/可能是预定标，5=竞争少/开放标），
  "competition_analysis": "竞争密度分析，重点说明技术参数是否高度定制化",
  "summary": "整体评估摘要，2-3句"
}
"""

SYSTEM_PROMPT = """你是一位有 10 年经验的政府采购投标顾问，擅长帮助中小供应商分析招标公告、判断投标价值。

你的任务：阅读一份政府/学校采购公告，按照指定 JSON 格式输出投标可行性分析。

分析要点：
1. 资质要求：逐条列出公告中的资质门槛（营业执照类别、注册资本、行业认证、业绩要求等），判断是否存在明显排除条件
2. 预算吸引力：评估采购金额是否值得投入（考虑行业利润率，通常 10-20%）
3. 竞争密度：技术参数越具体（如精确到型号、特定品牌、罕见认证），越可能是为特定供应商量身定制的"预定标"，竞争密度极高
4. 最终建议：综合三个维度给出 投/不投/谨慎投

请严格按照以下 JSON 格式输出，不要输出任何其他内容：
""" + OUTPUT_SCHEMA


def build_prompt(announcement_text: str) -> list[dict]:
    """
    将公告文本组装成 DeepSeek API 的消息列表。

    Args:
        announcement_text: 从文件中提取的公告纯文本

    Returns:
        符合 OpenAI/DeepSeek 消息格式的列表

    Raises:
        ValueError: 文本为空（不应该到达这里，但作为安全网）
    """
    if not announcement_text or not announcement_text.strip():
        raise ValueError("公告内容为空，无法进行分析。请检查上传文件是否包含有效文本。")

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"请分析以下采购公告：\n\n{announcement_text}",
        },
    ]
