import streamlit as st
import os
import google.generativeai as genai

# --- Google Gemini API Configuration ---
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY") 

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    st.error("Google API Key not found. Please set it in Streamlit Cloud secrets as 'GOOGLE_API_KEY'.")
    st.stop() # Stop execution if no API key to prevent further errors

# Initialize the Gemini model for text generation
try:
    # Use the model you confirmed works for generateContent
    # This should be 'models/gemini-1.5-flash-latest' based on your previous output
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest') 
    # Small test to ensure model is accessible without consuming much quota
    model.generate_content("Hello", stream=False) 
except Exception as e:
    st.error(f"Failed to initialize or connect to Gemini model 'models/gemini-1.5-flash-latest': {e}")
    st.error("Please check your API key and model availability for 'generateContent'.")
    st.stop()

st.set_page_config(page_title="My Portfolio Chatbot")
st.title("My Portfolio Chatbot")
# Update this message to reflect the model being used
st.write("Ask me anything! I'm powered by Google Gemini 1.5 Flash.") 

# Initialize chat history in Streamlit session state
if "chat_session" not in st.session_state:
    st.session_session = model.start_chat(history=[]) # Start a new chat session

# Display chat messages from history on app rerun
for message in st.session_state.chat_session.history: # Iterate through the chat session history
    role = "user" if message.role == "user" else "assistant" # Map Gemini roles to Streamlit roles
    with st.chat_message(role):
        st.markdown(message.parts[0].text) # Access the text part of the message

# React to user input
if prompt := st.chat_input("What would you like to ask?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to chat session history
    # The chat_session.send_message method automatically adds to history
    # and sends the full history to the model
    
    with st.spinner("Thinking..."):
        try:
            response = st.session_state.chat_session.send_message(prompt)
            bot_response = response.text
        except Exception as e:
            st.error(f"Error generating response from Gemini: {e}")
            bot_response = "I'm having trouble generating a response. Please try again later."
            
        if not bot_response:
            bot_response = "I'm having trouble generating a response. Please check the API."

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(bot_response)

    # Note: st.session_state.messages is no longer explicitly needed
    # as the history is managed by st.session_state.chat_session.history