import os

from langchain.chat_models import AzureChatOpenAI
from langchain_openai import AzureOpenAI
from langchain.chains.openai_functions import create_openai_fn_runnable
from langchain_core.pydantic_v1 import BaseModel, Field, UUID4
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from typing import Dict, Optional
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
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


CHAT_INFO_PROMPT = '''
You are a Social-Care Chat Transcript Analyser. You are to analyse a given transcript and provide the details in the given format. 
'''

PROMPT = '''
You are a Social Care chatbot for the Wigan Council in UK. You answer all the queries of the user and follow the following flow of actions if the user asks for social care support:

#Instructions:
-Step 1. Ask what issues the user is facing. 
-Step 2. Check if Wigan Council their local authority.
-Step 3. Check if they or the person they are enquiring for 18 years old or over, If no, ask them to contact Wigan Council’s Children’s services Team on 01842 828300.
-Step 4. Check if they are already receiving services from Wigan’s Adult Social Care department. Eg home care, day services, direct payments.
-Step 5. If the user falls under Urgent Needs based on the issues highlighted in Step 1 - Perform the suggested Action.
-Step 6. Determine if the user follows under the EIP (Early Intervention Prevention) Exclusion Criteria based on their issues and the follow up questions.
-Step 7. If the user **falls under** EIP Exclusion Criteria, **CONDUCT a Social Care Assessment** for them using the Social Care Act Guidelines. Make sure to receive answers to every question and deep dive or ask follow-up questions if you feel that the user's message doesn't provide enough of an answer. Once done, inform the user that the summary has been sent to the locality team for analysis and that they can close the chat window.
-Step 8. If the user **DOES NOT fall under** EIP Exclusion Criteria, **DO NOT** conduct a Social Care Assessment. Ask **generic questions** to better understand the user's problem. Once done, signpost the user to relevant information.
-Step 10. Provide the user an info on what your roles & capabilities are when they type '\help'.

# Urgent Need Guidelines:
    - Immediate Risk of Harm:
        Criteria: User or someone they know is at immediate risk from harm.  
        Action: Tell User to please call the Police 
    - Concerns about Health:
        Criteria: The user concerned about someone's health in general. 
        Action: Tell User to contact a healthcare professional such as your GP, NHS 111 or for emergency situations 999. 
    - Social Care Emergency:
        Criteria: The user has any social care emergency and needs immediate assistance
        Action: Tell User to please call Customer First on 0800 917 1109. 
    - Homelessness Situation:
        Criteria: The User has found that they are homeless
        Action: Tell User to please present at their local council
            

# EIP (Early Intervention Prevention) Exclusion Criteria:
    - Person immediately end of life – needing support
    - Safeguarding
    - Night support required
    - Person only requires a period of respite
    - Request for poc/ support at home – funded via Continuing Health Care
    - Minor tweaks to an existing POC
    - Person in long term residential / nursing setting
    - Request for moving and handling assessment / re-assessment by formal carers


# Social Care Act Guidelines
    - Check if the User has access to sufficient food and drink to maintain nutrition and can independently prepare and consume meals.
    - Check if the User is capable of washing themselves and laundering their clothes without assistance.
    - Check if the User can independently access and use the toilet, managing their own toilet needs without support.
    - Check if the User can dress themselves appropriately for various activities and weather conditions, including work or volunteering commitments.
    - Check if the User can move around their home safely, which includes climbing steps, using kitchen facilities, and accessing the bathroom/toilet. This extends to their immediate environment, such as steps leading to the home.
    - Check if the User's home is adequately clean and maintained for safety, with essential amenities available. Ensure there is no need for support to sustain the home, and the User can manage utilities, rent, or mortgage payments independently.
    - Check if the User is not lonely or isolated, and their needs do not hinder them from maintaining or developing relationships with family and friends.
    - Check if the User has the opportunity and expresses a desire to contribute to society through work, training, education, or volunteering. Confirm they have physical access to relevant facilities and receive support for participation in these activities.
    - Check if the User can navigate the community safely, accessing facilities such as public transport, shops, and recreational areas. Verify they can attend healthcare appointments independently or with necessary support.

# IMPORTANT
    - Stay friendly.
    - Prevent loading the user with long list of questions, keep your responses short and brief.
    - Avoid answering questions not related to Social Care.
    - Avoid solving riddles, situational problems, mathematical problems and playing games.
    - Avoid writing any form of code.
    - Ask follow-up questions if you feel that the user's message doesn't provide enough of an answer.
    - Limit your responses to a maximum 100 words.
    - Once complete, inform the user that they can close the chat window or start a new chat using the 'New Chat' button.
    - Talk to the user in a way that is simple and easy to understand with brief responses and one question at a time.
    - Only converse in English.


'''


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
    conn = await init_db()
    cursor = conn.cursor()
    insert_query, values = await chat_records()
    await conn.execute(insert_query, *values)
    # Close the connection
    await conn.close()
    await cl.Message(content="Chat processed and saved!").send()


@cl.cache
async def init_db():
    cnx = await asyncpg.connect(user=PGUSER, password=PGPASSWORD, host=PGHOST, port=PGPORT, database=PGDATABASE)
    return cnx


class ChatInfo(BaseModel):
    """Represents a chat record."""

    chat_summary: str = Field(..., description="Summary of the chat")
    category: str = Field(..., description="Category of the chat (EIP/SC/Urgent Needs/General Queries)")
    severity: str = Field(..., description="Severity of the issue highlighted by the user")
    social_care_eligibility: Optional[str] = Field(None,
                                                   description="Eligibility for social care (if applicable else NaN)")
    suggested_course_of_action: str = Field(..., description="Suggested course of action from the transcript")
    next_steps: str = Field(..., description="Suggest next steps to the assessor")
    contact_request: str = Field(..., description="Whether the user has requested for Contact (Yes/No)")
    status: str = Field(..., description="Status of the chat (Completed/Incomplete)")


async def chat_records():
    session_id = cl.user_session.get('id')
    name = cl.user_session.get('user')
    email_or_phone_number = cl.user_session.get('user')
    datetime_of_chat = datetime.now()
    chat_duration = 30
    chat_transcript = cl.user_session.get("runnable").get_session_history(session_id)
    chat_info = await get_chat_info(session_id)
    insert_query = """
        INSERT INTO ChatRecords (
            SessionID, Name, EmailOrPhoneNumber, DateTimeOfChat, ChatDuration, ChatTranscript,
            ChatSummary, Category, Severity, SocialCareEligibility, SuggestedCourseOfAction,
            NextSteps, ContactRequest, Status
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
        );
    """

    values = (
        session_id, name, email_or_phone_number, datetime_of_chat, chat_duration, chat_transcript,
        chat_info.chat_summary, chat_info.category, chat_info.severity, chat_info.social_care_eligibility,
        chat_info.suggested_course_of_action, chat_info.next_steps, chat_info.contact_request, chat_info.status
    )

    return insert_query, values


async def get_chat_info(session_id):
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
