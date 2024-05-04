import os
import streamlit as st
from pypdf import PdfReader
import ollama

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Set up the UI with a custom theme
st.set_page_config(layout="wide", page_title="ChatGPT PDF Q&A")
st.sidebar.title("ChatPDF")
st.sidebar.write("Upload a PDF file and ask questions about its content.")

# Create a directory to store user data if it doesn't exist
DATA_DIR = "user_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Define sign-up and sign-in states
is_authenticated = st.session_state.get("is_authenticated", False)
username = st.session_state.get("username", "")

# Sign-Up Functionality
if not is_authenticated:
    new_username = st.sidebar.text_input("New Username")
    new_password = st.sidebar.text_input("New Password", type="password")
    confirm_password = st.sidebar.text_input("Confirm Password", type="password")
    sign_up_button = st.sidebar.button("Sign Up")

    if sign_up_button:
        # Perform validation and create new account
        if new_password == confirm_password:
            # Store the new user's credentials
            with open(os.path.join(DATA_DIR, f"{new_username}.txt"), "w") as file:
                file.write(new_password)
            # Create a chat history file for the new user
            open(os.path.join(DATA_DIR, f"{new_username}_chat_history.txt"), "a").close()
            st.experimental_rerun()  # Reload page after sign-up
            st.sidebar.success("Account created successfully! Please sign in.")
        else:
            st.sidebar.error("Passwords do not match.")

# Sign-In Functionality
if not is_authenticated:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    sign_in_button = st.sidebar.button("Sign In")

    if sign_in_button:
        # Check if the username exists
        if os.path.exists(os.path.join(DATA_DIR, f"{username}.txt")):
            # Check if the password matches
            with open(os.path.join(DATA_DIR, f"{username}.txt"), "r") as file:
                stored_password = file.read().strip()
            if password == stored_password:
                st.session_state.is_authenticated = True
                st.session_state.username = username
                st.experimental_rerun()  # Reload page after sign-in
                st.sidebar.success("Successfully signed in!")
            else:
                st.sidebar.error("Invalid username or password")
        else:
            st.sidebar.error("Invalid username or password")

# Only show the main app content if the user is authenticated
if is_authenticated:
    # Upload PDF
    uploaded_pdf = st.sidebar.file_uploader("Choose a PDF file", type="pdf")

    # Display uploaded PDF name
    if uploaded_pdf:
        st.sidebar.write(f"**Uploaded PDF:** {uploaded_pdf.name}")
        pdf_text = extract_text_from_pdf(uploaded_pdf)
    else:
        st.sidebar.write("**No PDF uploaded.**")
        pdf_text = ""

    # Load chat history for the current user
    chat_history_file = os.path.join(DATA_DIR, f"{username}_chat_history.txt")
    chat_history = []
    if os.path.exists(chat_history_file):
        with open(chat_history_file, "r") as file:
            chat_history = file.readlines()

    # Function to update the chat history
    def update_chat_history(user_question, response):
        chat_history.append(f"User: {user_question.strip()}\nBot: {response['message']['content'].strip()}\n")

        # Save chat history to file
        with open(chat_history_file, "w") as file:
            file.writelines(chat_history)

    # Use a form to input the question and handle submission
    with st.form(key="question_form"):
        user_question = st.text_input("Enter your question:")
        submit_button = st.form_submit_button(label="Submit Question")

        if submit_button:
            if not pdf_text:
                st.write("Please upload a PDF file first.")
            elif not user_question:
                st.write("Please enter a question.")
            else:
                # Create prompt
                prompt = (
                    f"Based on the following content from the PDF:\n\n{pdf_text}\n\n"
                    f"Answer the following question:\n{user_question}"
                )

                # Display a loading spinner
                with st.spinner('This may take up to 1 minute...'):
                    # Use the prompt in the Ollama API
                    response = ollama.chat(model="llama3", messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ])
                    # Update the chat history
                    update_chat_history(user_question, response)

    # Display chat history above the input
    with st.container():
        for message in chat_history:
            st.write(message)
else:
    # Display sign-in or sign-up message
    st.markdown("# Sign in or Sign up", unsafe_allow_html=True)
    st.markdown("🡲 Sign in or sign up in the sidebar.", unsafe_allow_html=True)

    # Reset username field if user is not signed in
    if not is_authenticated:
        st.session_state.username = ""
