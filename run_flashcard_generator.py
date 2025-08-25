import google.generativeai as genai
from PIL import Image
import openai
import os
import sys
import json

# --- 1. Configuration: PROVIDE BOTH API KEYS ---
# ⚠️ SECURITY WARNING: Hardcoding API keys is not secure for production.
try:
    # --- PASTE YOUR API KEYS HERE ---
    GEMINI_API_KEY = "AIzaSyAUB5leYMYn87eJalphWoaV0JujHRjmzuw"
    OPENAI_API_KEY = "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"
    
    genai.configure(api_key=GEMINI_API_KEY)
    openai.api_key = OPENAI_API_KEY
except Exception as e:
    print(f"API Key configuration error: {e}")
    exit()

# --- 2. AI Model Initialization ---
vision_model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- 3. Function Definitions ---

def transcribe_handwriting(image_path: str) -> str:
    """
    This is your OCR function. It takes an image path from the command line
    and returns the transcribed text.
    """
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
        return f"An error occurred during OCR processing: {e}"

def generate_flashcards_with_openai(ocr_text: str) -> dict:
    """
    This function now focuses solely on creating detailed flashcards.
    It takes the OCR text and returns a structured dictionary of flashcards.
    """
    prompt = f"""
    You are an expert study assistant. Your task is to create a set of detailed flashcards from the provided text.
    Identify all key concepts, terms, dates, and important facts. For each one, create a flashcard.
    
    Your response must be a single, valid JSON object with a single key "flashcards". 
    The value should be an array of objects, where each object is a flashcard.

    Example format:
    {{
      "flashcards": [
        {{"question": "What is the capital of France?", "answer": "Paris"}},
        {{"question": "Who wrote 'Hamlet'?", "answer": "William Shakespeare"}}
      ]
    }}

    Text from notes:
    ---
    {ocr_text}
    ---
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        return {"error": f"An error occurred during flashcard generation: {e}"}

# --- 4. Main Program Execution ---
if __name__ == "__main__":
    # Force the script's output to use UTF-8 to prevent encoding errors on Windows
    sys.stdout.reconfigure(encoding='utf-8')
    
    if len(sys.argv) > 1:
        image_filename = sys.argv[1]
    else:
        print("Error: No image file path was provided to the script.")
        exit()

    # Step 1: Perform OCR
    transcribed_notes = transcribe_handwriting(image_filename)
    
    if transcribed_notes.startswith("Error"):
        print(f"OCR Failed!\n{transcribed_notes}")
    else:
        # Step 2: Generate flashcards from the OCR text
        flashcard_data = generate_flashcards_with_openai(transcribed_notes)
        
        # Step 3: Format ONLY the flashcards as the final output.
        if "error" in flashcard_data:
            print(f"Flashcard Generation Failed!\n{flashcard_data['error']}")
        else:
            output_string = "🃏 **Generated Flashcards**\n\n"
            flashcards = flashcard_data.get("flashcards", [])
            
            if not flashcards:
                output_string += "No key concepts were found to create flashcards."
            else:
                for card in flashcards:
                    output_string += f"**Q:** {card.get('question', 'N/A')}\n"
                    output_string += f"**A:** {card.get('answer', 'N/A')}\n"
                    output_string += "---\n"
            
            # The final, formatted string is printed to the console for Streamlit to capture.
            print(output_string)

