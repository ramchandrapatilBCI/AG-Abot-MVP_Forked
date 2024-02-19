import logging
import os

from datetime import timezone
from langchain_openai import AzureChatOpenAI
from langchain.chains.openai_functions import create_openai_fn_runnable
from langchain_core.pydantic_v1 import BaseModel, Field, UUID4
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from chainlit import Message
import chainlit as cl
from utils import CHAT_INFO_PROMPT, PROMPT, ChatInfo
from datetime import datetime
from typing import Dict, Optional, Tuple, Any
import asyncpg

from dotenv import load_dotenv

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
        NextSteps, ContactRequest, Status, Rating, Feedback
    ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
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
    """
    Perform oauth callback for the given provider and token.
    Args:
        provider_id (str): The ID of the OAuth provider.
        token (str): The token for OAuth authentication.
        raw_user_data (Dict[str, str]): The raw user data received from the provider.
        default_user (cl.User): The default user to be returned if the OAuth process fails.
    Returns:
        Optional[cl.User]: The user object if the OAuth process is successful, else None.
    """
    return default_user


@cl.on_chat_start
async def on_chat_start() -> None:
    """
    Triggered when a chat starts.
    """
    try:
        # Initialize AzureChatOpenAI model
        model = AzureChatOpenAI(
            azure_deployment="gpt-4-1106",
            openai_api_version="2023-09-01-preview",
        )

        # Create a prompt from system and human messages
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", PROMPT),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )

        # Set up a chain of operations
        chain = prompt | model | StrOutputParser()

        # Set the runnable for the user session
        runnable = RunnableWithMessageHistory(
            chain,
            lambda session_id: RedisChatMessageHistory(session_id, url=REDIS_URL),
            input_messages_key="question",
            history_messages_key="history",
        )

        # Set the user session runnable
        cl.user_session.set("runnable", runnable)
    except Exception as e:
        # Log errors
        logging.error(f"An error occurred in on_chat_start: {str(e)}")


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """
    Asynchronous function that handles incoming messages and performs various actions based on the message content.
    Takes a `message` parameter of type `cl.Message`. Does not return anything.
    """
    # Get the user's runnable object and user id from the user session
    runnable = cl.user_session.get("runnable")  # type: Runnable
    user_id = cl.user_session.get("id")

    # Get the transcript action from the user session and remove it if it exists
    transcript: cl.Action = cl.user_session.get('transcript')
    if transcript:
        await transcript.remove()

    # Create actions for ratings and transcript
    transcript = cl.Action(name="Transcript", value="transcript", description="Transcript")
    rating_actions = [
        cl.Action(
            name="rating", value=str(i), label=str(i), description=str(i)
        )
        for i in range(1, 6)
    ]
    # Set up rating and transcript actions in the user session
    actions = [transcript]
    cl.user_session.set('rating_actions', rating_actions)
    cl.user_session.set('transcript', transcript)

    # Create a message with the transcript action
    msg: Message = cl.Message(content="", actions=actions)

    # Create content actions for specific message content
    content_actions = {
        '\\transcript': runnable.get_session_history(user_id),
        '\\t': runnable.get_session_history(user_id)
    }
    # Execute content actions based on message content
    if message.content in content_actions:
        await cl.Message(content=content_actions[message.content]).send()
    else:
        try:
            # Process the message content using the user's runnable object
            async for chunk in runnable.astream(
                    {"question": message.content},
                    config=RunnableConfig(callbacks=[cl.AsyncLangchainCallbackHandler()],
                                          configurable={"session_id": user_id})
            ):
                if '<END>' in msg.content[-5:]:
                    # Remove the '<END>' token from the message content and update the message
                    msg.content = msg.content[:-5]
                    await msg.update()
                    msg.actions = rating_actions
                    break
                await msg.stream_token(chunk)

            # Send the processed message
            await msg.send()
        except Exception as e:
            # Handle any exceptions and send appropriate content responses
            logger.error(f"An error occurred: {str(e)}")
            content_responses: dict[str, Message] = {
                "'self_harm': {'filtered': True, 'severity': 'medium'}": cl.Message(
                    content="It looks like your message mentions self-harm. If you, or someone you know, is at risk or "
                            "is experiencing self-harm, please contact the emergency services immediately.",
                    actions=actions
                ),
                "'self_harm': {'filtered': True, 'severity': 'high'}": cl.Message(
                    content="It looks like your message mentions self-harm. If you, or someone you know, is at risk or "
                            "is experiencing self-harm, please contact the emergency services immediately.",
                    actions=actions
                ),
                "'violence': {'filtered': True, 'severity': 'medium'}": cl.Message(
                    content="It looks like your message mentions violence. If you, or someone you know, is at risk or "
                            "is experiencing violence, please contact the emergency services immediately.",
                    actions=actions
                ),
                "'violence': {'filtered': True, 'severity': 'high'}": cl.Message(
                    content="It looks like your message mentions violence. If you, or someone you know, is at risk or "
                            "is experiencing violence, please contact the emergency services immediately.",
                    actions=actions
                )
            }

            # Check for harmful content in the message and send appropriate responses
            for harmful_content, response in content_responses.items():
                if harmful_content in message.content:
                    await response.send()
                    break
            else:
                # Send a default message if no harmful content is detected
                await cl.Message(
                    content="I'm sorry, but your message has been flagged as containing harmful content by our content "
                            "moderation policy. Please re-write your message and try again.",
                    actions=actions
                ).send()


