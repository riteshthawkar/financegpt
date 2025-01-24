import warnings
warnings.filterwarnings("ignore", module="custom_tools")

from openai import OpenAI
import openai
import requests
import json
import inspect
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=100)

import os
from dotenv import load_dotenv

# from langchain import hub

load_dotenv(".env")
USER_AGENT = os.getenv("USER_AGENT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


client = OpenAI(
    api_key=OPENAI_API_KEY  
)



from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.agents import AgentExecutor, create_tool_calling_agent , create_react_agent
from langchain_core.prompts import ChatPromptTemplate

from custom_tools import *

model = ChatOpenAI(model="gpt-4o")
memory = InMemoryChatMessageHistory(session_id="test_session_id")

tools=[get_financial_news,WikipediaQueryRun(api_wrapper=api_wrapper),get_stock_price,get_price_by_date,get_price_history,get_52_week_high_low,get_market_trends,
       
       compare_stock_performance,daily_performance,weekly_performance,sector_performance,recommend_stocks_for_long_term,

       check_growth_potential,get_top_dividend_stocks,assess_risk,get_premarket_price,get_present_date
       
       
       ]

# print(tools[15])

# tools = [
#     func for name, func in inspect.getmembers(custom_tools, inspect.isfunction)
# ]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        # First put the history
        ("placeholder", "{chat_history}"),
        # Then the new input
        ("human", "{input}"),
        # Finally the scratchpad
        ("placeholder", "{agent_scratchpad}"),
    ]
)


agent = create_tool_calling_agent(model, tools,prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools,verbose=False,handle_parsing_errors=True)



def chat(query:str) :

    agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    lambda session_id: memory,
    input_messages_key="input",
    history_messages_key="chat_history",
)

    config = {"configurable": {"session_id": "test_session_id"}}

    response = agent_with_chat_history.invoke(
        {"input": query}, config
    )
    return response['output']





