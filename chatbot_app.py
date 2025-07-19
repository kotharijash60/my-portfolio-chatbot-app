import streamlit as st
import os
import json
import google.generativeai as genai

# --- Configuration ---
PERSONAL_INFO_FILE = "personal_info.json"

# --- Google Gemini API Configuration ---
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("Google API Key not found. Please set it in Streamlit Cloud secrets as 'GOOGLE_API_KEY'.")
    st.stop()

# --- Load Personal Information ---
@st.cache_data(show_spinner="Loading personal data...")
def load_personal_info(file_path):
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
    st.stop()

# --- Construct the System Instruction ---
# This part will be given to the model once at initialization
def get_system_instruction(personal_info):
    if not personal_info:
        return "" # Return empty if no personal info

    identity_statement = f"You are an AI chatbot assistant of {personal_info['name']}. You were created by {personal_info['name']} to provide accurate and helpful information about his professional background, skills, education, and projects. Always introduce yourself with this identity if asked 'who are you?' or similar questions."

    personal_data = f"""
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
    for project in personal_info['projects']:
        project_type = "Client Project" if "client project" in project['name'].lower() else "Personal Project"
        personal_data += f"- **{project['name']} ({project_type})**: {project['description']}\n"

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
    return f"{identity_statement}\n{personal_data}\n{general_instructions}"

# --- Use st.cache_resource for Model Initialization ---
@st.cache_resource
def get_gemini_model(system_instruction_text):
    """Initializes and returns the Google Gemini GenerativeModel with system instructions."""
    try:
        # Configure the Google Generative AI client (moved here for explicit key usage)
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Initialize the model with system_instruction
        model = genai.GenerativeModel(
            'models/gemini-1.5-flash-latest',
            system_instruction=[system_instruction_text] # Pass system instruction here
        )
        return model
    except Exception as e:
        st.error(f"Failed to initialize or connect to Gemini model 'models/gemini-1.5-flash-latest': {e}")
        st.error("Please check your API key and model availability for 'generateContent'.")
        st.stop()

# Get the system instruction text
system_instruction_text = get_system_instruction(personal_info)

# Get the cached model instance, passing the system instruction
model = get_gemini_model(system_instruction_text)


st.set_page_config(page_title=f"{personal_info['name']}'s Portfolio Chatbot", layout="centered")
st.title(f"Hi, I'm {personal_info['name']}'s AI Assistant!")
st.write("Ask me anything! I'm powered by Google Gemini 1.5 Flash.")

# Initialize chat history in Streamlit session state
if "chat_session" not in st.session_state:
    initial_message_content = f"Hello! I am a chatbot assistant of {personal_info['name']}. I was created by {personal_info['name']} to help you learn more about his professional background. How can I assist you today? You can ask me about his **skills**, **projects**, **education**, or **how to get in touch**!"

    # Start a new chat session with the initial assistant message in display history only
    # The system instruction is already handled in model initialization
    st.session_state.chat_session = model.start_chat(history=[]) # Start with an empty history for the model
    st.session_state.messages = [ # This is for Streamlit's display history
        {"role": "assistant", "content": initial_message_content}
    ]
else:
    # Ensure st.session_state.messages is always initialized if chat_session exists
    if "messages" not in st.session_state:
        # Reconstruct display messages from chat_session history if needed on rerun
        st.session_state.messages = []
        for msg in st.session_state.chat_session.history:
            role = "user" if msg.role == "user" else "assistant"
            st.session_state.messages.append({"role": role, "content": msg.parts[0].text})


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input(f"What would you like to ask {personal_info['name']}?"):
    # Add user message to Streamlit display history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Thinking..."):
        try:
            # Send *only* the user's direct prompt to Gemini
            response = st.session_state.chat_session.send_message(prompt)
            bot_response = response.text
        except genai.types.BlockedPromptException as e:
            st.error(f"Your prompt was blocked due to safety concerns: {e.response.prompt_feedback}")
            bot_response = "I'm sorry, but I cannot respond to that query due to safety guidelines."
        except Exception as e:
            st.error(f"Error generating response from Gemini: {e}")
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                bot_response = "I'm currently experiencing high traffic or have hit a rate limit. Please try again in a moment!"
            else:
                bot_response = "I'm having trouble generating a response. Please try again later."

    # Add assistant response to Streamlit display history
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    with st.chat_message("assistant"):
        st.markdown(bot_response)