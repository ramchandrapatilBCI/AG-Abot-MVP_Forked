import os

from langchain.chat_models import AzureChatOpenAI
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from typing import Dict, Optional
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
import uuid
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
You are a Social Care chatbot for the Wigan Council in UK. You answer all the queries of the user and follow the following flow of actions if the user asks for social care support:

#Instructions:
-Step 1. Ask what issues the user is facing. 
-Step 2. Check if Wigan Council their local authority.
-Step 3. Check if they or the person they are enquiring for 18 years old or over, If no, ask them to contact Wigan Council’s Children’s services Team on 01842 828300.
-Step 4. Check if they are already receiving services from Wigan’s Adult Social Care department. Eg home care, day services, direct payments.
-Step 5. If the user falls under Urgent Needs based on the issues highlighted in Step 1 - Perform the suggested Action.
-Step 6. Determine if the user follows under the EIP (Early Intervention Prevention) Exclusion Criteria based on their issues and the follow up questions.
-Step 7. If the user falls under EIP Exclusion Criteria, Conduct a Social Care Assessment for them using the Social Care Act Guidelines. Make sure to receive answers to every question and deep dive or ask follow-up questions if you feel that the user's message doesn't provide enough of an answer. Once done, inform the user that the summary has been sent to the locality team for analysis and that they can close the chat window.
-Step 8. If the user **does not** fall under EIP, Ask generic questions to better understand the user's problem. Once done, signpost the user to relevant information.
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
    - Does the User have access to food and drink to maintain nutrition and are they able to prepare and consume the food and drink?
    - Is the User able to wash themselves and launder their clothes?
    - Is the User able to access and use the toilet and manage their own toilet needs?
    - Is the User able to dress themselves and be appropriately dressed, for example, in relation to the weather or the activities they are undertaking, which could include work/volunteering?
    - Is the User able to move around the home safely, including climbing steps, using kitchen facilities and accessing the bathroom/toilet? This also includes their immediate environment e.g. steps to the home.
    - Is the User’s home sufficiently clean and maintained to be safe, including having essential amenities? Does the User require support to sustain the home or maintain amenities such as water, electricity and gas or pay their rent or mortgage?
    - Is the User lonely or isolated? Do their needs prevent them from maintaining or developing relationships with family and friends?
    - Does the User have the opportunity and/or wish to apply themselves and contribute to society through work, training, education or volunteering? This includes physical access to any facility and support with participation in the relevant activity.
    - Is the User able to get around in the community safely and able to use facilities such as public transport, shops and recreational facilities? This includes the need for support when attending health care appointments.


# IMPORTANT
    - Stay friendly.
    - Prevent loading the user with long list of questions, keep your responses short and brief.
    - Avoid answering questions not related to Social Care.
    - Avoid solving riddles, situational problems, mathematical problems and playing games.
    - Avoid writing any form of code.
    - Ask follow-up questions if you feel that the user's message doesn't provide enough of an answer.
    - Limit your responses to a maximum 100 words.
    - Once complete, inform the user that they can close the chat window or start a new chat using the 'New Chat' button.
    - Talk to the user like you would talk to a 9 year old (Simple, and easy to understand with brief responses and one question at a time)
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
    if end: end.remove()
    if transcript: transcript.remove()
    end = cl.Action(name="End chat", value="End", description="End chat")
    transcript = cl.Action(name="Transcript", value="transcript", description="Transcript")
    actions = [
        end, transcript
    ]
    msg = cl.Message(content="", actions=actions)
    if message.content in ['\\transcript', '\\t']:
        await cl.Message(content=runnable.get_session_history(user_id)).send()
    else:
        async for chunk in runnable.astream(
                {"question": message.content},
                config=RunnableConfig(callbacks=[cl.AsyncLangchainCallbackHandler()],
                                      configurable={"session_id": user_id})
        ):
            await msg.stream_token(chunk)

    await msg.send()
    cl.user_session.set('end', end)
    cl.user_session.set('transcript', transcript)


@cl.action_callback("End chat")
async def on_action_end(action: cl.Action):
    cl.user_session.set("id", str(uuid.uuid4()))
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
    await cl.Message(content="Chat processed and saved!").send()
