# VoiceAgent

![VoiceAgent](assets/interface.png)

A voice-controlled system that listens, understands, and acts — with control.

---

## Overview

VoiceAgent is built around a simple idea: interaction should feel natural, but execution should remain controlled.

The system takes human speech as input, interprets intent using a language model, and performs actions safely within a restricted environment. Every step is visible, every action is deliberate, and nothing happens without user confirmation.

This is not just a voice interface — it is a structured pipeline where speech becomes intent, and intent becomes action.

---

## What It Does

* Accepts input through microphone or audio upload
* Converts speech into text using a local Whisper model
* Interprets intent using a Groq-powered language model
* Validates the request before execution
* Requires explicit user approval for file operations
* Executes actions inside a controlled `output/` directory
* Displays the full pipeline in real time

---

## System Flow

```text id="1l7w2h"
Audio Input → Transcription → Intent Detection → Validation → User Approval → Execution → Output
```

---

## Capabilities

* File creation
* Code generation
* Text summarization
* General conversational responses

---

## Setup

Clone the repository:

```bash id="0n6o6y"
git clone https://github.com/Suraj308/VoiceAgent.git
cd VoiceAgent
```

Install dependencies:

```bash id="2a9drh"
pip install -r requirements.txt
```

Create a `.env` file:

```id="0r6m8h"
GROQ_API_KEY=your_groq_api_key
```

Run the application:

```bash id="1q2m8h"
python app.py
```

---

## Example Commands

* "Create a file named test.txt with hello"
* "Create a Python file with hello world function"
* "Summarize artificial intelligence"
* "Hello"

---

## Safety Approach

The system is designed with restraint in mind.

* Filenames are sanitized
* Only specific file types are allowed
* File size is limited
* Existing files are not overwritten
* All execution is sandboxed
* User confirmation is required before any action

---

## Design Choices

* Whisper is used locally to avoid API costs and enable offline processing
* Groq provides fast and consistent intent classification
* Structured JSON prompting ensures predictable intent parsing
* Human-in-the-loop prevents unintended execution

---

## Demo



---

## Author

Suraj

---

## Closing Note

VoiceAgent is an attempt to balance intelligence with control.

It shows how voice, language models, and system design can come together — not just to respond, but to act, carefully.
