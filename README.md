# Hindi Staff Training App

A web application for internal staff training with Hindi video content and voice-based assessments.

## Features

- **Admin Dashboard**: Upload training videos and manage quiz questions
- **User Authentication**: Secure login/registration system
- **Video Training**: Watch Hindi training videos
- **Voice-based Quizzes**: Answer questions using voice input
- **AI-Powered Assessment**: Get instant feedback on your answers
- **Progress Tracking**: View your training history and scores

## Prerequisites

- Python 3.8+
- pip (Python package manager)

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd internal-staff-training
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your API keys and configuration

5. Create necessary directories:
   ```bash
   mkdir -p videos
   ```

## Running the Application

1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8501
   ```

## Usage

1. **Admin Access**
   - Log in with admin credentials
   - Upload training videos or add YouTube/Vimeo links
   - Create and manage quiz questions for each video

2. **User Access**
   - Register for a new account or log in
   - Browse available training modules
   - Watch videos and complete quizzes
   - View your progress and scores

## Configuration

Edit the `.env` file to configure:
- OpenAI API key for answer evaluation
- Google Cloud credentials for speech-to-text
- Database settings (in production)

## Deployment

For production deployment, consider using:
- Streamlit Cloud
- Heroku
- AWS/GCP with proper security configurations

## License

This project is for internal use only.

## Support

For support, please contact your system administrator.
