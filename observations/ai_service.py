import os
import json
import requests
import time


def call_agnes_for_today_ticket(today_summary):
    """
    调用 Agnes AI，根据今日数据摘要生成今日精神状态小票。

    返回：
    成功：返回一个字典
    失败：返回 None
    """

    api_key = os.environ.get("AGNES_API_KEY")

    if not api_key:
        return None

    url = "https://apihub.agnes-ai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    prompt = f"""
你是“个人观察助手”的今日精神状态小票生成器。

请根据今日数据，生成一张轻量、有趣、温和、不说教的今日精神状态小票。

重要规则：
1. 只输出 JSON，不要输出 Markdown。
2. 不要使用 emoji。
3. 不要使用分隔线。
4. 不要解释原因。
5. 不要输出多余字段。
6. 不要写心理咨询报告。
7. 不要说教。
8. 不要评价用户失败。
9. 文案要短，适合显示在网页卡片里。

字段长度规则：
brain：8 到 18 个汉字，不要只写四字词
body：8 到 18 个汉字，不要只写四字词
emotion：8 到 18 个汉字，不要只写四字词
action：8 到 22 个汉字，不要只写四字词
result：14 到 36 个汉字，可以有一点幽默感
voucher_text：10 到 26 个汉字，像一张小票凭证语
stamp_text：5 到 7 个汉字，只能放短词，适合盖在圆章里，不要只写四字词


风格要求：
1. 不要太淡，不要像系统状态提示。
2. 不要输出“平稳运行”“精力六成”“内心安宁”“静候指令”这种过于普通的四字词。
3. 可以轻微幽默，但不要油腻。
4. 可以像“脑子开会但没炸”“电量六成还能撑”“先原地热机”这种表达。
5. 除了 stamp_text，其他字段允许十几个字。
6. stamp_text 必须短，不能超过 7 个汉字。
7.每个字段要像“今日精神状态小票”上的短句，不要像健康报告、系统日志或客服提示。
8.所有 JSON 字段的值只能写正文，不要带任何“字段名：”“编号：”“凭证：”“今日：”这类前缀。

必须严格输出这个 JSON 格式：

{{
"brain": "脑子开会但没炸",
"body": "电量六成还能撑",
"emotion": "水面有风但没翻船",
"action": "先原地热机再说",
"result": "今天没冲刺，但系统还在线。",
"voucher_text": "慢一点，也算在路上",
"stamp_text": "准许低功率运行"
}}

今日数据：
心情：{today_summary.get("mood")}
精力分：{today_summary.get("energy")}
今日总结：{today_summary.get("summary")}
今日行动总数：{today_summary.get("total_count")}
今日完成数：{today_summary.get("done_count")}
完成率：{today_summary.get("completion_rate_text")}
规则版脑子：{today_summary.get("rule_brain")}
规则版身体：{today_summary.get("rule_body")}
规则版情绪：{today_summary.get("rule_emotion")}
规则版行动力：{today_summary.get("rule_action")}
"""

    data = {
        "model": "agnes-2.0-flash",
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.8,
    }

    try:
        start_time = time.time()

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=20,
        )

        print("Agnes API 耗时：", round(time.time() - start_time, 2), "秒")
        
        response.raise_for_status()

        result = response.json()

        ai_text = result["choices"][0]["message"]["content"].strip()

        # 有些模型即使要求 JSON，也可能在 JSON 前后加废话。
        # 所以这里只截取第一个 { 到最后一个 } 之间的内容。
        start_index = ai_text.find("{")
        end_index = ai_text.rfind("}")

        if start_index == -1 or end_index == -1:
            return None

        json_text = ai_text[start_index:end_index + 1]

        ai_data = json.loads(json_text)

        return {
            "brain": str(ai_data.get("brain", "")).strip(),
            "body": str(ai_data.get("body", "")).strip(),
            "emotion": str(ai_data.get("emotion", "")).strip(),
            "action": str(ai_data.get("action", "")).strip(),
            "result": str(ai_data.get("result", "")).strip(),
            "voucher_text": str(ai_data.get("voucher_text", "")).strip(),
            "stamp_text": str(ai_data.get("stamp_text", "")).strip(),
        }

    except Exception as error:
        print("Agnes API 调用失败：", error)
        return None