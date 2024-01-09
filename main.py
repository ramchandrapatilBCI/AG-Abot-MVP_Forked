import datetime
import os
import re
import time
import uuid
from typing import Any

import chainlit as cl
from openai import AsyncAzureOpenAI
import asyncio
from chainlit import Message, Action
from dotenv import load_dotenv
from langchain import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversation.memory import ConversationSummaryMemory
from langchain.chat_models import AzureChatOpenAI
from sqlalchemy import create_engine, Column, Date, String, Text, Engine, Connection, Numeric, UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session

load_dotenv(dotenv_path='venv/.env')

aclient = AsyncAzureOpenAI(api_version="2023-09-01-preview",
                           azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
                           api_key=os.getenv("OPENAI_KEY"))
DEPLOYMENT_NAME: str = "gpt-4-32k"
user = ""
template: str = """Current conversation history:
{history}
The last question in the conversation history is the one the User is replying to
Instruction: You are a Social Care Self-assessment ChatBot! First you are to determine if the user has any urgent needs.
            Consider the conversation history (keeping track of questions that have been answered satisfactorily and 
            which question is being answered currently, perform the action associated with the question) 
            and keep in mind the following,
            Ask User for their name if their name is not present in current conversation history without fail even 
            if the User's question is just hello.
            After the name start ask Urgent Need questions and based on the User's answer suggest the associated action,
            Ask only one question at a time from the following scenarios.
            If the user responds positively to any Urgent Need question, after suggesting the course of action,
             stop the assessment, don't ask any other questions, and ask user how else can you help him.
             Check conversation history to check what question the user is responding to.
            Urgent need questions are:
                * Are you or someone you know at immediate risk from harm?  -> If Yes, Tell User to please call the Police 
                * Are you concerned about someone's health in general? -> If Yes, Tell User to contact a healthcare professional such as your GP, NHS 111 or for emergency situations 999. 
                * Do you have any social care emergency and need immediate assistance? ->  If Yes, Tell User to please call Customer First on 0800 917 1109. 
                * Have you found that you are homeless? ->  If Yes, Tell User to please present at their local council

            Give the specified response to the respective answer to the urgent need questions.
            Your response should always be polite, neat and friendly and should ask for further assistance.
            Give unique responses to keep the conversation engaging and fun.
            Rephrase the questions to make the conversation more engaging.
            After all urgent need questions have been asked write "Urgent Need Complete" and nothing else
            User: {input}

            ChatBot:
            """