@cl.action_callback("Transcript")
async def on_action_transcript(action: cl.Action):
    """
    Handles the "Transcript" action asynchronously.
    Retrieves the user's runnable and user_id from the user session,
    then gets and sends the session history as a message.
    If an error occurs, logs the error message.
    Removes the action after handling.
    """
    # Retrieve user's runnable and user_id from the user session
    runnable = cl.user_session.get("runnable")
    user_id = cl.user_session.get("id")

    if runnable and user_id:
        try:
            if session_history := runnable.get_session_history(user_id):
                await cl.Message(content=session_history).send()
        except Exception as e:
            # Log error message if an error occurs
            logging.error(f"Error occurred while getting session history: {e}")
    else:
        # Log a warning if runnable or user_id is None
        logging.warning("runnable or user_id is None")

    try:
        # Remove the action after handling
        await action.remove()
    except Exception as e:
        # Log error message if an error occurs
        logging.error(f"Error occurred while removing action: {e}")


@cl.action_callback("rating")
async def rating(action: cl.Action):
    """
    Handle the rating action by setting the rating and collecting feedback.
    """
    rating_actions = cl.user_session.get('rating_actions')
    transcript: cl.Action = cl.user_session.get('transcript')

    # Remove all previous rating actions
    for rating_action in rating_actions:
        await rating_action.remove()

    # Remove the transcript if it exists
    if transcript:
        await transcript.remove()

    # Set the rating value in the user session
    cl.user_session.set('rating', action.value)

    # Ask the user for feedback and store it in the user session
    feedback = await cl.AskUserMessage(
        content="Please enter your feedback...",
        timeout=600,
        disable_feedback=True
    ).send()
    transcript = cl.Action(
        name="Transcript",
        value="transcript",
        description="Transcript"
    )
    if feedback:
        cl.user_session.set('feedback', feedback['output'])


        # Send a thank you message and provide the option to view the transcript
        await cl.Message(
            content="Thank you for your feedback!",
            actions=[transcript]
        ).send()
    else:
        await cl.Message(
            content="No feedback provided",
            actions=[transcript]
        ).send()


@cl.on_chat_end
async def on_chat_end():
    """
    Triggered when a chat ends.
    Processes the chat history and saves it to the database.
    """

    # Get the session ID
    session_id = cl.user_session.get('id')
    if session_id is None:
        raise ValueError("Invalid session_id")

    if session_history := cl.user_session.get("runnable").get_session_history(
        session_id
    ):
        # await cl.Message(content="Processing...").send()

        try:
            # Initialize the database connection
            conn = await init_db()
            if conn is None:
                raise ConnectionError("Failed to connect to the database.")
            # Start a transaction and insert chat records
            async with conn.transaction():
                values = await chat_records()
                await conn.execute(INSERT_QUERY, *values)
        except (ValueError, asyncpg.PostgresError) as e:
            logger.error(f"Error processing chat: {e}")
        finally:
            # Close the database connection
            await conn.close()

        # Send a message indicating the chat has been processed and saved
        # await cl.Message(content="Chat processed and saved!").send()


