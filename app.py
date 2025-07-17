import os
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime
import json
import base64
from io import BytesIO
import av
from streamlit_mic_recorder import mic_recorder
import wave
import numpy as np

# Create necessary directories
os.makedirs("recordings", exist_ok=True)
os.makedirs("videos", exist_ok=True)

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
    
    # Create tabs for different admin functions
    tab1, tab2 = st.tabs(["Upload Video", "Manage Questions"])
    
    with tab1:
        st.header("Upload Training Video")
        with st.form("video_upload"):
            video_title = st.text_input("Video Title")
            video_url = st.text_input("Video URL (YouTube/Vimeo)")
            video_file = st.file_uploader("Or upload video file", type=["mp4", "webm"])
            
            if st.form_submit_button("Save Video"):
                if not video_title:
                    st.error("Please enter a video title")
                elif not (video_url or video_file):
                    st.error("Please provide either a video URL or upload a video file")
                else:
                    # Save video details to database
                    with open(VIDEOS_DB, 'r') as f:
                        videos = json.load(f)
                    
                    video_id = f"vid_{len(videos['videos']) + 1}"
                    video_data = {
                        "id": video_id,
                        "title": video_title,
                        "url": video_url if video_url else None,
                        "file_path": f"videos/{video_id}.mp4" if video_file else None,
                        "questions": []
                    }
                    videos['videos'].append(video_data)
                    
                    # Save video file if uploaded
                    if video_file:
                        os.makedirs("videos", exist_ok=True)
                        with open(f"videos/{video_id}.mp4", "wb") as f:
                            f.write(video_file.getbuffer())
                    
                    with open(VIDEOS_DB, 'w') as f:
                        json.dump(videos, f)
                    st.success("Video saved successfully!")
    
    with tab2:
        st.header("Manage Quiz Questions")
        with open(VIDEOS_DB, 'r') as f:
            videos = json.load(f)
        
        if not videos['videos']:
            st.warning("No videos available. Please upload a video first.")
            return
        
        video_options = {v['id']: v['title'] for v in videos['videos']}
        selected_video = st.selectbox("Select Video", options=list(video_options.keys()), 
                                    format_func=lambda x: video_options[x])
        
        if selected_video:
            video = next(v for v in videos['videos'] if v['id'] == selected_video)
            
            st.subheader(f"Questions for: {video['title']}")
            
            # Display existing questions
            if 'questions' in video and video['questions']:
                for i, q in enumerate(video['questions']):
                    st.write(f"### Question {i+1}")
                    question = st.text_area(f"Question {i+1}", 
                                         value=q['question'], 
                                         key=f"q_{selected_video}_{i}")
                    answer = st.text_area(f"Answer {i+1}", 
                                       value=q['answer'], 
                                       key=f"a_{selected_video}_{i}")
                    
                    col1, col2 = st.columns([1, 6])
                    with col1:
                        if st.button(f"Update Question {i+1}", key=f"update_{selected_video}_{i}"):
                            video['questions'][i] = {
                                "question": question,
                                "answer": answer
                            }
                            with open(VIDEOS_DB, 'w') as f:
                                json.dump(videos, f)
                            st.success("Question updated!")
                    with col2:
                        if st.button(f"Delete Question {i+1}", key=f"delete_{selected_video}_{i}"):
                            del video['questions'][i]
                            with open(VIDEOS_DB, 'w') as f:
                                json.dump(videos, f)
                            st.success("Question deleted!")
                            st.rerun()
                    st.write("---")
            else:
                st.info("No questions added yet. Use the form below to add a new question.")
            
            # Add new question
            st.subheader("Add New Question")
            new_question = st.text_area("New Question", key=f"new_q_{selected_video}")
            new_answer = st.text_area("Expected Answer", key=f"new_a_{selected_video}")
            
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
                st.rerun()

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
        st.session_state.audio_frames = []
    
    current_q = st.session_state.current_question
    total_questions = len(video['questions'])
    
    if current_q < total_questions and not st.session_state.quiz_complete:
        question = video['questions'][current_q]
        
        st.subheader(f"Question {current_q + 1}/{total_questions}")
        st.write(question['question'])
        
        # Audio recording section
        st.write("Record your answer:")
        
        # Create a unique key for the audio recorder
        recorder_key = f"audio_recorder_{video_id}_{current_q}"
        
        # Audio recorder component
        st.write("Click the microphone to record your answer:")
        audio_data = audio_recorder(key=recorder_key)
        
        # Display audio player if audio was recorded
        if audio_data and 'audio_bytes' in audio_data:
            st.audio(audio_data['audio_bytes'], format=audio_data['mime_type'].split('/')[-1])
            
            # The audio file is already saved by audio_recorder, just get the path
            audio_path = audio_data['file_path']
            
            # Text area for the transcribed answer
            transcribed_text = st.text_area(
                "Transcribed answer (edit if needed):",
                value="",
                placeholder="Type or speak your answer...",
                key=f"transcription_{current_q}"
            )
            
            # Create columns for buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Submit Answer"):
                    if transcribed_text.strip():
                        st.session_state.answers[current_q] = {
                            'question': question['question'],
                            'expected_answer': question['answer'],
                            'user_answer': transcribed_text,
                            'audio_path': audio_path,
                            'score': None,
                            'feedback': None
                        }
                        
                        # Move to next question or complete quiz
                        if current_q < total_questions - 1:
                            st.session_state.current_question += 1
                        else:
                            st.session_state.quiz_complete = True
                        st.rerun()
                    else:
                        st.warning("Please type or record your answer")
            
            with col2:
                if st.button("Rerecord"):
                    # Clear the current recording
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                    st.rerun()
        else:
            st.info("Click the microphone button to start recording your answer")
            
            if st.button("Skip Question"):
                if current_q < total_questions - 1:
                    st.session_state.current_question += 1
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

def audio_recorder(key):
    """
    A simple audio recorder component using streamlit_mic_recorder
    Returns audio data in bytes if recording is available, None otherwise
    """
    try:
        # Display the recorder
        audio_data = mic_recorder(
            start_prompt="🎤 Record Answer",
            stop_prompt="⏹️ Stop Recording",
            just_once=True,
            use_container_width=False,
            format="webm",
            key=key
        )
        
        if audio_data:
            # The audio data is a dictionary with 'bytes' and 'mime_type' keys
            if isinstance(audio_data, dict) and 'bytes' in audio_data:
                audio_bytes = audio_data['bytes']
                mime_type = audio_data.get('mime_type', 'audio/webm')
                
                # Save the audio bytes to a file
                temp_path = f"recordings/recording_{key}.webm"
                with open(temp_path, "wb") as f:
                    f.write(audio_bytes)
                
                # Return the file path and MIME type
                return {
                    'audio_bytes': audio_bytes,
                    'mime_type': mime_type,
                    'file_path': temp_path
                }
            
        return None
        
    except Exception as e:
        st.error(f"Error recording audio: {str(e)}")
        return None

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
