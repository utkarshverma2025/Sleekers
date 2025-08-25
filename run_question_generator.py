import google.generativeai as genai
from PIL import Image
from openai import OpenAI
import os
import sys # <-- ADDED LINE: Import the sys module to read command-line arguments

# --- 1. Configuration: PROVIDE BOTH API KEYS ---
# ⚠️ SECURITY WARNING: Hardcoding API keys is okay for a short-term hackathon but is not secure.
# For a real project, use environment variables to keep your keys safe.

# Paste your Google Gemini API Key for the Handwriting OCR
try:
    # This key is an example and will not work. Replace it with your own.
    GEMINI_API_KEY = "AIzaSyAUB5leYMYn87eJalphWoaV0JujHRjmzuw" 
    if GEMINI_API_KEY == "PASTE_YOUR_GEMINI_API_KEY_HERE":
        print("ERROR: Please provide your Google Gemini API Key.")
        exit()
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    exit()

# Paste your OpenAI API Key for the Question Generator
try:
    # This key is an example and will not work. Replace it with your own.
    OPENAI_API_KEY = "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" # 🔑 Replace with your actual key
    if OPENAI_API_KEY == "hb":
         print("ERROR: Please provide your actual OpenAI API Key.")
         exit()
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    print(f"Error configuring OpenAI API: {e}")
    exit()


# --- 2. AI Model Setup ---
vision_model = genai.GenerativeModel('gemini-1.5-flash-latest')


# --- 3. Function Definitions ---

def transcribe_handwriting(image_path: str) -> str:
    """
    Takes an image file path and uses Gemini Vision to transcribe the handwriting.
    """
    # This function remains unchanged.
    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        return f"Error: The file '{image_path}' was not found."
    except Exception as e:
        return f"Error opening image: {e}"

    prompt = "Transcribe the handwritten text from this image accurately. Provide only the text content."
    
    try:
        response = vision_model.generate_content([prompt, img])
        return response.text.strip()
    except Exception as e:
        return f"An error occurred during Gemini processing: {e}"

def generate_questions_with_openai(ocr_text: str) -> str:
    """
    Takes transcribed text and uses OpenAI GPT-4o mini to generate questions.
    """
    # This function remains unchanged.
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": rf"""Here are my notes:

        {ocr_text}

        Please generate 10 good, human-readable questions based on these notes.  
        ⚠️ Important: Use **normal human math notation** like √, π, ∫, fractions, exponents (a², x³), etc.  
        Do NOT use LaTeX (e.g., \int, ^{{2}}), programming-style (** or //), or MathML.  
        Only output plain text that looks like how math appears in a textbook."""
                }
            ]
        )
        output = response.choices[0].message.content.strip()
        cleaned_output = "\n".join(line.strip() for line in output.splitlines() if line.strip())
        return cleaned_output
        
    except Exception as e:
        return f"An error occurred during OpenAI processing: {e}"


# --- 4. Main Program Execution ---
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    # --- MODIFIED SECTION START ---
    # Instead of asking for input, we now read the image path
    # that the Streamlit app passes to this script.
    if len(sys.argv) > 1:
        image_filename = sys.argv[1] # The first argument is the image path
    else:
        # This error message will show up in Streamlit if something goes wrong.
        print("Error: No image file path was provided to the script.")
        exit()
    # --- MODIFIED SECTION END ---


    # Call the OCR function to get the transcribed text.
    transcribed_notes = transcribe_handwriting(image_filename)

    # Check if OCR was successful before proceeding.
    if transcribed_notes.startswith("Error"):
        # The Streamlit app will display this error message.
        print(f"OCR Failed!\n{transcribed_notes}")
    else:
        # Now, use the transcribed text to generate questions with OpenAI.
        generated_questions = generate_questions_with_openai(transcribed_notes)

        # The final output that Streamlit will capture and display.
        print(generated_questions)
