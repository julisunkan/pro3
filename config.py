import os

# Groq API
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_MODEL = 'llama-3.3-70b-versatile'

# Flask
SECRET_KEY = os.environ.get('SECRET_KEY', 'cold-email-secret-2024')
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

# Email templates
TEMPLATES = {
    'short_pitch': 'Short Pitch',
    'problem_solution': 'Problem-Solution',
    'quick_intro': 'Quick Intro',
    'partnership': 'Partnership',
}

TONES = ['formal', 'friendly', 'persuasive', 'humorous']
