import google.generativeai as genai
from PIL import Image
import sys
import os
import json
import fitz  # PyMuPDF for handling PDFs
import io

# --- 1. Configuration: PROVIDE YOUR GEMINI API KEY ---
try:
    GEMINI_API_KEY = "AIzaSyAUB5leYMYn87eJalphWoaV0JujHRjmzuw"
    if GEMINI_API_KEY == "PASTE_YOUR_GOOGLE_GEMINI_API_KEY_HERE":
        print("Error: Please provide your Google Gemini API Key.")
        exit()
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"API Key configuration error: {e}")
    exit()

# --- 2. AI Model Initialization ---
# Using the Pro model for the highest quality analysis of complex documents.
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- 3. Function Definitions ---

def process_file(file_path: str) -> list:
    """
    NEW: This function reads a file (image or PDF) and returns a list of PIL Image objects.
    """
    images = []
    try:
        if file_path.lower().endswith('.pdf'):
            # Handle PDF: convert each page to an image
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                images.append(Image.open(io.BytesIO(img_data)))
            doc.close()
        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Handle standard image files
            images.append(Image.open(file_path))
        else:
            return [{"error": "Unsupported file format. Please use PDF, PNG, JPG, or JPEG."}]
            
        return images
    except Exception as e:
        return [{"error": f"Error processing file '{os.path.basename(file_path)}': {e}"}]

def analyze_test_with_gemini(question_images: list, answer_images: list) -> dict:
    """
    Uses Gemini 1.5 Pro to evaluate the student's answers against the question paper.
    """
    prompt = f"""
    You are an expert AI Teacher for competitive exams like JEE and NEET. Your task is to analyze a student's handwritten answer sheet by comparing it to the provided question paper.

    **Instructions:**
    1.  Review the images from the Question Paper and the Student's Answer Sheet.
    2.  For each question answered, compare the student's solution to the question's requirements.
    3.  Evaluate the correctness, method, and final answer.
    4.  Provide an overall score, detailed feedback on mistakes, clear explanations of the correct concepts, and actionable advice for improvement.

    **Output Format:**
    Your response MUST be a single, valid JSON object with this exact structure:
    {{
      "overall_score": "Provide a score (e.g., '75/100') and a percentage.",
      "overall_feedback": "A brief, encouraging summary of the student's performance, highlighting strengths and key areas for improvement.",
      "detailed_analysis": [
        {{
          "question_number": "The question number (e.g., 'Q1a')",
          "evaluation": "'Correct', 'Incorrect', or 'Partially Correct'.",
          "explanation": "A detailed explanation of why the answer is right or wrong. For incorrect answers, explain the correct concept and method.",
          "suggestion": "A specific tip for improvement related to this question's topic or error type."
        }}
      ]
    }}
    """
    try:
        # Construct the multi-modal prompt
        request_contents = [prompt, "\n--- QUESTION PAPER IMAGES --- \n"]
        request_contents.extend(question_images)
        request_contents.append("\n--- STUDENT'S ANSWER SHEET IMAGES --- \n")
        request_contents.extend(answer_images)

        response = model.generate_content(request_contents)
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        result = json.loads(cleaned_response)
        return result
    except Exception as e:
        return {"error": f"An error occurred during AI analysis: {e}"}

# --- 4. Main Program Execution ---
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    
    if len(sys.argv) != 3:
        print("Error: Please provide two file paths (question paper and answer sheet).")
        exit()

    question_paper_path = sys.argv[1]
    answer_sheet_path = sys.argv[2]

    # Step 1: Process both files (PDF or Image)
    question_doc_images = process_file(question_paper_path)
    if isinstance(question_doc_images[0], dict) and "error" in question_doc_images[0]:
        print(question_doc_images[0]["error"])
        exit()

    answer_doc_images = process_file(answer_sheet_path)
    if isinstance(answer_doc_images[0], dict) and "error" in answer_doc_images[0]:
        print(answer_doc_images[0]["error"])
        exit()
    
    # Step 2: Perform the AI analysis
    analysis_data = analyze_test_with_gemini(question_doc_images, answer_doc_images)
    
    # Step 3: Format and print the final output for Streamlit
    if "error" in analysis_data:
        print(f"Analysis Failed!\n{analysis_data['error']}")
    else:
        output_string = "**Test Analysis Complete!**\n\n"
        output_string += f"### Overall Score: {analysis_data.get('overall_score', 'N/A')}\n\n"
        output_string += f"**Feedback:** {analysis_data.get('overall_feedback', 'No feedback available.')}\n\n"
        output_string += "---\n"
        output_string += "### Detailed Breakdown\n\n"
        
        for item in analysis_data.get('detailed_analysis', []):
            output_string += f"**Question {item.get('question_number', 'N/A')}**\n"
            output_string += f"- **Evaluation:** {item.get('evaluation', 'N/A')}\n"
            output_string += f"- **Explanation:** {item.get('explanation', 'N/A')}\n"
            output_string += f"- **Suggestion:** {item.get('suggestion', 'N/A')}\n\n"
        
        print(output_string)
