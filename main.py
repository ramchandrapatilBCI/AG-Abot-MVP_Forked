import logging
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
from chainlit.socket import connect, disconnect
import uuid

load_dotenv(dotenv_path='venv/.env')

REDIS_URL = os.getenv('REDIS_URL')
PGHOST = os.getenv('PGHOST')
PGUSER = os.getenv('PGUSER')
PGPORT = os.getenv('PGPORT')
PGDATABASE = os.getenv('PGDATABASE')
PGPASSWORD = os.getenv('PGPASSWORD')
INSERT_QUERY: str = """
    INSERT INTO ChatRecords (
        SessionID, Name, EmailOrPhoneNumber, DateTimeOfChat, ChatDuration, ChatTranscript,
        ChatSummary, Category, Severity, SocialCareEligibility, SuggestedCourseOfAction,
        NextSteps, ContactRequest, Status
    ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
    );
"""
DB_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", CHAT_INFO_PROMPT),
        ("human", "Make calls to the relevant function to record the entities in the "
                  "following transcript: {input}"),
        ("human", "Tip: Make sure to answer in the correct format"),
    ]
)
# Add logging mechanism
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
    """
    This function initializes the chatbot and sets up the conversation flow.

    Parameters:
        None

    Returns:
        None

    Raises:
        None
    """
    logger.info("Chat started")
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

    try:
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
    except Exception as e:
        logging.error(f"An error occurred in on_chat_start: {str(e)}")


@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable
    user_id = cl.user_session.get("id")
    end, transcript = cl.user_session.get('end'), cl.user_session.get('transcript')
    if end:
        await end.remove()
    if transcript:
        await transcript.remove()
    end = cl.Action(name="End chat", value="End", description="End chat")
    transcript = cl.Action(name="Transcript", value="transcript", description="Transcript")
    actions = [
        end, transcript
    ]
    msg = cl.Message(content="", actions=actions)

    content_actions = {
        '\\transcript': cl.Message(content=runnable.get_session_history(user_id)).send,
        '\\t': cl.Message(content=runnable.get_session_history(user_id)).send
    }
    if message.content in content_actions:
        await content_actions[message.content]()
    else:
        try:
            async for chunk in runnable.astream(
                    {"question": message.content},
                    config=RunnableConfig(callbacks=[cl.AsyncLangchainCallbackHandler()],
                                          configurable={"session_id": user_id})
            ):
                await msg.stream_token(chunk)

            await msg.send()
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            harmful_content_responses = {
                "'self_harm': {'filtered': True, 'severity': 'medium'}": cl.Message(
                    content="It looks like your message mentions self-harm. If you, or someone you know, is at risk or "
                            "is experiencing self-harm, please contact the emergency services immediately.",
                    actions=[end, transcript]
                ),
                "'self_harm': {'filtered': True, 'severity': 'high'}": cl.Message(
                    content="It looks like your message mentions self-harm. If you, or someone you know, is at risk or "
                            "is experiencing self-harm, please contact the emergency services immediately.",
                    actions=[end, transcript]
                ),
                "'violence': {'filtered': True, 'severity': 'medium'}": cl.Message(
                    content="It looks like your message mentions violence. If you, or someone you know, is at risk or "
                            "is experiencing violence, please contact the emergency services immediately.",
                    actions=[end, transcript]
                ),
                "'violence': {'filtered': True, 'severity': 'high'}": cl.Message(
                    content="It looks like your message mentions violence. If you, or someone you know, is at risk or "
                            "is experiencing violence, please contact the emergency services immediately.",
                    actions=[end, transcript]
                )
            }
            for harmful_content, response in harmful_content_responses.items():
                if harmful_content in message.content:
                    await response.send()
                    break
            else:
                await cl.Message(
                    content="I'm sorry, but your message has been flagged as containing harmful content by our content "
                            "moderation policy. Please re-write your message and try again.",
                    actions=actions
                ).send()

    cl.user_session.set('end', end)
    cl.user_session.set('transcript', transcript)


@cl.action_callback("End chat")
async def on_action_end(action: cl.Action):
    """
    This function is called when the "End chat" action is triggered.
    It ends the chat, sends a message indicating the chat has ended, and removes the action.
    """
    try:
        await on_chat_end()
        await cl.Message(content=cl.user_session.get("id")).send()
        await disconnect(cl.user_session.get("id"), force_clear=True)
        await connect(uuid.uuid4())
        await cl.Message(content=cl.user_session.get("id")).send()
        await cl.Message(content="Chat ended!").send()
        if action is not None:
            await action.remove()
    except Exception as e:
        logger.error(f"Error in on_action_end: {e}")


