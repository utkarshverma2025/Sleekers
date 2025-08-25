import streamlit as st
import subprocess
import os
import sys
import io
import pandas as pd
import fitz  # PyMuPDF
import docx
from PIL import Image
import google.generativeai as genai

# -------------------------------
# 1. CONFIGURATION: API KEY
# -------------------------------
try:
    GEMINI_API_KEY = "PASTE_YOUR_GOOGLE_GEMINI_API_KEY_HERE"  # <-- PUT YOUR KEY HERE
    if GEMINI_API_KEY == "PASTE_YOUR_GOOGLE_GEMINI_API_KEY_HERE":
        st.error("⚠️ Please provide your Google Gemini API Key inside app.py")
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"API Key configuration error: {e}")
    st.stop()

# Initialize model
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# -------------------------------
# 2. DATA ANALYZER FUNCTIONS
# -------------------------------
def process_student_data_file(file_path: str) -> str:
    """Extracts student data from Excel, PDF, DOCX, or Image files into Markdown tables/text."""
    file_extension = os.path.splitext(file_path)[1].lower()
    data_string = ""

    try:
        if file_extension == '.xlsx':
            df = pd.read_excel(file_path)
            data_string = df.to_markdown(index=False)

        elif file_extension == '.pdf':
            doc = fitz.open(file_path)
            for page in doc:
                tables = page.find_tables()
                for table in tables:
                    df = table.to_pandas()
                    data_string += df.to_markdown(index=False) + "\n\n"
            if not data_string:  # fallback if no tables
                for page in doc:
                    data_string += page.get_text() + "\n"

        elif file_extension == '.docx':
            doc = docx.Document(file_path)
            for table in doc.tables:
                data = [[cell.text for cell in row.cells] for row in table.rows]
                if len(data) > 1:
                    df = pd.DataFrame(data[1:], columns=data[0])
                    data_string += df.to_markdown(index=False) + "\n\n"

        elif file_extension in ['.png', '.jpg', '.jpeg']:
            img = Image.open(file_path)
            prompt = "Extract the student data from this image as a Markdown table."
            response = model.generate_content([prompt, img])
            data_string = response.text

        else:
            return f"Error: Unsupported file format '{file_extension}'."

        return data_string.strip() if data_string else "⚠️ No data found."

    except Exception as e:
        return f"Error processing file '{os.path.basename(file_path)}': {e}"

