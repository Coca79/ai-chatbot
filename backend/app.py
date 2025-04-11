import os
import torch
from fastapi import FastAPI, WebSocket
from TTS.api import TTS
import whisper
import logging
import openai
from deepseek_ai import DeepSeek

app = FastAPI()

# Konfiguracja modeli
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
stt_model = whisper.load_model("medium", device=device)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Odbieranie audio w formacie wav
            audio_data = await websocket.receive_bytes()
            
            # STT - Whisper
            result = stt_model.transcribe(audio_data, fp16=torch.cuda.is_available())
            text_input = result["text"]
            
            # Przetwarzanie zapytania
            response = await process_query(text_input)
            
            # TTS - Coqui XTTS
            tts.tts_to_file(
                text=response,
                file_path="output.wav",
                speaker_wav="reference_speaker.wav",
                language="en"
            )
            
            # Wysyłanie odpowiedzi audio
            with open("output.wav", "rb") as f:
                await websocket.send_bytes(f.read())
            
    except Exception as e:
        logging.error(f"Error: {e}")

async def process_query(text: str) -> str:
    # Integracja z OpenAI i DeepSeek
    openai.api_key = os.getenv("OPENAI_KEY")
    deepseek = DeepSeek(api_key=os.getenv("DEEPSEEK_KEY"))
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": text}]
    )
    
    # Weryfikacja przez DeepSeek
    verified = deepseek.verify(response.choices[0].message.content)
    
    return verified.content if verified.valid else "Nie mogę odpowiedzieć na to pytanie"
