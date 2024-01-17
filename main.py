import os

from langchain_openai import AzureChatOpenAI
from langchain.chains.openai_functions import create_openai_fn_runnable
from langchain_core.pydantic_v1 import BaseModel, Field, UUID4
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from typing import Dict, Optional, Tuple, Any
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from utils import CHAT_INFO_PROMPT, PROMPT, ChatInfo
import uuid
from datetime import datetime
import chainlit as cl
from dotenv import load_dotenv
import asyncpg

load_dotenv(dotenv_path='venv/.env')

REDIS_URL = os.getenv('REDIS_URL')
PGHOST = os.getenv('PGHOST')
PGUSER = os.getenv('PGUSER')
PGPORT = os.getenv('PGPORT')
PGDATABASE = os.getenv('PGDATABASE')
PGPASSWORD = os.getenv('PGPASSWORD')


@cl.oauth_callback
def oauth_callback(
        provider_id: str,
        token: str,
        raw_user_data: Dict[str, str],
        default_user: cl.User,
) -> Optional[cl.User]:
    return default_user


@cl.on_chat_start
async def on_chat_start():
    model = AzureChatOpenAI(
        azure_deployment="gpt-4-1106",
        openai_api_version="2023-09-01-preview",
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", PROMPT),
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
    user_id = cl.user_session.get("id")
    end, transcript = cl.user_session.get('end'), cl.user_session.get('transcript')
    if end:
        end.remove()
    if transcript:
        transcript.remove()
    end = cl.Action(name="End chat", value="End", description="End chat")
    transcript = cl.Action(name="Transcript", value="transcript", description="Transcript")
    actions = [
        end, transcript
    ]
    msg = cl.Message(content="", actions=actions)
    if message.content in ['\\transcript', '\\t']:
        await cl.Message(content=runnable.get_session_history(user_id)).send()
    else:
        try:
            async for chunk in runnable.astream(
                    {"question": message.content},
                    config=RunnableConfig(callbacks=[cl.AsyncLangchainCallbackHandler()],
                                          configurable={"session_id": user_id})
            ):
                await msg.stream_token(chunk)

            await msg.send()
        except:
            if "'self_harm': {'filtered': True, 'severity': 'medium'}" or \
                    "'self_harm': {'filtered': True, 'severity': 'high'}" in message.content:
                await cl.Message(
                    content="It looks like your message mentions self-harm. If you, or someone you know, is at risk or "
                            "is experiencing self-harm, please contact the emergency services immediately.").send()
            elif "'violence': {'filtered': True, 'severity': 'medium'}" or \
                    "'violence': {'filtered': True, 'severity': 'high'}" in message.content:
                await cl.Message(
                    content="It looks like your message mentions violence. If you, or someone you know, is at risk or "
                            "is experiencing violence, please contact the emergency services immediately.").send()
            else:
                await cl.Message(
                    content="I'm sorry, but your message has been flagged as containing harmful content by our content "
                            "moderation policy. Please re-write your message and try again.").send()

    cl.user_session.set('end', end)
    cl.user_session.set('transcript', transcript)


@cl.action_callback("End chat")
async def on_action_end(action: cl.Action):
    on_chat_end()
    await cl.Message(content="Chat ended!").send()
    await action.remove()


@cl.action_callback("Transcript")
async def on_action_transcript(action: cl.Action):
    runnable = cl.user_session.get("runnable")
    user_id = cl.user_session.get("id")
    await cl.Message(content=runnable.get_session_history(user_id)).send()
    await action.remove()


@cl.on_chat_end
async def on_chat_end():
    session_id = cl.user_session.get('id')
    if str(cl.user_session.get("runnable").get_session_history(session_id)) == "":
        pass
    else:
        await cl.Message(content="Processing...").send()
        conn = await init_db()
        insert_query, values = await chat_records()
        await conn.execute(insert_query, *values)
        # Close the connection
        await conn.close()
        await cl.Message(content="Chat processed and saved!").send()


async def init_db():
    cnx = await asyncpg.connect(user=PGUSER, password=PGPASSWORD, host=PGHOST, port=PGPORT, database=PGDATABASE)
    return cnx


async def chat_records():
    session_id = cl.user_session.get('id')
    name = cl.user_session.get('user')
    email_or_phone_number = cl.user_session.get('user')
    datetime_of_chat = datetime.now()
    chat_duration = 30
    chat_transcript = cl.user_session.get("runnable").get_session_history(session_id)
    chat_info = await get_chat_info(session_id)
    insert_query: str = """
        INSERT INTO ChatRecords (
            SessionID, Name, EmailOrPhoneNumber, DateTimeOfChat, ChatDuration, ChatTranscript,
            ChatSummary, Category, Severity, SocialCareEligibility, SuggestedCourseOfAction,
            NextSteps, ContactRequest, Status
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
        );
    """

    values = (
        session_id, name.identifier, email_or_phone_number.identifier, datetime_of_chat, chat_duration,
        str(chat_transcript), chat_info.chat_summary, chat_info.category, chat_info.severity,
        chat_info.social_care_eligibility, chat_info.suggested_course_of_action, chat_info.next_steps,
        chat_info.contact_request, chat_info.status
    )

    return insert_query, values


async def get_chat_info(session_id: UUID4):
    llm = AzureChatOpenAI(azure_deployment="gpt-4-1106",
                          openai_api_version="2023-09-01-preview")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CHAT_INFO_PROMPT),
            ("human", "Make calls to the relevant function to record the entities in the "
                      "following transcript: {input}"),
            ("human", "Tip: Make sure to answer in the correct format"),
        ]
    )
    transcript = cl.user_session.get("runnable").get_session_history(session_id)
    chain = create_openai_fn_runnable([ChatInfo], llm, prompt)
    return await chain.ainvoke({"input": transcript})
