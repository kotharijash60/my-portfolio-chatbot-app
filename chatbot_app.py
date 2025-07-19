import streamlit as st
import os
import json # Import json for loading personal_info
import google.generativeai as genai

# --- Configuration ---
PERSONAL_INFO_FILE = "personal_info.json" # Path to your personal info JSON

# --- Google Gemini API Configuration ---
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("Google API Key not found. Please set it in Streamlit Cloud secrets as 'GOOGLE_API_KEY'.")
    st.stop() # Stop execution if no API key to prevent further errors

# Configure the Google Generative AI client
genai.configure(api_key=GOOGLE_API_KEY)

# --- Load Personal Information ---
@st.cache_data(show_spinner="Loading personal data...")
def load_personal_info(file_path):
    """Loads personal information from a JSON file."""
    if not os.path.exists(file_path):
        st.error(f"Error: Personal information file '{file_path}' not found. Please create it.")
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.error(f"Error: Could not parse '{file_path}'. Please check its JSON format for errors (e.g., missing commas, unclosed brackets).")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while loading '{file_path}': {e}")
        return None

personal_info = load_personal_info(PERSONAL_INFO_FILE)

if personal_info is None:
    st.stop() # Stop the app if crucial data is missing or malformed

# --- Use st.cache_resource for Model Initialization ---
@st.cache_resource
def get_gemini_model():
    """Initializes and returns the Google Gemini GenerativeModel."""
    try:
        # Use the model you confirmed works for generateContent
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        return model
    except Exception as e:
        st.error(f"Failed to initialize or connect to Gemini model 'models/gemini-1.5-flash-latest': {e}")
        st.error("Please check your API key and model availability for 'generateContent'.")
        st.stop() # Stop the app if model initialization fails

# Get the cached model instance
model = get_gemini_model()

# --- Agentic Logic (Personal Knowledge Base & Prompt Engineering) ---
def create_agentic_prompt(user_query, personal_info):
    if not personal_info:
        return "I apologize, but my personal information is not available at the moment."

    identity_statement = f"You are an AI chatbot assistant of {personal_info['name']}. You were created by {personal_info['name']} to provide accurate and helpful information about his professional background, skills, education, and projects. Always introduce yourself with this identity if asked 'who are you?' or similar questions."

    system_intro = f"""{identity_statement}

    Here is key information about {personal_info['name']} for you to reference:
    - **Name:** {personal_info['name']}
    - **Occupation:** {personal_info['occupation']}
    - **About Me:** {personal_info['about_me']}
    - **Skills:** {', '.join(personal_info['skills'])}
    - **Education:** {personal_info['education']}
    - **Contact Email:** {personal_info['contact_email']}
    - **LinkedIn:** {personal_info['linkedin_profile']}
    - **GitHub:** {personal_info['github_profile']}
    - **Portfolio Website:** {personal_info['portfolio_website']}

    **Projects:**
    """
    # Explicitly list projects with their types for Gemini to learn
    for project in personal_info['projects']:
        project_type = "Client Project" if "client project" in project['name'].lower() else "Personal Project"
        system_intro += f"- **{project['name']} ({project_type})**: {project['description']}\n"


    general_instructions = """
    **Primary Goal:** Answer user questions about Jash Kothari's professional profile using the provided information.

    **Specific Answering Instructions:**
    - Always provide factual answers directly from the provided information.
    - **For Projects:** If asked about "client projects", "personal projects", or "different types of projects", list the relevant projects by their name and a brief description, clearly indicating their type (Client/Personal).
    - If asked for a summary of a section (e.g., "summarize your skills"), provide a brief overview.
    - If the user asks about contact information, provide the email, LinkedIn, GitHub, and portfolio website directly.

    **General Chat Behavior:**
    - Be polite, concise, and helpful.
    - If the question is a general knowledge question not related to Jash Kothari, answer it to the best of your ability using your general knowledge, but maintain your persona as Jash Kothari's assistant.
    - Do not invent information about Jash Kothari that is not explicitly provided. If you cannot find the answer in the provided information, simply state that you don't have that specific detail about Jash Kothari.
    - Do not mention or suggest navigating to specific "sections" or "pages" as they are not present visually.
    """

    full_prompt_for_llm = f"{system_intro}\n{general_instructions}\n\nUser Query: {user_query}"
    return full_prompt_for_llm


st.set_page_config(page_title=f"{personal_info['name']}'s Portfolio Chatbot")
st.title(f"Hi, I'm {personal_info['name']}'s AI Assistant!")
st.write("Ask me anything! I'm powered by Google Gemini 1.5 Flash.")

# Initialize chat history in Streamlit session state
if "chat_session" not in st.session_state:
    # Initial message for the chatbot, introducing itself
    initial_message_content = f"Hello! I am a chatbot assistant of {personal_info['name']}. I was created by {personal_info['name']} to help you learn more about his professional background. How can I assist you today? You can ask me about his **skills**, **projects**, **education**, or **how to get in touch**!"
    
    # Start a new chat session with the initial message in history
    st.session_state.chat_session = model.start_chat(history=[
        {"role": "model", "parts": [initial_message_content]} # Gemini's 'assistant' role is 'model'
    ])

# Display chat messages from history on app rerun
for message in st.session_state.chat_session.history:
    # Map Gemini roles to Streamlit roles for display
    role = "user" if message.role == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

# React to user input
if prompt := st.chat_input("What would you like to ask?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Create agentic query by combining user prompt with personal info
    agentic_query = create_agentic_prompt(prompt, personal_info)

    with st.spinner("Thinking..."):
        try:
            # Send the agentic query to Gemini
            response = st.session_state.chat_session.send_message(agentic_query)
            bot_response = response.text
        except Exception as e:
            st.error(f"Error generating response from Gemini: {e}")
            # Provide a more helpful message for rate limits or other common issues
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                bot_response = "I'm currently experiencing high traffic or have hit a rate limit. Please try again in a moment!"
            else:
                bot_response = "I'm having trouble generating a response. Please try again later."
            
        if not bot_response:
            bot_response = "I'm having trouble generating a response. The API might be unresponsive."

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(bot_response)