template1 = """Current conversation history:
{history}
Initialize after the message "Start"
Instruction: Your motive is to find out if the user is an Individual or a Carer. Ask the neceassry questions to the user after 
explaining to the user what the categories mean using the following information.
Information: 
'''For brevity and simplicity, the term 'assessment under the Care Act' is used to refer to either a Care Act assessment of:
    - an individual's needs for care and support
    - a User's needs for support.'''
After finding out the category of the user print the output in the following format (don't print, anything else):
User is: Individual/Carer

User: {input}

ChatBot: """
template2 = """
            Current conversation history:
            {history}
            The last question in the conversation history is the one the User is replying to.
            Initialize after the message "Start"
            Instruction: You are a Social Care Self-assessment ChatBot! You are here to pre-assess Users to check for their
            Social Care plan eligibility.
            After all urgent need questions have been asked and If the User does not fall under any Urgent Need 
            only then proceed with the following:
            Your motive is to get the following questions answered from the User,
            ask only one question at a time, and only ask questions that have not been answered or the answer is not satisfactory by 
            referring to the conversation history,
            Questions to be asked:
                - Does the User have access to food and drink to maintain nutrition and are they able to prepare and consume the food and drink?
                - Is the User able to wash themselves and launder their clothes?
                - Is the User able to access and use the toilet and manage their own toilet needs?
                - Is the User able to dress themselves and be appropriately dressed, for example, in relation to the weather or the activities they are undertaking, which could include work/volunteering?
                - Is the User able to move around the home safely, including climbing steps, using kitchen facilities and accessing the bathroom/toilet? This also includes their immediate environment e.g. steps to the home.
                - Is the User’s home sufficiently clean and maintained to be safe, including having essential amenities? Does the User require support to sustain the home or maintain amenities such as water, electricity and gas or pay their rent or mortgage?
                - Is the User lonely or isolated? Do their needs prevent them from maintaining or developing relationships with family and friends?
                - Does the User have the opportunity and/or wish to apply themselves and contribute to society through work, training, education or volunteering? This includes physical access to any facility and support with participation in the relevant activity.
                - Is the User able to get around in the community safely and able to use facilities such as public transport, shops and recreational facilities? This includes the need for support when attending health care appointments.
                - Does the User have any parenting or other caring responsibilities e.g. as a parent, step-parent or grandparent?

            Your response should always be polite, neat and friendly and should ask for further assistance.
            Give unique responses to keep the conversation engaging and fun.
            Don't thank the user for their response, because it makes the conversation boring and monotonous.
            Rephrase the questions to make the conversation more engaging.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            Structure your response for easier reading and better understanding.
            Once all questions have been answered, respond with 
            "Assessment Complete. Please wait while we process your responses"
            and nothing else.
User: {input}

ChatBot: """
template3 = """
            Current conversation history:
            {history}
            The last question in the conversation history is the one the User is replying to.
            Initialize after the message "Start"
            Instruction: You are a Social Care Self-assessment ChatBot! You are here to pre-assess Users to check for their
            Social Care plan eligibility.
            After all urgent need questions have been asked and If the User does not fall under any Urgent Need 
            only then proceed with the following:
            Your motive is to get the following questions answered from the User,
            ask only one question at a time, and only ask questions that have not been answered or the answer is not satisfactory by 
            referring to the conversation history,
            Questions to be asked:
                - Does the User have any parenting responsibilities for a child in addition to their caring role for the adult, e.g. as a parent, step-parent or grandparent?
                - Does the User have any caring responsibilities to other adults, e.g. for a parent, as well as the adult with care and support needs?
                - Is the User's home a safe and appropriate environment to live in? Does it present a significant risk to the User’s wellbeing? A habitable home should be safe and have essential amenities such as water, electricity and gas.
                - Does the User have time to do essential shopping and to prepare meals for themselves and their family?
                - Does the User’s role prevent them from maintaining or developing relationships with family and friends?
                - Is the User able to continue in their job, contribute to society, apply themselves in education and volunteer to support civil society or have the opportunity to get a job, if they are not in employment?
                - Does the User have opportunities to make use of local community services and facilities e.g. library, cinema, gym or swimming pool?
                - Does the User have leisure time, e.g. some free time to read or engage in a hobby?

            Your response should always be polite, neat and friendly and should ask for further assistance.
            Give unique responses to keep the conversation engaging and fun.
            Don't thank the user for their response, because it makes the conversation boring and monotonous.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            Structure your response for easier reading and better understanding.
            Once all questions have been answered, respond with 
            "Assessment Complete. Please wait while we process your responses"
            and nothing else.
User: {input}
 
ChatBot: """

answer_prefix_tokens: list[str] = ["ChatBot"]

engine: Engine = create_engine(
    url="postgresql+psycopg2://hackathon_lq70_user:1cGvQbblv55lr2WX76tI5wi8VH1u2mpR@dpg-claueimg1b2c73a8f9t0-a"
        ".frankfurt-postgres.render.com/hackathon_lq70",
    pool_size=10,
    max_overflow=2,
    pool_recycle=300,
    pool_pre_ping=True,
    pool_use_lifo=True,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)
dbConnection: Connection = engine.connect()
Session: sessionmaker[Session] = sessionmaker(bind=engine)


class ChatRecord(declarative_base()):
    __tablename__ = 'chat_data'

    chat_id = Column(UUID(as_uuid=True), primary_key=True)
    date = Column(Date)
    name = Column(String(255))
    chat = Column(Text)
    summary = Column(Text)
    score = Column(Numeric(5, 2))
    user_type = Column(String(50))


