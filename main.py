import os

from langchain.chat_models import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from typing import Dict, Optional
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

import chainlit as cl
from dotenv import load_dotenv

load_dotenv(dotenv_path='venv/.env')

REDIS_URL = os.getenv('REDIS_URL')


@cl.oauth_callback
def oauth_callback(
        provider_id: str,
        token: str,
        raw_user_data: Dict[str, str],
        default_user: cl.User,
) -> Optional[cl.User]:
    return default_user


PROMPT = '''

'''


@cl.on_chat_start
async def on_chat_start():
    model = AzureChatOpenAI(
        azure_deployment="gpt-4-1106",
        openai_api_version="2023-09-01-preview",
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You're an assistant who's good at {ability}"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )
    chain = prompt | model | StrOutputParser()
    runnable = RunnableWithMessageHistory(
        chain,
        lambda session_id: RedisChatMessageHistory(session_id, url=REDIS_URL),
        input_messages_key="question",
        history_messages_key="history",
    )
    cl.user_session.set("runnable", runnable)


@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable
    id = cl.user_session.get("id")
    msg = cl.Message(content="")

    async for chunk in runnable.astream(
            {"ability": "math", "question": message.content},
            config=RunnableConfig(callbacks=[cl.AsyncLangchainCallbackHandler()],
                                  configurable={"session_id": id})
    ):
        await msg.stream_token(chunk)

    await msg.send()
