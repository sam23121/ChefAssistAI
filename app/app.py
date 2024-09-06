import streamlit as st
import time
import uuid

from assistant import qa_function
from db import save_conversation, save_feedback, get_recent_conversations, get_feedback_stats, init_db


def print_log(message):
    print(message, flush=True)



def main():
    print_log("Starting the Cheif Assistant application")
    st.title("Cheif Assistant")

    # Session state initialization
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
        print_log(f"New conversation started with ID: {st.session_state.conversation_id}")
    if 'count' not in st.session_state:
        st.session_state.count = 0
        print_log("Feedback count initialized to 0")

    

    # Model selection
    model_choice = st.selectbox(
        "Select a Free LLM Provider:",
        ["openrouter", "groq"]
    )
    print_log(f"User selected model: {model_choice}")

    
    # User input
    user_input = st.text_input("Enter your question:")

    if st.button("Ask"):
        print_log(f"User asked: '{user_input}'")
        with st.spinner('Processing...'):
            print_log(f"Getting answer from assistant using {model_choice}")
            start_time = time.time()
            answer_data = qa_function(user_input, model_choice)
            end_time = time.time()
            print_log(f"Answer received in {end_time - start_time:.2f} seconds")
            st.success("Completed!")
            st.write(answer_data['answer'])
            
            # Display monitoring information
            st.write(f"Response time: {answer_data['response_time']:.2f} seconds")
            st.write(f"Relevance: {answer_data['relevance']}")
            st.write(f"Model used: {answer_data['model_used']}")
            st.write(f"Total tokens: {answer_data['total_tokens']}")
            

            # Save conversation to database
            print_log("Saving conversation to database")
            save_conversation(st.session_state.conversation_id, user_input, answer_data)
            print_log("Conversation saved successfully")

    # Feedback buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("+1"):
            st.session_state.count += 1
            print_log(f"Positive feedback received. New count: {st.session_state.count}")
            if save_feedback(st.session_state.conversation_id, 1):
                st.success("Positive feedback saved")
            else:
                st.error("Failed to save positive feedback")

    with col2:
        if st.button("-1"):
            st.session_state.count -= 1
            print_log(f"Negative feedback received. New count: {st.session_state.count}")
            if save_feedback(st.session_state.conversation_id, -1):
                st.success("Negative feedback saved")
            else:
                st.error("Failed to save negative feedback")

    st.write(f"Current count: {st.session_state.count}")

    # Display recent conversations
    st.subheader("Recent Conversations")
    relevance_filter = st.selectbox("Filter by relevance:", ["All", "RELEVANT", "PARTLY_RELEVANT", "NON_RELEVANT"])
    recent_conversations = get_recent_conversations(limit=5, relevance=relevance_filter if relevance_filter != "All" else None)
    for conv in recent_conversations:
        st.write(f"Q: {conv[1]}")  
        st.write(f"A: {conv[2]}")  
        st.write(f"Relevance: {conv[5]}")  
        st.write(f"Model: {conv[3]}")  
        st.write("---")

    # Display feedback stats
    feedback_stats = get_feedback_stats()
    if feedback_stats:
        thumbs_up, thumbs_down = feedback_stats  # Unpack the tuple
        st.subheader("Feedback Statistics")
        st.write(f"Thumbs up: {thumbs_up}")
        st.write(f"Thumbs down: {thumbs_down}")
    else:
        print_log("No feedback stats available.")
        st.write("No feedback data available.")


print_log("Streamlit app loop completed")


if __name__ == "__main__":
    print_log("Chef Assistant application started")
    init_db()
    main()