session = Session()


async def database_push(name, chat, summary, score, user_type) -> None:
    patient = ChatRecord(
        chat_id=cl.user_session.get("unique_id"),
        date=datetime.datetime.now(),
        name=name,
        chat=chat,
        summary=summary,
        score=score,
        user_type=user_type
    )
    session.add(patient)
    session.commit()


async def find_name(text: str) -> str:
    prompt = 'You are a name extractor, Extract the name from the given text. Only print the name and nothing else.'
    messages = [{'role': 'system', 'content': prompt}, {'role': "user", 'content': text}]
    name = await aclient.chat.completions.create(model="gpt-4-32k",
                                                 messages=messages, temperature=0)
    return name.choices[0].message.content


@cl.author_rename
def rename(orig_author: str) -> str:
    rename_dict = {"ConversationChain": "Very advanced complicated intelligence!",
                   'User': 'Citizen'}
    return rename_dict.get(orig_author, orig_author)


async def process_transcript(supporting_doc):
    if user == "I":
        prompt = '''Given the following transcript please write a brief 200-250 word summary and then answer whether or  
                 not the person meets the following criteria in a standardised list format Yes or No with explanation 
                 on the next line make sure the explanation is on the line below the yes/no. Finally, score out of 10 
                 how many are not met so if they are really struggling they'd score 10/10, unknown does not count as not 
                 met and having no caregiving responsibilities doesnt add to the score, only if 
                 they struggle do you add a score so not having trouble doesnt add. make sure you add a +1 or a +0 to each 
                 explanation to show how the scores being made up later:
                    - Managing and maintaining nutrition
                    - Maintaining personal hygiene
                    - Managing toilet needs
                    - Being appropriately clothed
                    - Being able to make use of the adult's home safely
                    - Maintaining a habitable home environment
                    - Developing and maintaining family or other personal relationship
                    - Accessing and engaging in work, training, education or volunteering
                    - Making use of necessary facilities or services in the local community, including public transport, and recreational facilities or services
                    - Carrying out any caring responsibilities the adult has for a child
                 The transcript to use is here:'''

        messages = [{'role': 'system', 'content': prompt}, {'role': "user", 'content': supporting_doc}]
        res = await aclient.chat.completions.create(model="gpt-4-32k",
                                                    messages=messages, temperature=0.1)
        return res.choices[0].message.content
    elif user == "C":
        prompt = '''Given the following transcript please write a brief 200-250 word summary (mention user is a Carer in the summary)
                 and then answer whether or  
                 not the person meets the following criteria in a standardised list format Yes or No with explanation 
                 on the next line make sure the explanation is on the line below the yes/no. Finally, score out of 10 
                 how many are not met so if they are really struggling they'd score 8/8, unknown does not count as not 
                 met, having caregiving responsibilities adds to the score whereas lhaving leisure time doesn't, only if 
                 they struggle do you add a score so not having trouble doesnt add. make sure you add a +1 or a +0 to each 
                 explanation to show how the scores being made up later:
                    - Carrying out any caring responsibilities the carer has for a child
                    - Providing care to other persons for whom the carer provides care
                    - Maintaining a habitable home environment in the carer’s home, whether or not this is also the home of the adult needing care
                    - Managing and maintaining nutrition
                    - Developing and maintaining family or other personal relationships
                    - Engaging in work, training, education or volunteering
                    - Making use of necessary facilities or services in the local community, including recreational facilities or services
                    - Does the carer have leisure time, e.g. some free time to read or engage in a hobby?

                 The transcript to use is here:'''

        messages = [{'role': 'system', 'content': prompt}, {'role': "user", 'content': supporting_doc}]
        res = await aclient.chat.completions.create(model="gpt-4-32k",
                                                    messages=messages, temperature=0.1)

        return res.choices[0].message.content


