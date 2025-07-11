import streamlit as st
import os
import json
import requests

# Hugging Face Model ID and API Token
# Streamlit Cloud uses st.secrets for environment variables/secrets
HF_MODEL_ID = "gpt2"
# IMPORTANT: You will set HF_API_TOKEN in Streamlit Cloud's secrets later.
HF_API_TOKEN = st.secrets.get("HF_API_TOKEN") 

# Hugging Face Inference API endpoint
API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL_ID}"

def query_huggingface_api(payload):
    """Sends a query to the Hugging Face Inference API."""
    if not HF_API_TOKEN:
        st.error("Hugging Face API Token not found. Please set it in Streamlit Cloud secrets.")
        return None

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with AI model: {e}")
        st.error("Please check your API token or model ID.")
        return None

st.set_page_config(page_title="My Portfolio Chatbot")
st.title("My Portfolio Chatbot")
st.write("Ask me anything! I'm gpt2")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What would you like to ask?"):
    # Display user message in chat message container
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate a response from the AI model
    with st.spinner("Thinking..."):
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 150, # Limit response length
                "temperature": 0.7,    # Creativity of response
                "top_p": 0.9,          # Diversity of response
                "return_full_text": False # Only return generated text
            },
            "options": {
                "wait_for_model": True # Wait if model is loading
            }
        }
        output = query_huggingface_api(payload)

        if output:
            # Hugging Face response format for text-generation is often a list of dicts
            bot_response = output[0]['generated_text'] if output and isinstance(output, list) and output[0] and 'generated_text' in output[0] else "Sorry, I couldn't generate a response."
        else:
            bot_response = "I'm having trouble generating a response. Please check the API."

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(bot_response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": bot_response})