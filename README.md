# MinutesAI  
**Meeting Summarizer & Action-Item Generator**  

A one-file Python script that turns any meeting audio (or video) into polished summaries, bullet-point key takeaways, and tagged action items—all in one go.

---

## Why MinutesAI?

- **Hybrid AI pipeline**: Combines Whisper’s state-of-the-art speech-to-text with GPT-4’s chain-of-thought summarization.  
- **Meeting overload solved**: Remote teams drowning in calls—everyone wants TL;DRs and clear next steps.  
- **Standalone CLI**: No multi-module frameworks, Jupyter mashups, or half-baked scripts. Just one polished, zero-dependency file.

---

## Core Features (in `minutesai.py`)

1. **Input handling**  
   - Accepts local audio/video: `.mp3`, `.wav`, `.mp4`, Zoom exports  
   - Auto-extracts audio via `ffmpeg-python`  
2. **Transcription**  
   - Calls OpenAI’s Whisper API (or a local Whisper model)  
   - Outputs a time-stamped transcript  
3. **Chunking**  
   - Splits transcript at speaker breaks or pauses  
   - Ensures each chunk stays under the LLM token limit  
4. **LLM Summarization**  
   - System prompt enforces JSON-only output  
   - For each chunk, generates:  
     - **Summary** (1–2 sentences)  
     - **Key points** (list)  
     - **Action items** (list of `{"assignee": "...", "task": "..."}` objects)  
5. **Aggregation & Formatting**  
   - Merges chunk summaries into a master overview  
   - Collates and de-duplicates action items  
   - Renders a Markdown (or simple HTML) report with:  
     - 🔹 **Overview**  
     - 🔹 **Key Takeaways**  
     - 🔹 **Action Items**  
     - 🔹 **Full Transcript** (optional)  
6. **CLI Flags**  
   ```bash
   python minutesai.py \
     --input meeting.mp4 \
     --model gpt-4-turbo \
     --whisper-model small \
     --max-chars 1200 \
     --output report.md \
     --include-transcript

### Dependencies
pip install openai whisper ffmpeg-python pydub
