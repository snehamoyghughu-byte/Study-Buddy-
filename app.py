import re
from collections import Counter
from io import BytesIO

import streamlit as st
from PyPDF2 import PdfReader

st.set_page_config(page_title="Study Buddy", page_icon="📚", layout="wide")

STOP_WORDS = {
    "the", "and", "for", "that", "with", "this", "from", "have", "will", "into", "your",
    "their", "about", "what", "when", "where", "were", "been", "are", "is", "was", "were",
    "can", "could", "should", "would", "not", "but", "also", "then", "than", "each", "very",
    "more", "most", "some", "such", "only", "during", "because", "while", "through", "over",
    "under", "after", "before", "between", "within", "without", "other", "another", "these",
    "those", "they", "them", "their", "there", "here", "many", "much", "must", "may", "might"
}


def read_text_from_upload(uploaded_file):
    if uploaded_file is None:
        return ""

    if uploaded_file.name.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(uploaded_file.getvalue()))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text

    return uploaded_file.getvalue().decode("utf-8", errors="ignore")


def clean_text(text):
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sentences(text):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def summarize_text(text, max_sentences=3):
    sentences = split_sentences(text)
    if not sentences:
        return "No content found."

    words = [w.lower() for s in sentences for w in re.findall(r"[a-zA-Z]{3,}", s) if w.lower() not in STOP_WORDS]
    counts = Counter(words)

    scored = []
    for sentence in sentences:
        sentence_words = [w.lower() for w in re.findall(r"[a-zA-Z]{3,}", sentence) if w.lower() not in STOP_WORDS]
        score = sum(counts[word] for word in sentence_words)
        scored.append((score, sentence))

    scored.sort(key=lambda item: item[0], reverse=True)
    summary_sentences = [sentence for _, sentence in scored[:max_sentences]]
    return " ".join(summary_sentences)


def extract_topics(text, limit=6):
    words = [w.lower() for w in re.findall(r"[a-zA-Z]{4,}", text) if w.lower() not in STOP_WORDS]
    counts = Counter(words)
    return [word for word, _ in counts.most_common(limit)]


def generate_quiz(text, limit=4):
    sentences = split_sentences(text)
    quiz = []

    for index, sentence in enumerate(sentences[:limit], start=1):
        keywords = [w for w in re.findall(r"[a-zA-Z]{4,}", sentence) if w.lower() not in STOP_WORDS]
        if not keywords:
            continue
        keyword = keywords[0]
        quiz.append(
            {
                "question": f"{index}. What does '{keyword}' mean in this topic?",
                "answer": sentence,
            }
        )

    return quiz


def evaluate_answer(student_answer, expected_answer):
    expected_words = set(re.findall(r"[a-zA-Z]{3,}", expected_answer.lower()))
    student_words = set(re.findall(r"[a-zA-Z]{3,}", student_answer.lower()))

    if not expected_words:
        return 0.0

    overlap = len(expected_words & student_words)
    score = round((overlap / len(expected_words)) * 10, 1)
    return score


def build_flashcards(topics, text):
    cards = []
    sentences = split_sentences(text)

    for topic in topics:
        description = ""
        for sentence in sentences:
            if topic.lower() in sentence.lower():
                description = sentence
                break
        if not description:
            description = f"Learn more about {topic}."
        cards.append((topic, description))

    return cards


def build_revision_plan(topics, difficulty):
    plan = []
    days = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"]
    topic_chunks = [topics[i : i + 2] for i in range(0, len(topics), 2)]

    for day, chunk in zip(days, topic_chunks[:5]):
        plan.append(f"{day}: Review {', '.join(chunk)} and test yourself.")

    if difficulty == "Hard":
        plan.append("Extra challenge: Spend 20 minutes revising the hardest topic before bedtime.")

    return plan


st.title("📚 Study Buddy")
st.subheader("Turn your notes into a smarter study plan")

st.markdown(
    "Upload a PDF or text file, then get a summary, topic list, quiz, flashcards, and a revision plan in one place."
)

with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader("Upload notes or PDF", type=["txt", "pdf"])
    difficulty = st.selectbox("Choose difficulty", ["Easy", "Medium", "Hard"])
    study_mode = st.selectbox("Study plan style", ["Daily", "Weekend Review"])

    if st.button("Load sample notes"):
        with open("sample_notes.txt", "r", encoding="utf-8") as sample_file:
            st.session_state["raw_text"] = sample_file.read()

if "raw_text" not in st.session_state:
    st.session_state["raw_text"] = ""

if uploaded_file is not None:
    st.session_state["raw_text"] = read_text_from_upload(uploaded_file)

text = clean_text(st.session_state["raw_text"])

if not text:
    st.info("Upload a file or load the sample notes to begin.")
    st.stop()

summary = summarize_text(text)
topics = extract_topics(text)
quiz = generate_quiz(text)
flashcards = build_flashcards(topics, text)
revision_plan = build_revision_plan(topics, difficulty)

st.success("Study pack created successfully.")

tabs = st.tabs(["Summary", "Topics", "Quiz", "Flashcards", "Revision Plan"])

with tabs[0]:
    st.write(summary)

with tabs[1]:
    st.write("Main topics:")
    for topic in topics:
        st.checkbox(topic, value=False, disabled=True)

with tabs[2]:
    st.write("Try these quiz prompts:")
    for item in quiz:
        st.text_input(item["question"], key=f"q_{item['question']}")

    if st.button("Evaluate answers"):
        for item in quiz:
            key = f"q_{item['question']}"
            student_answer = st.session_state.get(key, "")
            score = evaluate_answer(student_answer, item["answer"])
            st.write(f"{item['question']} -> Score: {score}/10")

with tabs[3]:
    for front, back in flashcards:
        with st.expander(front):
            st.write(back)

with tabs[4]:
    st.write(f"Study mode: {study_mode}")
    for item in revision_plan:
        st.write(f"- {item}")

st.markdown("---")
st.caption("Built as an easy-to-understand starter project for Study Buddy AI.")