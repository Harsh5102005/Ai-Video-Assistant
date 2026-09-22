import os
import re
import tempfile
from html import escape
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from utils.audio_processing import process_input
from core.transcribe import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


APP_CSS = """
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1280px;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
    }

    [data-testid="stSidebar"] * {
        color: #f8fafc;
    }

    [data-testid="stSidebar"] .stButton > button {
        border: 0;
        font-weight: 700;
    }

    .hero {
        padding: 1.6rem 1.8rem;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        color: #0f172a;
        background:
            radial-gradient(circle at top right, rgba(20, 184, 166, .16), transparent 28rem),
            linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        margin-bottom: 1.2rem;
    }

    .hero h1 {
        margin: 0;
        color: #0f172a;
        font-size: clamp(2rem, 4vw, 3.5rem);
        font-weight: 800;
        line-height: 1.05;
        letter-spacing: 0;
    }

    .hero p {
        max-width: 780px;
        margin: .8rem 0 0;
        color: #475569;
        font-size: 1.05rem;
    }

    .stat-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: .8rem;
        margin: 1rem 0 1.2rem;
    }

    .stat-card {
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1rem;
        color: #0f172a;
        background: #ffffff;
    }

    .stat-label {
        color: #64748b;
        font-size: .78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .04em;
    }

    .stat-value {
        color: #0f172a;
        font-size: 1.45rem;
        font-weight: 800;
        margin-top: .2rem;
    }

    .panel {
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 1.1rem 1.2rem;
        color: #0f172a;
        background: #ffffff;
        height: 100%;
    }

    .panel h3 {
        margin-top: 0;
        color: #0f172a;
        font-weight: 800;
    }

    .panel p {
        color: #334155;
    }

    .muted {
        color: #64748b !important;
    }

    @media (max-width: 900px) {
        .stat-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }

    @media (max-width: 560px) {
        .stat-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
"""

st.markdown(APP_CSS, unsafe_allow_html=True)


def safe_filename(value: str, fallback: str = "video_assistant_report") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", value or fallback).strip("_")
    return cleaned[:80] or fallback


def transcript_stats(transcript: str) -> dict:
    words = re.findall(r"\b\w+\b", transcript or "")
    minutes = max(1, round(len(words) / 150)) if words else 0
    return {
        "words": len(words),
        "characters": len(transcript or ""),
        "reading_time": minutes,
    }


def build_markdown_report(result: dict) -> str:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""# {result["title"]}

Generated: {created_at}

## Summary

{result["summary"]}

## Action Items

{result["action_item"]}

## Key Decisions

{result["key_decisions"]}

## Open Questions

{result["open_questions"]}

## Transcript

{result["transcript"]}
"""


def run_pipeline(source: str, language: str = "english", progress_cb=None):
    def step(message: str):
        if progress_cb:
            progress_cb(message)

    step("Preparing source")
    chunks = process_input(source)

    step("Transcribing audio")
    transcript = transcribe_all(chunks, translate=(language.lower() in ["hindi", "hinglish"]))

    step("Generating meeting title")
    title = generate_title(transcript)

    step("Writing summary")
    summary = summarize(transcript)

    step("Finding action items")
    action_item = extract_action_items(transcript)

    step("Finding key decisions")
    decision = extract_key_decisions(transcript)

    step("Finding open questions")
    questions = extract_questions(transcript)

    step("Building chat index")
    rag_chain = build_rag_chain(transcript)

    return {
        "title": title.strip(),
        "transcript": transcript,
        "summary": summary,
        "action_item": action_item,
        "key_decisions": decision,
        "open_questions": questions,
        "rag_chain": rag_chain,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "language": language,
    }


def init_state():
    defaults = {
        "result": None,
        "chat_history": [],
        "processing": False,
        "status_history": [],
        "pending_question": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


with st.sidebar:
    st.title("AI Video Assistant")
    st.caption("Transcribe, summarize, extract decisions, and chat with long videos.")

    st.divider()

    input_mode = st.radio(
        "Source",
        ["YouTube URL", "Upload file"],
        index=0,
        horizontal=True,
    )

    source = None
    tmp_path_to_cleanup = None

    if input_mode == "YouTube URL":
        source = st.text_input(
            "Video URL",
            placeholder="https://youtube.com/watch?v=...",
            help="Paste a public YouTube video URL.",
        ).strip()
    else:
        uploaded_file = st.file_uploader(
            "Audio or video file",
            type=["mp4", "mp3", "wav", "m4a", "mov", "mkv", "webm"],
            help="Supported files are converted to WAV before transcription.",
        )
        if uploaded_file is not None:
            suffix = os.path.splitext(uploaded_file.name)[1]
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp_file.write(uploaded_file.read())
            tmp_file.close()
            source = tmp_file.name
            tmp_path_to_cleanup = tmp_file.name
            st.caption(f"Selected: {uploaded_file.name}")

    language = st.selectbox(
        "Audio language",
        ["english", "hindi", "hinglish"],
        index=0,
        help="Hindi and Hinglish are translated to English during transcription.",
    )

    st.divider()

    run_clicked = st.button(
        "Run analysis",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.processing or not source,
    )

    if st.session_state.result:
        if st.button("Start over", use_container_width=True):
            st.session_state.result = None
            st.session_state.chat_history = []
            st.session_state.status_history = []
            st.session_state.pending_question = None
            st.rerun()

    st.divider()
    st.caption("Tip: use shorter files while testing. Whisper and embeddings can take time on CPU.")


if run_clicked and source:
    st.session_state.processing = True
    st.session_state.chat_history = []
    st.session_state.status_history = []

    status_box = st.empty()
    progress_bar = st.progress(0, text="Starting")
    total_steps = 8
    steps_seen = {"count": 0}

    def progress_cb(message: str):
        steps_seen["count"] += 1
        pct = min(int(steps_seen["count"] / total_steps * 100), 96)
        st.session_state.status_history.append(message)
        progress_bar.progress(pct, text=message)
        status_box.info(message)

    try:
        with st.spinner("Processing your video. This can take a few minutes."):
            result = run_pipeline(source, language, progress_cb=progress_cb)
        st.session_state.result = result
        progress_bar.progress(100, text="Analysis complete")
        status_box.success("Analysis complete")
    except Exception as error:
        st.session_state.result = None
        status_box.error(f"Something went wrong: {error}")
    finally:
        st.session_state.processing = False
        if tmp_path_to_cleanup and os.path.exists(tmp_path_to_cleanup):
            try:
                os.remove(tmp_path_to_cleanup)
            except OSError:
                pass


result = st.session_state.result

if not result:
    st.markdown(
        """
        <section class="hero">
            <h1>Turn videos into usable meeting intelligence.</h1>
            <p>
                Upload a recording or paste a YouTube URL, then get an English transcript,
                a professional summary, action items, decisions, open questions, and a chat
                assistant grounded in the transcript.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div class="panel"><h3>1. Add a source</h3><p class="muted">Paste a URL or upload an audio/video file from the sidebar.</p></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="panel"><h3>2. Run analysis</h3><p class="muted">The app transcribes, summarizes, and builds a searchable chat index.</p></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="panel"><h3>3. Export or ask</h3><p class="muted">Download a report, search the transcript, or ask questions in chat.</p></div>',
            unsafe_allow_html=True,
        )

    if st.session_state.status_history:
        with st.expander("Last run progress"):
            for item in st.session_state.status_history:
                st.write(f"- {item}")
