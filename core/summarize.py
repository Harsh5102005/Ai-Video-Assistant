from langchain_mistralai import ChatMistralAI
from langchain_core.runnables import RunnablePassthrough,RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os 


def get_llm():
    return ChatMistralAI(model='codestral-latest',mistral_api_key=os.getenv('MISTRAL_API_KEY'))

def split_transcript(transcript:str)->list:
    splitter=RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200
    )
    return splitter.split_text(transcript)


def summarize(transcript:str)->str:
    llm=get_llm()
    map_prompt=ChatPromptTemplate(
        [
            ('system',"Summarize this portion of meeting transcript concisely"),
            ('human',"{text}")
        ]
    )
    map_chain=map_prompt| llm|StrOutputParser()

    chunks=split_transcript(transcript)
    chunk_summaries=[map_chain.invoke({"text":chunk}) for chunk in chunks]

    combined_chunk="\n\n".join(chunk_summaries)
    combined_prompt=ChatPromptTemplate(
        [
            ("system","You are an expert meeting summarizer. combine these partial summaries into one final professsional meeting summary in bullet points",),
            ('human',"{text}"),
            
        ]

    )
    final_chain=RunnablePassthrough()|RunnableLambda(lambda x:{"text":x}) |combined_prompt|llm|StrOutputParser()
    return final_chain.invoke(combined_chunk)


def generate_title(text:str)->str:
    llm=get_llm()

    title_chain=RunnablePassthrough()|RunnableLambda(lambda x:{"text":x}) |ChatPromptTemplate([
        ('system',"Based on meeting transcription, generate a short professional meeting title"
        "max 8 words and only return the title nothing else"),
        ('human',"{text}")
    ])|llm|StrOutputParser()

    return title_chain.invoke(text[:2000])