@cl.action_callback("Transcript")
async def on_action_transcript(action: cl.Action):

    runnable = cl.user_session.get("runnable")
    user_id = cl.user_session.get("id")

    if runnable is not None and user_id is not None:
        try:
            session_history = runnable.get_session_history(user_id)
            if session_history is not None:
                await cl.Message(content=session_history).send()
        except Exception as e:
            logging.error(f"Error occurred while getting session history: {e}")
    else:
        logging.warning("runnable or user_id is None")

    try:
        await action.remove()
    except Exception as e:
        logging.error(f"Error occurred while removing action: {e}")


@cl.on_chat_end
async def on_chat_end():
    """
    This function is triggered when a chat ends.
    It processes the chat history and saves it to the database.
    """
    session_id = cl.user_session.get('id')
    if session_id is None:
        raise ValueError("Invalid session_id")

    session_history = cl.user_session.get("runnable").get_session_history(session_id)
    if session_history:
        await cl.Message(content="Processing...").send()

        conn = await init_db()
        if conn is None:
            raise ConnectionError("Failed to connect to the database.")

        try:
            async with conn.transaction():
                values = await chat_records()
                await conn.execute(INSERT_QUERY, *values)
        except ValueError as e:
            # Handle the `ValueError` raised by `chat_records` and provide a meaningful error message
            logger.error(f"Error processing chat: {e}")
        except asyncpg.PostgresError as e:
            # Handle the exception here, such as logging the error or providing a meaningful error message
            logger.error(f"Error executing SQL query: {e}")
        finally:
            # Close the connection
            await conn.close()

        await cl.Message(content="Chat processed and saved!").send()


async def init_db():
    try:
        cnx = await asyncpg.connect(user=PGUSER, password=PGPASSWORD, host=PGHOST, port=PGPORT, database=PGDATABASE,
                                    ssl=True)
        if not cnx.is_closed():
            return cnx
        else:
            raise ConnectionError("Failed to connect to the database.")
    except asyncpg.PostgresError as e:
        # Handle the exception here, such as logging the error or providing a meaningful error message
        logging.error(f"Error connecting to the database: {e}")
        raise ConnectionError("Failed to connect to the database.")


async def chat_records():
    session_id = cl.user_session.get('id')
    user = cl.user_session.get('user')
    if user is None:
        raise ValueError("Invalid user")
    name = user
    email_or_phone_number = user
    datetime_of_chat = datetime.utcnow()
    chat_duration = 30
    chat_transcript = cl.user_session.get("runnable").get_session_history(session_id)
    chat_info = await get_chat_info(session_id)

    if chat_info is None:
        # Handle the case when `get_chat_info(session_id)` returns None
        raise ValueError("Invalid chat_info")

    attribute_defaults = {
        'chat_summary': None,
        'category': None,
        'severity': None,
        'social_care_eligibility': None,
        'suggested_course_of_action': None,
        'next_steps': None,
        'contact_request': None,
        'status': None
    }
    attribute_values = {attr: getattr(chat_info, attr, attribute_defaults[attr]) for attr in attribute_defaults}

    chat_summary = attribute_values['chat_summary']
    category = attribute_values['category']
    severity = attribute_values['severity']
    social_care_eligibility = attribute_values['social_care_eligibility']
    suggested_course_of_action = attribute_values['suggested_course_of_action']
    next_steps = attribute_values['next_steps']
    contact_request = attribute_values['contact_request']
    status = attribute_values['status']

    if not all([chat_summary, category, severity, suggested_course_of_action,
                next_steps, contact_request, status]):
        raise ValueError("Invalid values for chat_summary, category, severity, "
                         "suggested_course_of_action, next_steps, contact_request, or status")

    if isinstance(chat_transcript, str):
        chat_transcript_str = chat_transcript
    else:
        chat_transcript_str = str(chat_transcript)

    values = (
        session_id, name.identifier, email_or_phone_number.identifier, datetime_of_chat, chat_duration,
        chat_transcript_str, chat_summary, category, severity, social_care_eligibility,
        suggested_course_of_action, next_steps, contact_request, status
    )

    return values


async def get_chat_info(session_id: UUID4):
    """
    Retrieves chat information based on the given session ID.

    Args:
        session_id (UUID4): The ID of the session.

    Returns:
        The chat information.

    Raises:
        ValueError: If the session_id is invalid.
        RuntimeError: If unable to initialize the summarizer module.
    """
    if not isinstance(session_id, UUID4):
        raise ValueError("Invalid session_id")

    try:
        llm = AzureChatOpenAI(azure_deployment="gpt-4-32k-0613",
                              openai_api_version="2023-09-01-preview")
        chain = create_openai_fn_runnable([ChatInfo], llm, DB_PROMPT)
        return await chain.ainvoke({"input": cl.user_session.get("runnable").get_session_history(session_id)})
    except Exception as e:
        raise RuntimeError('Unable to initialise summariser module.')
