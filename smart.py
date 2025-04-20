import streamlit as st
import requests
import os
import time
from dotenv import load_dotenv
import random

# Load environment variables from .env file
load_dotenv()

# Load API keys from environment variables
QA_KEY = os.getenv("HUGGINGFACE_QA_KEY")
SUMMARIZE_KEY = os.getenv("HUGGINGFACE_SUMMARY_KEY")

if not all([QA_KEY, SUMMARIZE_KEY]):
    st.error("⚠️ One or more API keys are missing. Check your .env file.")
    st.stop()

qa_headers = {"Authorization": f"Bearer {QA_KEY}"}
sum_headers = {"Authorization": f"Bearer {SUMMARIZE_KEY}"}

# Function to handle API calls with retries
def hf_api_with_retries(url, headers, payload, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e

# Function to generate normal questions (without API)
def generate_normal_questions(text):
    sentences = text.split(". ")
    questions = []
    
    # Generate questions based on key sentences
    for sentence in sentences:
        if len(sentence.split()) > 5:  # Skip very short sentences
            question = f"What is the meaning of '{sentence.strip()}?'"
            questions.append(question)
    
    return questions

# Function to generate multiple-choice questions (without API)
# Function to generate multiple-choice questions (without API)
def generate_mcq_questions(text):
    sentences = text.split(". ")
    mcqs = []
    
    # Generate MCQs based on key sentences
    for sentence in sentences:
        if len(sentence.split()) > 5:  # Skip very short sentences
            # Choose the correct answer
            correct_answer = sentence.strip()
            
            # Select 3 random distractors (sentences from text)
            distractors = random.sample([s for s in sentences if s != sentence], 3)
            
            options = [correct_answer] + distractors
            random.shuffle(options)
            
            question = f"What is described by the following statement?\n'{sentence.strip()}'"
            
            # Convert options to A, B, C, D format
            option_labels = ['A', 'B', 'C', 'D']
            labeled_options = {option_labels[i]: options[i] for i in range(len(options))}
            
            mcqs.append((question, labeled_options, correct_answer))
    
    return mcqs

# Streamlit UI setup
st.set_page_config(page_title="📚 Smart Study Assistant", layout="centered")
st.title("📚 Smart Study Assistant")

st.markdown("""
Choose what you want to do:
- 💬 Ask study questions
- 🧾 Summarize your notes
- ❓ Generate questions from topic
- 🃏 Generate flashcards
""")

option = st.sidebar.selectbox(
    "📌 Choose a feature", 
    ["Ask a Doubt", "Summarize Notes", "Generate Questions", "Flashcard Generator"])

# Ask a Doubt - Using Hugging Face QA API
if option == "Ask a Doubt":
    context = st.text_area("📘 Paste your study material (context):", height=200)
    question = st.text_input("❓ Type your question:")

    if st.button("Get Answer"):
        if context and question:
            with st.spinner("🤖 Thinking..."):
                payload = {"inputs": {"question": question, "context": context}}
                try:
                    response = hf_api_with_retries(
                        "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2",
                        headers=qa_headers,
                        payload=payload
                    )
                    result = response.json()
                    answer = result.get("answer", "No answer found.")
                    st.success("✅ Answer:")
                    st.write(answer)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        else:
            st.warning("Please provide both context and question.")

# Summarize Notes - Using Hugging Face Summarization API
elif option == "Summarize Notes":
    text = st.text_area("📝 Paste your notes:", height=250)
    if st.button("Summarize"):
        if text:
            with st.spinner("🧠 Summarizing..."):
                models = ["facebook/bart-large-cnn", "sshleifer/distilbart-cnn-12-6"]
                payload = {"inputs": text}
                summary = None

                for model in models:
                    for attempt in range(3):
                        try:
                            response = requests.post(
                                f"https://api-inference.huggingface.co/models/{model}",
                                headers=sum_headers,
                                json=payload
                            )
                            response.raise_for_status()
                            result = response.json()
                            if isinstance(result, list) and "summary_text" in result[0]:
                                summary = result[0]["summary_text"]
                                break
                        except:
                            time.sleep(1)
                            continue
                    if summary:
                        break

                if summary:
                    st.success("📌 Summary:")
                    st.write(summary)
                else:
                    st.error("❌ Failed to summarize text.")
        else:
            st.warning("Please paste some text.")

# Generate Questions - Without API
elif option == "Generate Questions":
    text = st.text_area("📚 Paste a topic or notes:", height=250)
    question_type = st.radio("Question Type", ["Normal Questions", "Multiple Choice"])

    if st.button("Generate Questions"):
        if text:
            st.write("Generating questions...")
            if question_type == "Normal Questions":
                questions = generate_normal_questions(text)
                for idx, question in enumerate(questions):
                    st.markdown(f"**Q{idx+1}:** {question}")

            elif question_type == "Multiple Choice":
                mcqs = generate_mcq_questions(text)
                for idx, mcq in enumerate(mcqs):
                    # Accessing tuple elements by index
                    question = mcq[0]
                    labeled_options = mcq[1]
                    correct_answer = mcq[2]
                    
                    # Display the question and options in A, B, C, D format
                    st.markdown(f"**Q{idx+1}:** {question}")
                    for label, option in labeled_options.items():
                        st.write(f"{label}. {option}")
                    
                    # Show the correct answer
                    correct_option = [label for label, option in labeled_options.items() if option == correct_answer][0]
                    st.write(f"**Correct Answer:** {correct_option}) {correct_answer}")
        else:
            st.warning("Please provide input text.")


# Flashcard Generator - Implemented in a previous section (you can modify as needed)
elif option == "Flashcard Generator":
    flashcard_text = st.text_area("🧠 Paste your notes or topic to create flashcards:", height=250)

    if st.button("Generate Flashcards"):
        if flashcard_text:
            with st.spinner("🧠 Creating flashcards..."):
                # Manual Flashcard Generation Logic
                flashcards = []
                flashcard_text_lines = flashcard_text.split('\n')

                for line in flashcard_text_lines:
                    if ':' in line:
                        term, definition = line.split(":", 1)
                        flashcards.append(f"{term.strip()}: {definition.strip()}")

                if flashcards:
                    st.success("📝 Flashcards:")
                    for fc in flashcards:
                        term, definition = fc.split(":", 1)
                        st.markdown(f"**{term.strip()}**: {definition.strip()}")
                else:
                    st.warning("⚠️ No flashcards created. Please ensure content is formatted with 'Term: Definition'.")
        else:
            st.warning("Please enter some notes or topic content.")