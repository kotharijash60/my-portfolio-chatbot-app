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

# --- Debugging: List Available Models ---
st.header("Debugging: Available Gemini Models (Supporting generateContent)")
try:
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            st.write(f"Available Model: **`{m.name}`** (Supported Methods: `{m.supported_generation_methods}`)")
    
    if not available_models:
        st.warning("No models found that support 'generateContent'. This might indicate an API key issue or regional restriction.")

except Exception as e:
    st.error(f"Error listing models: {e}")

st.divider() # Adds a separator in the UI

# Initialize the Gemini model (we will set this correctly AFTER seeing list_models output)
# For now, we'll use a placeholder that will likely still error for the main chat functionality
# You will replace this with the correct model name after the next deploy shows the list
# Initialize the Gemini model
model = genai.GenerativeModel('models/gemini-1.5-flash-latest') 
st.write("Ask me anything! I'm powered by Google Gemini 1.5 Flash.") 

def query_gemini_api(prompt_text):
    """Sends a query to the Google Gemini API."""
    if not GOOGLE_API_KEY:
        return "Google API Key not configured."
    
    if model is None: # Check if model failed to initialize due to the error
        return "AI Model failed to initialize. Check the 'Debugging' section above."

    try:
        response = model.generate_content(prompt_text, stream=False)
        return response.text
    except Exception as e:
        st.error(f"Error communicating with Google Gemini API: {e}")
        st.error("Please check your API key or model availability.")
        return None

st.set_page_config(page_title="My Portfolio Chatbot")
st.title("My Portfolio Chatbot")
st.write("Ask me anything! I'm powered by Google Gemini.") # Updated message

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What would you like to ask?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Thinking..."):
        bot_response = query_gemini_api(prompt)
            
        if not bot_response:
            bot_response = "I'm having trouble generating a response. Please check the API."

    with st.chat_message("assistant"):
        st.markdown(bot_response)
    st.session_state.messages.append({"role": "assistant", "content": bot_response})