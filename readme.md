# YouTube Video Analyzer

A Flask-based web application that analyzes YouTube videos by fetching their details, transcripts, and generating summaries and keyword analyses using the Ollama API.

## Diagram

![YouTube API Class Diagram](https://github.com/kenobicjj/youtubeanalystAPI/blob/main/Youtube

## Features

- Enter a YouTube video URL to analyze.
- Fetch video details such as title, channel, views, likes, and comments.
- Retrieve and summarize the video transcript.
- Analyze the transcript for word count, sentence count, average word length, and keywords.
- Select from available Ollama models for generating summaries and keywords.

## Requirements

- Python 3.x
- Flask
- Google API Client
- NLTK
- YouTube Transcript API
- Ollama API

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/youtube-video-analyzer.git
   cd youtube-video-analyzer
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install the required packages:**

   ```bash
   pip install -r requirements.txt
   ```

5. **Set up your environment variables:**

   Create a `.env` file in the root directory and add your YouTube API key:

   ```plaintext
   YOUTUBE_API_KEY=your_youtube_api_key
   ```

## Usage

1. **Run the application:**

   ```bash
   python youtube-analyzer.py
   ```

2. **Open your web browser and navigate to:**

   ```
   http://127.0.0.1:5000/
   ```

3. **Enter a YouTube video URL and click "Analyze".**

4. **View the results, including video details, summary, and analysis.**

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - The web framework used.
- [Google API Client](https://github.com/googleapis/google-api-python-client) - For interacting with the YouTube API.
- [NLTK](https://www.nltk.org/) - For natural language processing tasks.
- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api) - For fetching video transcripts.
- [Ollama](https://ollama.com/) - For generating summaries and keywords.
