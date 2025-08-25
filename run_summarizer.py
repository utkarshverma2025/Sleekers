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

def summarize_text_with_openai(ocr_text: str) -> dict:
    """
    This is your summarizer function, modified to make a single, non-streaming call.
    It takes the OCR text and returns a structured dictionary with the summary,
    key points, and flashcards.
    """
    prompt = f"""
    Summarize the following text in a single, valid JSON object format:
    {{
      "summary": "a detailed but concise summary in atleast 50% of the word count of the given text",
      "key_points": ["point 1", "point 2", "point 3","point 4","point 5","point 6","point 7","point 8","point 9","point 10"],
    }}
    Text: {ocr_text}
    """
    try:
        # Using the latest client syntax for a non-streaming call
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"} # Use JSON mode for reliable output
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        # Return an error message within a dictionary to maintain structure
        return {"error": f"An error occurred during summarization: {e}"}

# --- 4. Main Program Execution ---
if __name__ == "__main__":
    # This script is now a command-line tool. It reads the image path
    # passed to it by the Streamlit app.
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
        # Step 2: Perform Summarization on the OCR text
        summary_data = summarize_text_with_openai(transcribed_notes)
        
        # Step 3: Format the final output as a clean string to be printed.
        # This printed string is what the Streamlit app will capture and display.
        if "error" in summary_data:
            print(f"Summarization Failed!\n{summary_data['error']}")
        else:
            output_string = "**Analysis Complete!**\n\n"
            output_string += "**Summary**\n"
            output_string += summary_data.get("summary", "No summary available.") + "\n\n"
            
            output_string += "**Key Points**\n"
            key_points = summary_data.get("key_points", [])
            for point in key_points:
                output_string += f"- {point}\n"
            
            
            # The final, formatted string is printed to the console for Streamlit to capture.
            print(output_string)