def query_student_data(data_context: str, query: str) -> str:
    """Ask AI a question about the uploaded student data."""
    prompt = f"""
    You are an expert Data Analyst assistant for a teacher.
    Answer the teacher’s question using ONLY the provided student data context.
    If answer not found, say so clearly.

    --- STUDENT DATA CONTEXT ---
    {data_context}
    ---

    --- TEACHER'S QUESTION ---
    "{query}"
    ---
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI analysis error: {e}"

# -------------------------------
# 3. STREAMLIT DASHBOARD
# -------------------------------
st.set_page_config(
    page_title="SleekAI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "view" not in st.session_state:
    st.session_state.view = "home"

def run_script(script_path, *args):
    """Helper for calling external student tools (questions, flashcards, etc.)"""
    try:
        result = subprocess.run(
            ['python', script_path, *args],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        return result.stdout
    except Exception as e:
        return f"Error running {script_path}: {e}"

# -------------------------------
# HOME PAGE
# -------------------------------
if st.session_state.view == "home":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍🏫 Teacher", use_container_width=True):
            st.session_state.view = "teacher"
            st.rerun()
    with col2:
        if st.button("🎓 Student", use_container_width=True):
            st.session_state.view = "student"
            st.rerun()

# -------------------------------
# TEACHER DASHBOARD
# -------------------------------
elif st.session_state.view == "teacher":
    with st.sidebar:
        if st.button("⬅️ Back to Home", use_container_width=True):
            st.session_state.view = "home"
            st.rerun()

    st.title("👨‍🏫 Teacher Dashboard")

    if st.button("Student Performances", use_container_width=True):
        st.info("📂 Assignment upload functionality coming soon...")

    # 🔹 STUDENT DETAILS WITH DATA ANALYZER
    if st.button("Student Details", use_container_width=True):
        st.subheader("📊 Upload & Analyze Student Data")

        uploaded_file = st.file_uploader(
            "Upload student data file (Excel, PDF, DOCX, or Image)",
            type=["xlsx", "pdf", "docx", "png", "jpg", "jpeg"]
        )

        if uploaded_file is not None:
            temp_dir = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, uploaded_file.name)

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success("✅ File uploaded successfully!")
            st.write("📄 Extracted Data:")
            student_data = process_student_data_file(temp_path)
            st.text_area("Extracted Data", value=student_data, height=300)

            teacher_query = st.text_input("🔎 Ask a question about this data:")
            if st.button("Get Answer"):
                if student_data and not student_data.startswith("Error"):
                    answer = query_student_data(student_data, teacher_query)
                    st.subheader("AI Answer")
                    st.write(answer)
                else:
                    st.error("⚠️ No valid data available for querying.")

    if st.button("Class Schedules", use_container_width=True):
        st.info("📝 Test paper creation functionality coming soon...")

# -------------------------------
# STUDENT DASHBOARD
# -------------------------------
elif st.session_state.view == "student":
    with st.sidebar:
        if st.button("⬅️ Back to Home", use_container_width=True):
            st.session_state.view = "home"
            st.rerun()

    st.title("🎓 Student Dashboard")

    uploaded_file = st.file_uploader(
        "📤 Upload your notes (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"], key="student_notes"
    )

    if uploaded_file is not None:
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_image_path = os.path.join(temp_dir, uploaded_file.name)

        with open(temp_image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("✅ Notes uploaded successfully!")
        st.image(uploaded_file, caption="Your Notes", width=300)

        if st.button("🧠 Generate Questions", use_container_width=True):
            with st.spinner("AI is crafting questions..."):
                output = run_script("run_question_generator.py", temp_image_path)
                st.subheader("Generated Questions")
                st.text_area("Results", value=output, height=300)

        if st.button("📜 Summarize Notes", use_container_width=True):
            with st.spinner("AI is summarizing notes..."):
                output = run_script("run_summarizer.py", temp_image_path)
                st.subheader("Summary")
                st.text_area("Results", value=output, height=300)

        if st.button("🃏 Create Flashcards", use_container_width=True):
            with st.spinner("AI is generating flashcards..."):
                output = run_script("run_flashcard_generator.py", temp_image_path)
                st.subheader("Flashcards")
                st.text_area("Results", value=output, height=300)

    # --- AI Test Analysis ---
    st.markdown("---")
    st.header("✍️ AI Test Paper Analysis")
    col1, col2 = st.columns(2)
    with col1:
        question_paper = st.file_uploader("1. Upload Question Paper", type=["pdf", "png", "jpg"], key="q_paper")
    with col2:
        answer_sheet = st.file_uploader("2. Upload Answer Sheet", type=["pdf", "png", "jpg"], key="a_sheet")

    if st.button("Analyze My Test", use_container_width=True):
        if question_paper and answer_sheet:
            temp_dir = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)

            q_path = os.path.join(temp_dir, question_paper.name)
            a_path = os.path.join(temp_dir, answer_sheet.name)

            with open(q_path, "wb") as f:
                f.write(question_paper.getbuffer())
            with open(a_path, "wb") as f:
                f.write(answer_sheet.getbuffer())

            with st.spinner("AI is evaluating your test..."):
                output = run_script("run_test_analyzer.py", q_path, a_path)
                st.subheader("Test Analysis")
                st.markdown(output)
        else:
            st.warning("⚠️ Please upload both the question paper and the answer sheet.")