async def extract_score(text):
    print(text)
    score_pattern = r'Score: ([0-9.]+)/\d+'
    matches = re.search(score_pattern, text)
    print(matches)
    score = float(matches.group(1))
    chat_id = cl.user_session.get("unique_id")
    if score > 1:
        print('eligible')
        await send_msg('''
Based on what you've told us, it appears you could be eligible for extra help from us. Please confirm that you would like a full assessment from the Council.
Please note, you may need to pay something towards the cost of care, particularly if you have more than £23,250 in savings or get other allowances. As part of the assessment we will need to do a full financial assessment. If you don't agree to this you may need to pay the full cost of your care.
After the assessment we will tell you exactly what you will need to pay. You are not committing to anything at this stage.''')
        res = await cl.AskUserMessage(content="Agree? (Yes/No)").send()
        if 'yes' in res['content'].lower():
            content = f'Thank you for the approval. Your request has been sent forward, your unique id is {str(chat_id)}.' \
                      f' Thank you for your time ☺️'
            await send_msg(content)
        else:
            content = 'Confirmation denied. Your request has been cancelled. Thank you for your time ☺️'
            await send_msg(content)

    elif score < 2:
        print('not eligible')
        prompt = ''' Inform the user that "it does not appear you're eligible for extra help from us under the Care Act 2014."
        Then based on the Assessment results provided at the end of this prompt, provide the user with resources
                    that he/she needs from below, Only give resources for the categories the User is struggling in:
                    Home and living 
                        See information about services that can help you at home. http://www.lewisham.gov.uk/helpathome
                        Find out how to get help and advice with money and paperwork. http://www.lewisham.gov.uk/moneyandpaperwork
                        Find out about equipment and other help with using the toilet. http://www.lewisham.gov.uk/usingthetoilet

                        Food and drink 
                        Find out about help with shopping and meals. http://www.lewisham.gov.uk/mealsandshopping
                        See information about help with eating and drinking. http://www.lewisham.gov.uk/eatinganddrinkinghelp

                        Getting out in the community 
                        Find out about getting help with work, studying and volunteering. http://www.lewisham.gov.uk/helpwithworkstudyingvolunteering
                        See information about help with socialising with other people http://www.lewisham.gov.uk/helpsocialising

                        Find out about help with travel and transport. http://www.lewisham.gov.uk/helpwithtravelandtransport

                        Keeping well 
                        See information about improving your mental health. http://www.lewisham.gov.uk/autonomymentalhealth

                        Caring 
                        See information about help to care for children. http://www.lewisham.gov.uk/helptocareforchildren
                        Feeling safe 
                        See information about keeping safe in your home. http://www.lewisham.gov.uk/autonomysafety
                        See information about preventing falls. https://www.lewisham.gov.uk/falls  
                    Assessment:'''
        messages = [{'role': 'system', 'content': prompt}, {'role': "user", 'content': text}]
        ans = await aclient.chat.completions.create(model="gpt-4-32k",
                                                    messages=messages, temperature=0.1)
        await send_msg(ans['choices'][0].message.content)
        res = await cl.AskUserMessage(content='''
                It's important to note that you have a statutory right to request an assessment. If you would still like to request 
                an assessment please type Yes/No''').send()
        if 'yes' in res['content'].lower():
            await send_msg('''
                Please confirm that you would like a full assessment from the Council.
                Please note, you may need to pay something towards the cost of care, particularly if you have more than £23,250 in savings or get other allowances. As part of the assessment we will need to do a full financial assessment. If you don't agree to this you may need to pay the full cost of your care.
                After the assessment we will tell you exactly what you will need to pay. You are not committing to anything at this stage.''')
            res2 = await cl.AskUserMessage(content="Agree? (Yes/No)").send()
            if 'yes' in res2['content'].lower():
                content = f'Thank you for the approval. Your request has been sent forward, your unique id is {str(chat_id)}.' \
                          f' Thank you for your time ☺️'
                await send_msg(content)
            else:
                content = 'Confirmation denied. Your request has been cancelled. Thank you for your time ☺️'
                await send_msg(content)
        else:
            content = f'Confirmation denied. Your request has been cancelled. Thank you for your time ☺️'
            await send_msg(content)
    else:
        await cl.Message(content='Unsure').send()
    return score


