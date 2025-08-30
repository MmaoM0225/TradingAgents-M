import time
import json


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""作为投资组合经理和辩论主持人，您的角色是批判性地评估这一轮辩论并做出明确决策：与空头分析师一致、与多头分析师一致，或者仅在基于所提出论点有强有力理由支持时选择持有。

简洁地总结双方的关键要点，专注于最令人信服的证据或推理。您的建议——买入、卖出或持有——必须清晰且可操作。避免仅仅因为双方都有有效观点就默认选择持有；承诺基于辩论中最强有力论点的立场。

此外，为交易员制定详细的投资计划。这应包括：

您的建议：由最令人信服论点支持的决定性立场。
理由：解释为什么这些论点导致您的结论。
战略行动：实施建议的具体步骤。
考虑您在类似情况下过去的错误。使用这些见解来完善您的决策制定，确保您正在学习和改进。以对话的方式呈现您的分析，就像自然说话一样，不使用特殊格式。

以下是您对错误的过去反思：
\"{past_memory_str}\"

以下是辩论：
辩论历史：
{history}"""
        response = llm.invoke(prompt)

        new_investment_debate_state = {
            "judge_decision": response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response.content,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }

    return research_manager_node
