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
# We will explicitly use 'gemini-pro' as the model name
# If 'gemini-pro' still gives 404, we might try 'text-bison-001'
try:
    model = genai.GenerativeModel('gemini-pro') 
    # Test a simple generate_content call to confirm it's available
    # This helps catch issues with the model's availability for generate_content
    model.generate_content("test", stream=False) 
except Exception as e:
    st.error(f"Failed to initialize or connect to Gemini model 'gemini-pro': {e}")
    st.stop()


def query_gemini_api(prompt_text):
    """Sends a query to the Google Gemini API."""
    if not GOOGLE_API_KEY:
        return "Google API Key not configured."
    
    try:
        # For simple text generation, generate_content is usually fine.
        # Stream=True allows for streaming responses, but Stream=False for direct response
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
    # Display user message in chat message container
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate a response from the AI model
    with st.spinner("Thinking..."):
        bot_response = query_gemini_api(prompt)
            
        if not bot_response:
            bot_response = "I'm having trouble generating a response. Please check the API."

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(bot_response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": bot_response})