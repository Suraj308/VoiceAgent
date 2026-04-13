import gradio as gr
from groq import Groq
import os
import json
import re
import time
from pathlib import Path
import whisper
from dotenv import load_dotenv
import numpy as np

# LOAD ENV 
load_dotenv()

# CONFIG
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = [".txt", ".py", ".md", ".json"]
MAX_FILE_SIZE = 5000

last_request_time = 0

# MODELS 
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
whisper_model = whisper.load_model("base")

# HELPERS 
def is_safe_filename(filename):
    return re.match(r'^[a-zA-Z0-9_\-\.]+$', filename)

# TRANSCRIBE (FINAL STABLE) 
def transcribe_audio(audio):
    if audio is None:
        return "No audio received"

    try:
        sr, data = audio

        # Convert to float32
        data = data.astype(np.float32)

        # Normalize audio
        if np.max(np.abs(data)) > 0:
            data = data / np.max(np.abs(data))

        # Resample if needed
        if sr != 16000:
            import librosa
            data = librosa.resample(data, orig_sr=sr, target_sr=16000)

        # Transcribe with controlled randomness
        result = whisper_model.transcribe(
            data,
            language="en",
            temperature=0.0
        )

        text = result["text"].strip()

        if len(text) < 2:
            return "Could not understand audio"

        return text

    except Exception as e:
        return f"Transcription error: {str(e)}"

# INTENT 
def parse_intent(text: str) -> dict:
    prompt = """Classify user intent into JSON:

Intents:
- create_file
- write_code
- summarize_text
- general_chat

Return format:
{
 "intent": "...",
 "params": {...},
 "reasoning": "..."
}
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.1
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(content)

        if not isinstance(parsed, dict) or "intent" not in parsed:
            raise ValueError("Invalid JSON")

        return parsed

    except Exception:
        return {
            "intent": "general_chat",
            "params": {"response": "System fallback triggered."},
            "reasoning": "Fallback"
        }

# SAFE EXECUTION 
def execute_action(intent_data, transcribed):
    intent = intent_data.get("intent", "")
    params = intent_data.get("params", {})
    reasoning = intent_data.get("reasoning", "")

    if intent in ["create_file", "write_code"]:
        filename = os.path.basename(params.get("filename", "untitled.txt"))

        if not is_safe_filename(filename):
            return transcribed, intent, "Unsafe filename", "Blocked"

        if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            return transcribed, intent, "Invalid file type", str(ALLOWED_EXTENSIONS)

        content = params.get("code") or params.get("content", "")

        if not isinstance(content, str) or len(content.strip()) == 0:
            return transcribed, intent, "Invalid content", "Empty"

        if len(content) > MAX_FILE_SIZE:
            return transcribed, intent, "File too large", "Limit 5000 chars"

        file_path = OUTPUT_DIR / filename

        if file_path.exists():
            return transcribed, intent, "File exists", "Rename file"

        try:
            file_path.write_text(content, encoding="utf-8")
            return (
                transcribed,
                f"{intent.upper()} — {reasoning}",
                f"File created: {filename}",
                f"Saved at {file_path}"
            )
        except Exception as e:
            return transcribed, intent, "Error", str(e)

    elif intent == "summarize_text":
        return transcribed, intent, "Summary", params.get("summary", "")

    else:
        return transcribed, intent, "Response", params.get("response", "")

# PIPELINE 
def analyze_voice(audio, history):
    global last_request_time

    if time.time() - last_request_time < 1:
        return "Slow down...", "", "", "", history, None

    last_request_time = time.time()

    text = transcribe_audio(audio)
    intent_data = parse_intent(text)

    intent_str = f"{intent_data.get('intent')} — {intent_data.get('reasoning')}"

    if intent_data["intent"] in ["create_file", "write_code"]:
        filename = os.path.basename(intent_data["params"].get("filename", "untitled.txt"))

        return (
            text,
            intent_str,
            f"Awaiting approval for {filename}",
            "Click AUTHORIZE",
            history,
            {"intent_data": intent_data, "transcribed": text}
        )

    else:
        _, intent_str, action, result = execute_action(intent_data, text)
        history.append([text, result])
        return text, intent_str, action, result, history, None


def confirm_and_execute(pending, history):
    if not pending:
        return "No pending action", "", history, None

    _, intent_str, action, result = execute_action(
        pending["intent_data"], pending["transcribed"]
    )

    history.append(["Executed", result])
    return action, result, history, None

# UI 
with gr.Blocks() as demo:

    gr.Markdown("# Voice Agent")

    audio = gr.Audio(sources=["microphone", "upload"], type="numpy")

    analyze = gr.Button("Analyze")
    confirm = gr.Button("Authorize")

    t = gr.Textbox(label="Transcribed")
    i = gr.Textbox(label="Intent")
    a = gr.Textbox(label="Action")
    r = gr.Textbox(label="Result")

    chat = gr.Chatbot(label="Mission Log")

    history = gr.State([])
    pending = gr.State(None)

    analyze.click(analyze_voice, [audio, history],
                  [t, i, a, r, history, pending])

    confirm.click(confirm_and_execute, [pending, history],
                  [a, r, history, pending])

# RUN
if __name__ == "__main__":
    demo.launch()