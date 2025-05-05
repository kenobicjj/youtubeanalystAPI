import os
from flask import Flask, render_template, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import requests
import json
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

app = Flask(__name__)

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# YouTube API key (you'll need to get one from Google Cloud Console)
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')  # Load the API key from the environment

# Ollama API settings
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3"  # Use the name of your Gemma model in Ollama

def create_youtube_client():
    """Create and return a YouTube API client."""
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_video_id(youtube_url):
    """Extract the video ID from a YouTube URL."""
    video_id = None
    # Regular expressions for different YouTube URL formats
    youtube_regex_patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\?\/]+)',
        r'(?:youtube\.com\/embed\/)([^&\?\/]+)',
        r'(?:youtube\.com\/v\/)([^&\?\/]+)'
    ]
    
    for pattern in youtube_regex_patterns:
        match = re.search(pattern, youtube_url)
        if match:
            video_id = match.group(1)
            break
    
    return video_id

def get_video_details(video_id):
    """Get details about a YouTube video."""
    youtube = create_youtube_client()
    try:
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        response = request.execute()
        
        if response['items']:
            video_data = response['items'][0]
            return {
                'title': video_data['snippet']['title'],
                'description': video_data['snippet']['description'],
                'channel': video_data['snippet']['channelTitle'],
                'published_at': video_data['snippet']['publishedAt'],
                'view_count': video_data['statistics'].get('viewCount', 0),
                'like_count': video_data['statistics'].get('likeCount', 0),
                'comment_count': video_data['statistics'].get('commentCount', 0),
                'thumbnail': video_data['snippet']['thumbnails']['high']['url']
            }
        else:
            return None
    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")
        return None

def get_video_transcript(video_id):
    """Get the transcript of a YouTube video."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = ' '.join([item['text'] for item in transcript_list])
        return transcript
    except Exception as e:
        print(f"Error fetching transcript: {str(e)}")
        return None

def generate_summary_with_ollama(transcript, max_length=1000):
    """Generate a summary using Ollama with Gemma model."""
    # Truncate transcript if needed to avoid context length issues
    if len(transcript) > 10000:
        transcript = transcript[:10000]
    
    # Prepare prompt for Gemma
    prompt = f"""
    Please summarize the following YouTube video transcript. 
    Focus on the main points, key insights, and important details. 
    Keep your summary concise (about 3-5 paragraphs).

    TRANSCRIPT:
    {transcript}
    
    SUMMARY:
    """
    
    # Call Ollama API
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                }
            },
            timeout=60  # Increase timeout for longer transcripts
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "No summary could be generated.")
        else:
            print(f"Ollama API error: {response.status_code} - {response.text}")
            return "Error generating summary. Please check Ollama server."
    except Exception as e:
        print(f"Ollama request error: {str(e)}")
        return f"Error connecting to Ollama: {str(e)}"

def analyze_transcript(transcript):
    """Perform basic analysis on the transcript."""
    if not transcript:
        return {
            'word_count': 0,
            'sentence_count': 0,
            'average_word_length': 0,
            'keywords': []
        }
    
    # Tokenize text
    words = word_tokenize(transcript.lower())
    sentences = sent_tokenize(transcript)
    
    # Remove stopwords for keywords
    stop_words = set(stopwords.words('english'))
    words_no_stop = [word for word in words if word.isalnum() and word not in stop_words]
    
    # Count word frequency
    word_freq = {}
    for word in words_no_stop:
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1
    
    # Get top 10 keywords
    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Calculate average word length
    total_length = sum(len(word) for word in words if word.isalnum())
    avg_word_length = total_length / len([word for word in words if word.isalnum()]) if len([word for word in words if word.isalnum()]) > 0 else 0
    
    return {
        'word_count': len(words),
        'sentence_count': len(sentences),
        'average_word_length': round(avg_word_length, 2),
        'keywords': keywords
    }

def generate_keywords_with_ollama(transcript):
    """Generate keywords using Ollama with Gemma model."""
    # Truncate transcript if needed
    if len(transcript) > 6000:
        transcript = transcript[:6000]
    
    # Prepare prompt for Gemma
    prompt = f"""
    Extract the 5-10 most important keywords or keyphrases from this YouTube video transcript.
    Return them as a simple comma-separated list without explanations or additional text.

    TRANSCRIPT:
    {transcript}
    
    KEYWORDS:
    """
    
    # Call Ollama API
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            keywords_text = result.get("response", "")
            
            # Process the keywords
            keywords_list = [k.strip() for k in keywords_text.split(',')]
            keywords = [(k, 1) for k in keywords_list if k]  # Adding dummy count of 1
            
            return keywords[:10]  # Limit to 10 keywords
        else:
            print(f"Ollama API error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Ollama request error: {str(e)}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_ollama')
def check_ollama():
    """Check if Ollama is running and the model is available."""
    try:
        response = requests.post(
            "http://localhost:11434/api/tags",
            timeout=5
        )
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            return jsonify({"status": "ok", "models": models})
        else:
            return jsonify({"status": "error", "message": "Ollama server returned an error."})
    except requests.exceptions.ConnectionError:
        return jsonify({"status": "error", "message": "Cannot connect to Ollama server. Make sure it's running."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error checking Ollama: {str(e)}"})

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    youtube_url = data.get('url')
    selected_model = data.get('ollamaModel')  # Get the selected model from the request

    if not youtube_url:
        return jsonify({'error': 'No URL provided'}), 400
    
    video_id = get_video_id(youtube_url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    # Get video details
    video_details = get_video_details(video_id)
    if not video_details:
        return jsonify({'error': 'Could not fetch video details'}), 400
    
    # Get transcript
    transcript = get_video_transcript(video_id)
    if not transcript:
        return jsonify({
            'video': video_details,
            'error': 'Could not fetch transcript. The video might not have captions.',
            'summary': None,
            'analysis': None
        }), 200
    
    # Generate summary using Ollama/Gemma
    summary = generate_summary_with_ollama(transcript)
    
    # Analyze transcript
    analysis = analyze_transcript(transcript)
    
    # Optionally enhance keywords using Ollama/Gemma
    gemma_keywords = generate_keywords_with_ollama(transcript)
    if gemma_keywords:
        analysis['keywords'] = gemma_keywords
    
    return jsonify({
        'video': video_details,
        'summary': summary,
        'analysis': analysis,
        'using_gemma': True
    })

@app.route('/save_api_key', methods=['POST'])
def save_api_key():
    data = request.get_json()
    api_key = data.get('apiKey')

    if not api_key:
        return jsonify({'message': 'API key is required.'}), 400

    # Write the API key to the .env file
    with open('.env', 'w') as f:
        f.write(f'YOUTUBE_API_KEY={api_key}\n')

    return jsonify({'message': 'API key saved successfully.'})

if __name__ == '__main__':
    app.run(debug=True)