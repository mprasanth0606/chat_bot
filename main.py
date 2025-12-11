from fastapi import FastAPI, Request,Body
from fastapi.responses import HTMLResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel

from pydantic import BaseModel
import io
import pyttsx3
import wave
import speech_recognition as sr

from app import get_rag_answer, vectordb  # import your RAG function and vector store

app = FastAPI()

# Mount static and templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load Whisper model
model = WhisperModel("small", device="cpu", compute_type="int8")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/record-mic")
async def record_mic():
    r = sr.Recognizer()
    r.energy_threshold = 200  # less sensitive
    r.pause_threshold = 2.0   # wait after silence
    r.dynamic_energy_threshold = True

    try:
        with sr.Microphone(sample_rate=16000) as source:
            print(" Listening...")
            # make mic stable
            r.adjust_for_ambient_noise(source, duration=0.3)

            audio_data = r.listen(
                source,
                timeout=15,            # increased timeout
                phrase_time_limit=20
            )

    except sr.WaitTimeoutError:
        print(" No speech detected")
        return {"text": ""}

    # Convert raw → int16 → float32
    raw = audio_data.get_raw_data()
    # Convert to WAV buffer
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(raw)
    buffer.seek(0)

    # Whisper transcription
    segments, _ = model.transcribe(buffer, beam_size=5)
    text = " ".join([seg.text for seg in segments])

    print("Text:", text)
    return {"text": text}

class TTSRequest(BaseModel):
    text: str
    voice: str = "Rain"

# Map your frontend names to pyttsx3 voices
VOICE_MAP = {
    "Rain": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0",
    "Sunshine": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_DAVID_11.0",
    "Robot": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-GB_HAZEL_11.0",
    "Calm": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-AU_CATHERINE_11.0"
}

@app.post("/tts")
async def tts_api(req: TTSRequest):
    engine = pyttsx3.init()
    voice_id = VOICE_MAP.get(req.voice)
    engine.setProperty('voice', voice_id)
    
    buffer = io.BytesIO()
    engine.save_to_file(req.text, 'temp.wav')
    engine.runAndWait()
    
    with open('temp.wav', 'rb') as f:
        buffer.write(f.read())
    
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="audio/wav")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ask-rag")
async def ask_rag(request: dict = Body(...)):
    question = request.get("question")
    answer = get_rag_answer(question, vectordb)
    return {"answer": answer}

