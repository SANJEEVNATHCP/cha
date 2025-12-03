"""Streamlit chatbot frontend."""
import streamlit as st
import requests
import json
from datetime import datetime
from typing import Optional

# Page configuration
st.set_page_config(
    page_title="Gen AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_URL = "http://localhost:8000"
if "api_url" not in st.session_state:
    st.session_state.api_url = API_URL

# Session state initialization
if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.user_id = None
    st.session_state.current_conversation_id = None
    st.session_state.conversations = []
    st.session_state.messages = []


def get_headers():
    """Get authorization headers with token."""
    if st.session_state.token:
        return {
            "Authorization": f"Bearer {st.session_state.token}",
            "Content-Type": "application/json"
        }
    return {"Content-Type": "application/json"}


def register_user(username: str, email: str, password: str) -> bool:
    """Register a new user."""
    try:
        response = requests.post(
            f"{st.session_state.api_url}/auth/register",
            json={"username": username, "email": email, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            st.session_state.user_id = data["user_id"]
            return True
        else:
            st.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error during registration: {str(e)}")
        return False


def login_user(email: str, password: str) -> bool:
    """Login a user."""
    try:
        response = requests.post(
            f"{st.session_state.api_url}/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            st.session_state.user_id = data["user_id"]
            return True
        else:
            st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error during login: {str(e)}")
        return False


def logout_user():
    """Logout the current user."""
    st.session_state.token = None
    st.session_state.user_id = None
    st.session_state.current_conversation_id = None
    st.session_state.conversations = []
    st.session_state.messages = []


def create_conversation(title: str = "New Conversation") -> Optional[int]:
    """Create a new conversation."""
    try:
        response = requests.post(
            f"{st.session_state.api_url}/chat/conversations",
            json={"title": title},
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["id"]
        else:
            st.error(f"Failed to create conversation: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error creating conversation: {str(e)}")
        return None


def load_conversations():
    """Load all conversations for the user."""
    try:
        response = requests.get(
            f"{st.session_state.api_url}/chat/conversations",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            st.session_state.conversations = response.json()
        else:
            st.error("Failed to load conversations")
    except Exception as e:
        st.error(f"Error loading conversations: {str(e)}")


def load_conversation_messages(conversation_id: int):
    """Load messages for a specific conversation."""
    try:
        response = requests.get(
            f"{st.session_state.api_url}/chat/conversations/{conversation_id}",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.messages = data["messages"]
            st.session_state.current_conversation_id = conversation_id
        else:
            st.error("Failed to load conversation")
    except Exception as e:
        st.error(f"Error loading conversation: {str(e)}")


def send_message(user_message: str) -> Optional[str]:
    """Send a message and get AI response."""
    if not st.session_state.current_conversation_id:
        st.error("No conversation selected")
        return None
    
    try:
        response = requests.post(
            f"{st.session_state.api_url}/chat/conversations/{st.session_state.current_conversation_id}/messages",
            json={
                "conversation_id": st.session_state.current_conversation_id,
                "message": user_message
            },
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            # Reload messages to get updated conversation
            load_conversation_messages(st.session_state.current_conversation_id)
            return data["assistant_message"]
        else:
            st.error(f"Failed to send message: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error sending message: {str(e)}")
        return None


def delete_conversation(conversation_id: int) -> bool:
    """Delete a conversation."""
    try:
        response = requests.delete(
            f"{st.session_state.api_url}/chat/conversations/{conversation_id}",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            load_conversations()
            if st.session_state.current_conversation_id == conversation_id:
                st.session_state.current_conversation_id = None
                st.session_state.messages = []
            return True
        else:
            st.error("Failed to delete conversation")
            return False
    except Exception as e:
        st.error(f"Error deleting conversation: {str(e)}")
        return False


# Main UI
def main():
    """Main Streamlit application."""
    
    # Authentication UI
    if not st.session_state.token:
        st.title("🤖 Gen AI Chatbot")
        
        auth_mode = st.radio("Choose an option:", ["Login", "Register"])
        
        col1, col2 = st.columns(2)
        
        if auth_mode == "Register":
            with col1:
                st.subheader("Create Account")
                reg_username = st.text_input("Username", key="reg_username")
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input("Password", type="password", key="reg_password")
                
                if st.button("Register", key="reg_button"):
                    if reg_username and reg_email and reg_password:
                        if register_user(reg_username, reg_email, reg_password):
                            st.success("Registration successful! Reloading...")
                            st.rerun()
                    else:
                        st.warning("Please fill in all fields")
        else:
            with col1:
                st.subheader("Login")
                login_email = st.text_input("Email", key="login_email")
                login_password = st.text_input("Password", type="password", key="login_password")
                
                if st.button("Login", key="login_button"):
                    if login_email and login_password:
                        if login_user(login_email, login_password):
                            st.success("Login successful! Reloading...")
                            st.rerun()
                    else:
                        st.warning("Please fill in all fields")
    else:
        # Main chat UI
        st.title("🤖 Gen AI Chatbot")
        
        # Sidebar
        with st.sidebar:
            st.subheader("User Menu")
            st.write(f"User ID: {st.session_state.user_id}")
            
            if st.button("Logout", key="logout_button"):
                logout_user()
                st.rerun()
            
            st.divider()
            
            st.subheader("Conversations")
            
            if st.button("➕ New Conversation", key="new_conv_button"):
                conv_id = create_conversation()
                if conv_id:
                    load_conversations()
                    load_conversation_messages(conv_id)
                    st.rerun()
            
            # Load conversations
            load_conversations()
            
            for conv in st.session_state.conversations:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    if st.button(
                        f"💬 {conv['title'][:30]}...",
                        key=f"conv_{conv['id']}",
                        use_container_width=True
                    ):
                        load_conversation_messages(conv['id'])
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"del_{conv['id']}", help="Delete"):
                        if delete_conversation(conv['id']):
                            st.rerun()
        
        # Main chat area
        if st.session_state.current_conversation_id:
            st.subheader(f"Conversation #{st.session_state.current_conversation_id}")
            
            # Display messages
            message_container = st.container()
            
            with message_container:
                for msg in st.session_state.messages:
                    if msg["role"] == "user":
                        with st.chat_message("user"):
                            st.write(msg["content"])
                    else:
                        with st.chat_message("assistant"):
                            st.write(msg["content"])
            
            st.divider()
            
            # Input area
            user_input = st.text_input("Type your message...", key="user_input")
            
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("Send", key="send_button"):
                    if user_input:
                        with st.spinner("Generating response..."):
                            response = send_message(user_input)
                            if response:
                                st.rerun()
        else:
            st.info("👈 Select a conversation from the sidebar or create a new one")


if __name__ == "__main__":
    main()