# @cl.action_callback("end_chat")
async def send_msg(res):
    msg: Message = cl.Message(content="")
    await msg.send()
    token_list: list[Any] = re.findall(pattern=r'\S+|\n', string=res)
    for token in token_list:
        await msg.stream_token(token=f'{token} ')
        await asyncio.sleep(0.06)
    await msg.update()


async def on_action() -> None:
    llm_chain: ConversationChain = cl.user_session.get("llm_chain")
    print('name')
    name = await find_name(text=llm_chain.memory.buffer)
    print('processing')
    res = await process_transcript(llm_chain.memory.buffer)
    time.sleep(0.5)
    print('scores')
    score = await extract_score(res)
    print('db push')
    await database_push(name=name, chat=llm_chain.memory.buffer, summary=res, score=score, user_type=user)
    time.sleep(0.5)
    llm_chain.memory.clear()
    await send_msg(f'New Chat Initiated... {llm_chain.memory.buffer}')


@cl.on_chat_start
def main():
    # Instantiate the chain for that user session
    unique_id = uuid.uuid4()
    print(unique_id)

    prompt: PromptTemplate = PromptTemplate(template=template, input_variables=["history", "input"])

    llm: AzureChatOpenAI = AzureChatOpenAI(
        openai_api_base=os.getenv('OPENAI_ENDPOINT'),
        openai_api_version="2023-07-01-preview",
        deployment_name=DEPLOYMENT_NAME,
        openai_api_key=os.getenv('OPENAI_KEY'),
        openai_api_type="azure",
        temperature=0,
        streaming=True
    )
    llm_chain: ConversationChain = ConversationChain(prompt=prompt, llm=llm, verbose=True,
                                                     memory=ConversationBufferMemory(llm=llm, ai_prefix='ChatBot',
                                                                                     human_prefix='User'))

    # Store the chain in the user session
    cl.user_session.set(key="llm_chain", value=llm_chain)
    cl.user_session.set(key="unique_id", value=unique_id)


@cl.on_message
async def main(message):
    global user
    msg: Message = cl.Message(content="")
    await msg.send()
    await asyncio.sleep(0.06)
    llm_chain: ConversationChain = cl.user_session.get("llm_chain")
    try:
        res: dict[str, Any] = await llm_chain.acall(message.content, callbacks=[
            cl.AsyncLangchainCallbackHandler(stream_final_answer=True)])
    except ValueError:
        res: dict[str, Any] = await llm_chain.acall(message, callbacks=[
            cl.AsyncLangchainCallbackHandler(stream_final_answer=True)])
    print(type(llm_chain.prompt))
    if 'Urgent Need Complete' in res["response"]:
        # await send_msg(res['response'].replace('Urgent Need Complete.', ''))
        llm_chain.prompt = PromptTemplate(template=template1, input_variables=["history", "input"])
        await main("Start")
    elif 'User is: Individual' in res["response"]:
        llm_chain.prompt = PromptTemplate(template=template2, input_variables=["history", "input"])
        user = "I"
        await main("Start")
    elif 'User is: Carer' in res["response"]:
        llm_chain.prompt = PromptTemplate(template=template3, input_variables=["history", "input"])
        user = "C"
        await main("Start")
    elif 'Assessment Complete' in res["response"]:
        response = res["response"]
        token_list: list[Any] = re.findall(pattern=r'\S+|\n', string=response.replace(' Assessment Complete.', ''))
        for token in token_list:
            await msg.stream_token(token=f'{token} ')
            await asyncio.sleep(0.06)
        await msg.update()
        await on_action()
        # await cl.Message(content='Done').send()
    else:
        # approve_action: Action = cl.Action(name="end_chat", value="ok", label="End Chat")
        # cl.user_session.set(key="actions")
        await send_msg(res['response'])