else:
    stats = transcript_stats(result["transcript"])
    report = build_markdown_report(result)
    filename_base = safe_filename(result["title"])
    title_html = escape(result["title"])

    st.markdown(
        f"""
        <section class="hero">
            <p class="muted">Analysis ready · {result.get("created_at", "")}</p>
            <h1>{title_html}</h1>
            <p>Review the summary, inspect the transcript, export the report, or ask focused questions about the video.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="stat-grid">
            <div class="stat-card"><div class="stat-label">Words</div><div class="stat-value">{stats["words"]:,}</div></div>
            <div class="stat-card"><div class="stat-label">Characters</div><div class="stat-value">{stats["characters"]:,}</div></div>
            <div class="stat-card"><div class="stat-label">Reading Time</div><div class="stat-value">{stats["reading_time"]} min</div></div>
            <div class="stat-card"><div class="stat-label">Language Mode</div><div class="stat-value">{result.get("language", "english").title()}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    export_col1, export_col2, export_col3 = st.columns([1, 1, 2])
    with export_col1:
        st.download_button(
            "Download report",
            data=report,
            file_name=f"{filename_base}_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with export_col2:
        st.download_button(
            "Download transcript",
            data=result["transcript"],
            file_name=f"{filename_base}_transcript.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with export_col3:
        if st.session_state.status_history:
            with st.expander("Processing timeline"):
                for index, item in enumerate(st.session_state.status_history, start=1):
                    st.write(f"{index}. {item}")

    tab_summary, tab_transcript, tab_chat = st.tabs(
        ["Summary", "Transcript", "Chat"]
    )

    with tab_summary:
        st.subheader("Professional Summary")
        st.markdown(result["summary"])

        insight_col1, insight_col2, insight_col3 = st.columns(3)
        with insight_col1:
            with st.container(border=True):
                st.subheader("Action Items")
                st.markdown(result["action_item"])
        with insight_col2:
            with st.container(border=True):
                st.subheader("Key Decisions")
                st.markdown(result["key_decisions"])
        with insight_col3:
            with st.container(border=True):
                st.subheader("Open Questions")
                st.markdown(result["open_questions"])

    with tab_transcript:
        search_term = st.text_input("Search transcript", placeholder="Type a word or phrase")
        transcript_text = result["transcript"]

        if search_term:
            matches = [m.start() for m in re.finditer(re.escape(search_term), transcript_text, re.IGNORECASE)]
            st.caption(f"{len(matches)} match(es) found")
            if matches:
                first = matches[0]
                start = max(0, first - 350)
                end = min(len(transcript_text), first + 650)
                st.text_area(
                    "First match context",
                    transcript_text[start:end],
                    height=180,
                )

        st.text_area(
            "Full transcript",
            transcript_text,
            height=520,
        )

    with tab_chat:
        st.subheader("Ask the transcript")
        st.caption("Answers are based on the indexed transcript context.")

        prompt_col1, prompt_col2, prompt_col3 = st.columns(3)
        sample_questions = [
            "What are the main takeaways?",
            "What action items were assigned?",
            "What risks or concerns were discussed?",
        ]
        for column, sample in zip([prompt_col1, prompt_col2, prompt_col3], sample_questions):
            with column:
                if st.button(sample, use_container_width=True):
                    st.session_state.pending_question = sample
                    st.rerun()

        if st.button("Clear chat"):
            st.session_state.chat_history = []
            st.session_state.pending_question = None
            st.rerun()

        for question_text, answer_text in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(question_text)
            with st.chat_message("assistant"):
                st.write(answer_text)

        question = st.session_state.pending_question or st.chat_input("Ask something about this video")
        st.session_state.pending_question = None

        if question:
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                with st.spinner("Searching the transcript"):
                    try:
                        answer = ask_question(result["rag_chain"], question)
                    except Exception as error:
                        answer = f"Error answering question: {error}"
                st.write(answer)
            st.session_state.chat_history.append((question, answer))
