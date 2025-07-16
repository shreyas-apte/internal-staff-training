import os
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Hindi Training App",
    page_icon="🎓",
    layout="wide"
)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_video' not in st.session_state:
    st.session_state.current_video = None
if 'quiz_questions' not in st.session_state:
    st.session_state.quiz_questions = {}

# Sample data (in production, this would be in a database)
VIDEOS_DB = "videos.json"
USERS_DB = "users.json"
RESULTS_DB = "results.csv"

def load_data():
    """Load data from JSON files"""
    if not os.path.exists(VIDEOS_DB):
        with open(VIDEOS_DB, 'w') as f:
            json.dump({"videos": []}, f)
    
    if not os.path.exists(USERS_DB):
        with open(USERS_DB, 'w') as f:
            json.dump({"users": []}, f)
    
    if not os.path.exists(RESULTS_DB):
        pd.DataFrame(columns=["user_id", "video_id", "score", "feedback", "timestamp"]).to_csv(RESULTS_DB, index=False)

def admin_page():
    """Admin interface for uploading videos and questions"""
    st.title("Admin Dashboard")
    
    with st.expander("Upload Training Video", expanded=False):
        with st.form("video_upload"):
            video_title = st.text_input("Video Title")
            video_url = st.text_input("Video URL (YouTube/Vimeo)")
            video_file = st.file_uploader("Or upload video file", type=["mp4", "webm"])
            
            if st.form_submit_button("Save Video"):
                # Save video details to database
                with open(VIDEOS_DB, 'r') as f:
                    videos = json.load(f)
                
                video_id = f"vid_{len(videos['videos']) + 1}"
                videos['videos'].append({
                    "id": video_id,
                    "title": video_title,
                    "url": video_url if video_url else None,
                    "file_path": f"videos/{video_id}.mp4" if video_file else None,
                    "questions": []
                })
                
                # Save video file if uploaded
                if video_file:
                    os.makedirs("videos", exist_ok=True)
                    with open(f"videos/{video_id}.mp4", "wb") as f:
                        f.write(video_file.getbuffer())
                
                with open(VIDEOS_DB, 'w') as f:
                    json.dump(videos, f)
                st.success("Video saved successfully!")
    
    # Add/edit questions for videos
    with st.expander("Manage Quiz Questions", expanded=True):
        with open(VIDEOS_DB, 'r') as f:
            videos = json.load(f)
        
        video_options = {v['id']: v['title'] for v in videos['videos']}
        selected_video = st.selectbox("Select Video", options=list(video_options.keys()), 
                                    format_func=lambda x: video_options[x])
        
        if selected_video:
            video = next(v for v in videos['videos'] if v['id'] == selected_video)
            
            st.subheader(f"Questions for: {video['title']}")
            
            # Display existing questions
            for i, q in enumerate(video['questions']):
                with st.expander(f"Question {i+1}"):
                    question = st.text_area(f"Question {i+1}", value=q['question'], key=f"q_{i}")
                    answer = st.text_area(f"Answer {i+1}", value=q['answer'], key=f"a_{i}")
                    
                    if st.button(f"Update Question {i+1}"):
                        video['questions'][i] = {
                            "question": question,
                            "answer": answer
                        }
                        with open(VIDEOS_DB, 'w') as f:
                            json.dump(videos, f)
                        st.success("Question updated!")
            
            # Add new question
            st.subheader("Add New Question")
            new_question = st.text_area("New Question")
            new_answer = st.text_area("Expected Answer")
            
            if st.button("Add Question") and new_question and new_answer:
                if 'questions' not in video:
                    video['questions'] = []
                video['questions'].append({
                    "question": new_question,
                    "answer": new_answer
                })
                with open(VIDEOS_DB, 'w') as f:
                    json.dump(videos, f)
                st.success("Question added!")

