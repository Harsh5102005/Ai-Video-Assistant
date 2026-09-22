# AI Video Assistant

AI Video Assistant is a Streamlit application that turns YouTube videos or local audio/video files into an English transcript, professional summary, action items, key decisions, open questions, and a transcript-grounded chat experience.

## Features

- YouTube URL and local audio/video upload support
- Audio conversion and chunking with FFmpeg/Pydub
- Local Whisper transcription
- Hindi/Hinglish to English translation using Whisper translate mode
- Meeting title generation and professional summary
- Action item, key decision, and open question extraction
- RAG chat over the transcript using LangChain and Chroma
- Streamlit dashboard with transcript search, chat suggestions, progress status, and report downloads

## Tech Stack

- Python
- Streamlit
- OpenAI Whisper
- LangChain
- Mistral AI
- ChromaDB
- HuggingFace sentence-transformer embeddings
- yt-dlp
- Pydub / FFmpeg

## Project Structure

```text
Ai-Video-Assistant/
|-- app.py                    # Streamlit UI
|-- main.py                   # CLI pipeline entry point
|-- core/
|   |-- extractor.py          # Action items, decisions, questions
|   |-- rag_engine.py         # Transcript-grounded chat chain
|   |-- summarize.py          # Title and summary generation
|   |-- transcribe.py         # Whisper transcription
|   `-- vector_store.py       # Chroma vector store
|-- utils/
|   `-- audio_processing.py   # Download, convert, and chunk audio
|-- requirements.txt
|-- .env.example
`-- .gitignore
```

## Prerequisites

Install these before running the project:

- Python 3.10 or newer
- FFmpeg installed and available in PATH
- A Mistral API key

The current code uses CUDA for Whisper and embeddings, so an NVIDIA GPU with CUDA is recommended. If you want CPU-only support, update the model device settings in `core/transcribe.py` and `core/vector_store.py`.

## Setup

1. Clone the repository:

```bash
git clone https://github.com/harsh5102005/Ai-Video-Assistant.git
cd Ai-Video-Assistant
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create your environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then add your API key:

```text
MISTRAL_API_KEY=your_mistral_api_key_here
```

## Run The App

```bash
streamlit run app.py
```

Then open the local URL shown by Streamlit.

## CLI Usage

You can also run the pipeline from the terminal:

```bash
python main.py
```

Enter a YouTube URL or a local file path when prompted.

## Notes

- `downloads/` contains generated audio files and is ignored by Git.
- `vector_db/` contains local Chroma database files and is ignored by Git.
- `.env` is ignored to protect API keys.
- Large audio/video files should not be committed to GitHub.

## Resume Description

AI Video Assistant - Built an end-to-end Streamlit application that converts YouTube videos and meeting recordings into searchable meeting intelligence. Implemented audio preprocessing, local Whisper transcription, Hindi/Hinglish-to-English translation, LLM-based summarization, action item extraction, and a LangChain/Chroma RAG chatbot for transcript-grounded Q&A using Mistral AI.
