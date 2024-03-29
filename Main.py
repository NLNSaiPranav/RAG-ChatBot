import os
from dotenv import load_dotenv
from typing import Any, List, Mapping, Optional, Union, Dict
from pydantic import BaseModel, Extra
from langchain import PromptTemplate
from langchain.chains import LLMChain, SimpleSequentialChain
from langchain.llms.base import LLM
from langchain.llms.utils import enforce_stop_tokens
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.llms import OpenAI
from langchain.chains import ConversationalRetrievalChain
import langchain.schema.document
from langchain.document_loaders import TextLoader
import requests
from ibm_watson_machine_learning.foundation_models.utils.enums import ModelTypes
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings import TensorflowHubEmbeddings
from langchain.memory import ConversationBufferMemory
import streamlit as st

load_dotenv()
project_id = os.getenv("5cb8e3b2-dbe7-44b5-afe3-ac5dfa3236ad", None)
credentials = {
    "url": "https://us-south.ml.cloud.ibm.com",
    "apikey": os.getenv("BieErUp8OcRozHv2unvr5yIQeoFsN6DVAGdGAk703Bd4", None)
}


print([model.name for model in ModelTypes])
model_id = ModelTypes.LLAMA_2_70B_CHAT
parameters = {
    GenParams.DECODING_METHOD: "greedy",
    GenParams.MAX_NEW_TOKENS: 200
}


def getBearer(apikey):
    form = {'apikey': apikey, 'grant_type': "urn:ibm:params:oauth:grant-type:apikey"}
    print("About to create bearer")
    response = requests.post("https://iam.cloud.ibm.com/oidc/token", data=form)
    if response.status_code != 200:
        print("Failed to get token. Invalid status code:", response.status_code)
        try:
            error_message = response.json()["error_description"]
        except Exception as e:
            error_message = str(e)
        raise Exception("Failed to get token: " + error_message)
    json = response.json()
    if "access_token" not in json:
        print("Invalid/no access token retrieved")
        raise Exception("Failed to get token, invalid response")
    print("Bearer retrieved")
    return json["access_token"]

credentials["token"] = getBearer("BieErUp8OcRozHv2unvr5yIQeoFsN6DVAGdGAk703Bd4")

llama_model = Model(
    model_id=model_id,
    params=parameters,
    credentials=credentials,
    project_id='5cb8e3b2-dbe7-44b5-afe3-ac5dfa3236ad')
# llama_model.get_details()['short_description']
# llama_model.get_details()['model_limits']
# instruction = "Using the directions below, answer in a maximum of  2 sentences. "
# question = "What is the capital of Italy"
# prompt=" ".join([instruction, question])
# llama_model.generate_text(question)
# result=llama_model.generate(prompt)['results'][0]['generated_text']
result={'model_id': 'meta-llama/llama-2-70b-chat',
 'created_at': '2023-10-24T18:58:01.390Z',
 'results': [{'generated_text': '?\nThe capital of Italy is Rome (Italian: Roma). Rome is the largest city in Italy and is located in the central-western part of the country. It is known for its rich history, architecture, art, and culture, and is home to many famous landmarks such as the Colosseum, the Pantheon, and the Vatican City.',
   'generated_token_count': 79,
   'input_token_count': 7,
   'stop_reason': 'eos_token'}],
 'system': {'warnings': [{'message': 'This model is a Non-IBM Product governed by a third-party license that may impose use restrictions and other obligations. By using this model you agree to its terms as identified in the following URL. URL: https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/fm-models.html?context=wx',
    'id': 'DisclaimerWarning'}]}}

parameters = {
    GenParams.DECODING_METHOD: "greedy",
    GenParams.MAX_NEW_TOKENS: 200
}

flan_ul2_model = Model(
    model_id=ModelTypes.FLAN_UL2,
    credentials=credentials,
    project_id='5cb8e3b2-dbe7-44b5-afe3-ac5dfa3236ad',
    params=parameters

    )
prompt_template = "What color is the {flower}?"
llm_chain = LLMChain(
    llm=flan_ul2_model.to_langchain(),
    prompt=PromptTemplate.from_template(prompt_template)
)

loader = TextLoader("Plaksha.txt")
document = loader.load()

# langchain.schema.document.Document
text_splitter = CharacterTextSplitter(separator="\n",
                                      chunk_size=1000,
                                      chunk_overlap=200)
documents = text_splitter.split_documents(document)


url = "https://tfhub.dev/google/universal-sentence-encoder-multilingual/3"
embeddings  = TensorflowHubEmbeddings(model_url=url)
text_chunks=[content.page_content for content in documents]
vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)

memory = ConversationBufferMemory(memory_key="chat_history",
                                  return_messages=True)
llm=llama_model.to_langchain()
qa = ConversationalRetrievalChain.from_llm(llm=llama_model.to_langchain(),
                                           retriever=vectorstore.as_retriever(),memory=memory)

def main():
    st.set_page_config(
    page_title="Chatbot Demo",
    page_icon=":robot_face:",
    layout="wide",
    initial_sidebar_state="auto",
    )
    
    st.title("Plaksh Chatbot")
    st.write("A chatbot for Plaksha University.")

    st.sidebar.image('download.png', use_column_width=True)
    chat_history = []
    st.sidebar.title("Settings")
    st.sidebar.write("This is a chatbot demo app.")
    st.sidebar.write("Enter your message in the text box below and click 'Send' to chat with the chatbot.")

    query = st.text_input("You:", "")
    # query = st.text_input("Enter your question:")
    if st.button("Send"):
        result = qa({"question": query, "chat_history": chat_history})
        answer = result["answer"]
        chat_history.append((query, answer))
        st.text_area("Chatbot:", answer)
        # st.write(answer)
if __name__ == "__main__":
    main()