def user_login():
    """User login/registration"""
    st.title("Welcome to Hindi Training")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login"):
                with open(USERS_DB, 'r') as f:
                    users = json.load(f)
                
                user = next((u for u in users['users'] if u['email'] == email and u['password'] == password), None)
                
                if user:
                    st.session_state.user_id = user['id']
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    
    with tab2:
        with st.form("register"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Register"):
                if password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    with open(USERS_DB, 'r') as f:
                        users = json.load(f)
                    
                    if any(u['email'] == email for u in users['users']):
                        st.error("Email already registered!")
                    else:
                        user_id = f"user_{len(users['users']) + 1}"
                        users['users'].append({
                            "id": user_id,
                            "name": name,
                            "email": email,
                            "password": password
                        })
                        
                        with open(USERS_DB, 'w') as f:
                            json.dump(users, f)
                        
                        st.session_state.user_id = user_id
                        st.success("Registration successful!")
                        st.rerun()

def training_page():
    """Main training interface for users"""
    st.title("Training Modules")
    
    with open(VIDEOS_DB, 'r') as f:
        videos = json.load(f)
    
    if not videos['videos']:
        st.warning("No training videos available yet. Please check back later.")
        return
    
    # Display available videos
    for video in videos['videos']:
        with st.expander(video['title'], expanded=False):
            if video['url']:
                st.video(video['url'])
            elif video['file_path'] and os.path.exists(video['file_path']):
                st.video(video['file_path'])
            
            if st.button(f"Take Quiz for {video['title']}", key=f"quiz_{video['id']}"):
                st.session_state.current_video = video['id']
                st.session_state.quiz_questions = {}
                st.rerun()

def quiz_page():
    """Quiz interface after watching a video"""
    video_id = st.session_state.current_video
    
    with open(VIDEOS_DB, 'r') as f:
        videos = json.load(f)
    
    video = next(v for v in videos['videos'] if v['id'] == video_id)
    
    st.title(f"Quiz: {video['title']}")
    
    if 'questions' not in video or not video['questions']:
        st.warning("No questions available for this video yet.")
        if st.button("Back to Training"):
            st.session_state.current_video = None
            st.rerun()
        return
    
    # Initialize session state for quiz
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
        st.session_state.answers = {}
        st.session_state.quiz_complete = False
    
    current_q = st.session_state.current_question
    total_questions = len(video['questions'])
    
    if current_q < total_questions and not st.session_state.quiz_complete:
        question = video['questions'][current_q]
        
        st.subheader(f"Question {current_q + 1}/{total_questions}")
        st.write(question['question'])
        
        # Voice recording component
        st.write("Record your answer:")
        st.info("Click the microphone button to start/stop recording")
        
        # This is a placeholder for the actual voice recording component
        # In a real implementation, you would use a library like streamlit-webrtc
        audio_data = st.audio("path/to/recorded/audio.wav")
        
        # Placeholder for transcription
        transcribed_text = st.text_area("Transcribed answer (edit if needed):")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Submit Answer"):
                if transcribed_text.strip():
                    st.session_state.answers[current_q] = {
                        'question': question['question'],
                        'expected_answer': question['answer'],
                        'user_answer': transcribed_text,
                        'score': None,
                        'feedback': None
                    }
                    
                    # In a real implementation, you would call the AI here to evaluate the answer
                    # For now, we'll just move to the next question
                    
                    if current_q < total_questions - 1:
                        st.session_state.current_question += 1
                        st.rerun()
                    else:
                        st.session_state.quiz_complete = True
                        st.rerun()
                else:
                    st.warning("Please record or type your answer")
        
        with col2:
            if st.button("Skip Question"):
                if current_q < total_questions - 1:
                    st.session_state.current_question += 1
                    st.rerun()
                else:
                    st.session_state.quiz_complete = True
                    st.rerun()
    
    elif st.session_state.quiz_complete:
        st.success("Quiz Complete!")
        
        # Calculate score (placeholder)
        score = len(st.session_state.answers) / total_questions * 100
        
        # Save results
        results_df = pd.read_csv(RESULTS_DB)
        results_df = pd.concat([results_df, pd.DataFrame([{
            'user_id': st.session_state.user_id,
            'video_id': video_id,
            'score': score,
            'feedback': "Good job!",  # This would come from the AI in a real implementation
            'timestamp': datetime.now().isoformat()
        }])], ignore_index=True)
        results_df.to_csv(RESULTS_DB, index=False)
        
        st.write(f"Your score: {score:.1f}%")
        
        # Display answers
        st.subheader("Your Answers")
        for i, (q, a) in enumerate(st.session_state.answers.items()):
            with st.expander(f"Question {q + 1}"):
                st.write(f"**Question:** {a['question']}")
                st.write(f"**Your Answer:** {a['user_answer']}")
                st.write(f"**Feedback:** {a.get('feedback', 'No feedback available')}")
        
        if st.button("Back to Training"):
            st.session_state.current_video = None
            st.session_state.quiz_complete = False
            st.session_state.current_question = 0
            st.rerun()

def results_page():
    """View training results"""
    st.title("Your Training Results")
    
    if not os.path.exists(RESULTS_DB):
        st.warning("No results found.")
        return
    
    results_df = pd.read_csv(RESULTS_DB)
    user_results = results_df[results_df['user_id'] == st.session_state.user_id]
    
    if user_results.empty:
        st.warning("No results found for your account.")
        return
    
    # Load video titles
    with open(VIDEOS_DB, 'r') as f:
        videos = json.load(f)
    
    video_map = {v['id']: v['title'] for v in videos['videos']}
    
    # Add video titles to results
    user_results['video_title'] = user_results['video_id'].map(video_map)
    
    # Display overall stats
    st.subheader("Overall Performance")
    avg_score = user_results['score'].mean()
    st.metric("Average Score", f"{avg_score:.1f}%")
    
    # Display results by video
    st.subheader("Results by Training Module")
    for _, row in user_results.iterrows():
        with st.expander(f"{row['video_title']} - {row['score']}%"):
            st.write(f"**Date Completed:** {row['timestamp']}")
            st.write(f"**Score:** {row['score']}%")
            st.write(f"**Feedback:** {row.get('feedback', 'No feedback available')}")

def main():
    # Load data
    load_data()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Hindi Training App")
        
        if st.session_state.user_id:
            # User is logged in
            with open(USERS_DB, 'r') as f:
                users = json.load(f)
            
            user = next(u for u in users['users'] if u['id'] == st.session_state.user_id)
            st.write(f"Welcome, {user['name']}!")
            
            if st.button("Logout"):
                st.session_state.user_id = None
                st.session_state.current_video = None
                st.rerun()
            
            menu = option_menu(
                menu_title=None,
                options=["Training", "Results", "Admin"],
                icons=["play-circle", "bar-chart", "gear"],
                default_index=0
            )
        else:
            menu = None
    
    # Show appropriate page based on menu selection
    if not st.session_state.user_id:
        user_login()
    elif menu == "Training":
        if st.session_state.current_video is not None:
            quiz_page()
        else:
            training_page()
    elif menu == "Results":
        results_page()
    elif menu == "Admin":
        # In a real app, you would check if the user is an admin
        admin_page()

if __name__ == "__main__":
    main()
