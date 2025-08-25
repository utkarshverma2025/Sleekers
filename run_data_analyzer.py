import google.generativeai as genai
from PIL import Image
import pandas as pd
import fitz  # PyMuPDF
import docx
import sys
import os
import io

# --- 1. Configuration: PROVIDE YOUR GEMINI API KEY ---
try:
    # --- PASTE YOUR GEMINI API KEY HERE ---
    GEMINI_API_KEY = "AIzaSyAUB5leYMYn87eJalphWoaV0JujHRjmzuw"
    if GEMINI_API_KEY == "PASTE_YOUR_GOOGLE_GEMINI_API_KEY_HERE":
        print("Error: Please provide your Google Gemini API Key.")
        exit()
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"API Key configuration error: {e}")
    exit()

# --- 2. AI Model Initialization ---
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- 3. Data Processing Functions ---

def process_student_data_file(file_path: str) -> str:
    """
    Reads a file (Excel, PDF, DOCX, Image) and extracts the student data
    into a clean, text-based format (Markdown table).
    """
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
            if not data_string: # Fallback for text-only PDFs
                for page in doc:
                    data_string += page.get_text() + "\n"
        
        elif file_extension == '.docx':
            doc = docx.Document(file_path)
            for table in doc.tables:
                # Read table into a list of lists
                data = [[cell.text for cell in row.cells] for row in table.rows]
                # Create a pandas DataFrame
                df = pd.DataFrame(data[1:], columns=data[0])
                data_string += df.to_markdown(index=False) + "\n\n"
        
        elif file_extension in ['.png', '.jpg', '.jpeg']:
            img = Image.open(file_path)
            prompt = "Extract the tabular data of student information from this image. Present the data as a clean, text-based Markdown table."
            response = model.generate_content([prompt, img])
            data_string = response.text
        
        else:
            return f"Error: Unsupported file format '{file_extension}'."
            
        return data_string.strip()

    except Exception as e:
        return f"Error processing file '{os.path.basename(file_path)}': {e}"

def query_student_data(data_context: str, query: str) -> str:
    """
    Takes the extracted data and a natural language query, and returns an answer.
    """
    prompt = f"""
    You are an expert Data Analyst assistant for a teacher.
    Your task is to answer questions based ONLY on the provided student data context.
    Do not make up information. If the answer cannot be found in the data, state that clearly.
    Provide clear, concise, and friendly answers.

    --- STUDENT DATA CONTEXT ---
    {data_context}
    ---

    --- TEACHER'S QUESTION ---
    "{query}"
    ---

    Answer:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"An error occurred during AI analysis: {e}"

# --- 4. Main Program Execution ---
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    
    if len(sys.argv) != 3:
        print("Error: This script requires two arguments: a file path and a query.")
        exit()

    data_file_path = sys.argv[1]
    user_query = sys.argv[2]

    # Step 1: Process the uploaded file to extract data
    student_data = process_student_data_file(data_file_path)
    
    if student_data.startswith("Error"):
        print(student_data)
        exit()
    
    # Step 2: Use the extracted data and the user's query to get an answer
    answer = query_student_data(student_data, user_query)
    
    # Step 3: Print the final answer for the Streamlit app to capture
    print(answer)