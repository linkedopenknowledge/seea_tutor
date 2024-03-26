import streamlit as st
st.set_page_config(layout="wide")
from streamlit_chat import message
import sqlite3
import requests


api_url = "https://74.82.29.9:8501/prompts/"
#response = requests.get(api_url, verify=False)
#response.json()
#print(response.json())

def sendp(ttext):
    prompt1 = {"promt_id":"q01", "prompt_text":ttext}
    response = requests.post(api_url, json=prompt1, verify=False)
    return  response.json()

st.write(sendp("How are wastes accounted for in the SEEA?"))