async def init_db():
    """
    Asynchronously initializes the database connection.

    Attempts to establish a connection to the database using the provided credentials.
    If successful, returns the connection object. If the connection fails, raises a ConnectionError.

    Returns:
        asyncpg.Connection: The database connection object.

    Raises:
        ConnectionError: If the connection to the database fails.
    """
    try:
        # Establish a connection to the database
        return await asyncpg.connect(
            user=PGUSER, password=PGPASSWORD, host=PGHOST, port=PGPORT, database=PGDATABASE, ssl=True
        )
    except asyncpg.PostgresError as e:
        # Handle the exception and raise a ConnectionError
        logging.exception(f"Error connecting to the database: {e}")
        raise ConnectionError("Failed to connect to the database.") from e


async def chat_records() -> tuple:
    """
    Asynchronous function to retrieve chat records and related information.
    Returns:
        tuple: A tuple containing session_id, name identifier, email or phone number
        identifier, datetime of chat, chat duration, chat transcript, chat summary,
        category, severity, social care eligibility, suggested course of action,
        next steps, contact request, and status.
    """
    session_id = cl.user_session.get('id')
    user = cl.user_session.get('user')
    if user is None:
        raise ValueError("Invalid user")
    name = user
    email_or_phone_number = user
    datetime_of_chat: datetime = datetime.now(timezone.utc)
    chat_duration = 30
    chat_transcript = cl.user_session.get("runnable").get_session_history(session_id)
    chat_info = await get_chat_info(session_id)

    if chat_info or chat_transcript is None:
        # Handle the case when `get_chat_info(session_id)` returns None
        raise ValueError("Invalid chat_info and chat transcript")

    attribute_defaults: dict = {
        'chat_summary': None,
        'category': None,
        'severity': None,
        'social_care_eligibility': None,
        'suggested_course_of_action': None,
        'next_steps': None,
        'contact_request': None,
        'status': None
    }
    attribute_values: dict = {attr: getattr(chat_info, attr, attribute_defaults[attr]) for attr in attribute_defaults}

    chat_summary = attribute_values['chat_summary']
    category = attribute_values['category']
    severity = attribute_values['severity']
    social_care_eligibility = attribute_values['social_care_eligibility']
    suggested_course_of_action = attribute_values['suggested_course_of_action']
    next_steps = attribute_values['next_steps']
    contact_request = attribute_values['contact_request']
    status = attribute_values['status']
    feedback = cl.user_session.get('feedback')
    final_rating = cl.user_session.get('rating')

    if not all([chat_summary, category, severity, suggested_course_of_action,
                next_steps, contact_request, status]):
        raise ValueError("Invalid values for chat_summary, category, severity, "
                         "suggested_course_of_action, next_steps, contact_request, or status")

    if isinstance(chat_transcript, str):
        chat_transcript_str = chat_transcript
    else:
        chat_transcript_str = str(chat_transcript)

    values: tuple = (
        session_id, name.identifier, email_or_phone_number.identifier, datetime_of_chat, chat_duration,
        chat_transcript_str, chat_summary, category, severity, social_care_eligibility,
        suggested_course_of_action, next_steps, contact_request, status, final_rating, feedback
    )

    return values


async def get_chat_info(session_id):
    """
    Asynchronously gets chat information for the given session ID.
    Args:
        session_id (UUID4): The UUID4 of the session.
    Returns:
        Any: The chat information.
    """

    try:
        llm = AzureChatOpenAI(azure_deployment="gpt-4-32k-0613",
                              openai_api_version="2023-09-01-preview")
        chain: Runnable = create_openai_fn_runnable([ChatInfo], llm, DB_PROMPT)
        return await chain.ainvoke({"input": cl.user_session.get("runnable").get_session_history(session_id)})
    except Exception as e:
        raise RuntimeError('Unable to initialise summariser module.') from e
