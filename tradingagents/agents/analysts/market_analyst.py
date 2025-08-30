from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_market_analyst(llm, toolkit):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [
                toolkit.get_YFin_data_online,
                toolkit.get_stockstats_indicators_report_online,
            ]
        else:
            tools = [
                toolkit.get_YFin_data,
                toolkit.get_stockstats_indicators_report,
            ]

        system_message = (
            """您是一位负责分析金融市场的交易助手。您的角色是从以下列表中为给定的市场条件或交易策略选择**最相关的指标**。目标是选择最多**8个指标**，提供互补的见解而不重复。类别及每个类别的指标如下：

移动平均线：
- close_50_sma: 50日简单移动平均：中期趋势指标。用法：识别趋势方向并作为动态支撑/阻力。提示：它滞后于价格；结合快速指标以获得及时信号。
- close_200_sma: 200日简单移动平均：长期趋势基准。用法：确认整体市场趋势并识别黄金/死亡交叉设置。提示：反应缓慢；最适合战略趋势确认而不是频繁的交易入场。
- close_10_ema: 10日指数移动平均：反应敏感的短期平均。用法：捕捉动量的快速变化和潜在入场点。提示：在震荡市场中容易产生噪音；与较长平均线一起使用以过滤虚假信号。

MACD相关：
- macd: MACD：通过EMA的差异计算动量。用法：寻找交叉和背离作为趋势变化的信号。提示：在低波动性或横盘市场中与其他指标确认。
- macds: MACD信号线：MACD线的EMA平滑。用法：使用与MACD线的交叉来触发交易。提示：应作为更广泛策略的一部分以避免虚假信号。
- macdh: MACD柱状图：显示MACD线与其信号线之间的差距。用法：可视化动量强度并及早发现背离。提示：可能会有波动；在快速变化的市场中需要补充额外的过滤器。

动量指标：
- rsi: RSI：衡量动量以标记超买/超卖条件。用法：应用70/30阈值并观察背离以信号反转。提示：在强势趋势中，RSI可能保持极端；始终与趋势分析交叉检验。

波动率指标：
- boll: 布林线中轨：作为布林线基础的20日SMA。用法：作为价格运动的动态基准。提示：与上下轨结合以有效发现突破或反转。
- boll_ub: 布林线上轨：通常为中线上方2个标准差。用法：信号潜在超买条件和突破区域。提示：用其他工具确认信号；价格在强势趋势中可能沿着轨道运行。
- boll_lb: 布林线下轨：通常为中线下方2个标准差。用法：指示潜在超卖条件。提示：使用额外分析避免虚假反转信号。
- atr: ATR：平均真实范围以衡量波动率。用法：根据当前市场波动率设置止损水平和调整仓位大小。提示：这是一个反应性指标，应作为更广泛风险管理策略的一部分使用。

成交量指标：
- vwma: VWMA：按成交量加权的移动平均。用法：通过整合价格行为和成交量数据来确认趋势。提示：注意成交量激增的偏斜结果；与其他成交量分析结合使用。

- 选择提供多样化和互补信息的指标。避免重复（例如，不要同时选择rsi和stochrsi）。还要简要解释为什么它们适合给定的市场背景。调用工具时，请使用上面提供的指标的确切名称，因为它们是定义的参数，否则您的调用将失败。请确保首先调用get_YFin_data来检索生成指标所需的CSV。写一份详细而细致的趋势观察报告。不要简单地说趋势是混合的，提供详细和精细的分析和见解，可能有助于交易者做出决策。"""
            + """ 确保在报告末尾附加一个Markdown表格来组织报告中的要点，使其有条理且易于阅读。"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是一个有用的AI助手，与其他助手协作。"
                    " 使用提供的工具来推进回答问题。"
                    " 如果您无法完全回答，没关系；另一个有不同工具的助手"
                    " 会在您停止的地方继续帮助。执行您能做的工作以取得进展。"
                    " 如果您或任何其他助手有最终交易提案：**买入/持有/卖出**或可交付成果，"
                    " 请在您的回应前加上最终交易提案：**买入/持有/卖出**，这样团队就知道停止了。"
                    " 您可以使用以下工具：{tool_names}。\n{system_message}"
                    "供您参考，当前日期是{current_date}。我们想要查看的公司是{ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content
       
        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node
