from flask import Flask
from flask_socketio import SocketIO, emit
import ollama
import whisper
import sounddevice as sd
import numpy as np
import wave
import tempfile
import os
import asyncio
from edge_tts import Communicate
import threading
import re
import pandas as pd


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load Whisper model
stt_model = whisper.load_model("turbo")

# Globals
recording_buffer = []
session_id = 1
is_recording = False
session_histories = {}  # Temporary memory per client session
main_info = "NO"

def extract_and_search_order(query, file_path):
    
    match = re.search(r'\b(\d{5})\b', query)
    if match:
        order_id = match.group(1)
        
        
        df = pd.read_csv(file_path)
        
        
        result = df[df['Order_ID'] == int(order_id)]
        
        if not result.empty:
            order_details = result.to_dict(orient='records')[0]
            order_details_str = f"Details of Order ID  {order_id} are "
            order_details_str +=  ' '.join(f"{key}: {value} ," for key, value in order_details.items())
            return order_details_str
        else:
            return "NO"
    else:
        return "NO"

# def get_contextualized_query(prompt):
#         # order_id = self.get_order_id_from_user()
#         semantic_search = SemanticSearch('Orders.csv')
#         context_data = semantic_search.run_search(prompt)
#         # contextualized_query = f"You are customer care agent,and give the answer to '{prompt}' only using {', '.join(map(str, context_data.values()))}, such that there can be an answer within these sentences? Find the related data and provide the answer. Additionally, if the answer contains digits, please convert them to single digit words.(e.g., 1 to One, 2 to Two,0 to zero and ignore +,- etc.),Do not give more extra information more than user asked ."
        
#         return context_data
#         # else : return {', '.join(map(str, context_data.values()))}

# Background recording function
def background_recording():
    global is_recording, recording_buffer
    print("🎙️ Recording started (float32)...")

    samplerate = 16000
    recording_buffer = []

    while is_recording:
        frame = sd.rec(int(samplerate * 0.5), samplerate=samplerate, channels=1, dtype="float32")
        sd.wait()
        recording_buffer.extend(frame)

    print("🛑 Recording stopped.")

# def is_silent(audio_chunk, threshold=0.01):
#     return np.max(np.abs(audio_chunk)) < threshold

# def background_recording():
#     global is_recording, recording_buffer
#     print("🎙️ Recording started with silence detection...")

#     samplerate = 16000
#     recording_buffer = []
#     silence_duration = 0
#     silence_threshold = 1  # seconds
#     chunk_duration = 0.5  # seconds

#     while is_recording:
#         frame = sd.rec(int(samplerate * chunk_duration), samplerate=samplerate, channels=1, dtype="float32")
#         sd.wait()
#         frame_flat = frame.flatten()
#         recording_buffer.extend(frame_flat)

#         if is_silent(frame_flat):
#             silence_duration += chunk_duration
#         else:
#             silence_duration = 0  # voice detected

#         if silence_duration >= silence_threshold:
#             print("🛑 Silence detected. Triggering transcription...")
#             is_recording = False
#             socketio.emit("silence_triggered")  # frontend will call stop_recording
#             break

#     print("🛑 Recording thread exited.")


# Normalize and convert to float32
def normalize_and_convert(audio):
    audio_np = np.array(audio, dtype=np.float32)
    max_val = np.max(np.abs(audio_np), initial=1)
    if max_val > 0:
        audio_np /= max_val
    return audio_np

# Save WAV
def save_wav(filename, audio_data, samplerate=16000):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(audio_data.tobytes())

# SocketIO: Start Recording
@socketio.on("start_recording")
def handle_start_recording():
    global is_recording, recording_buffer
    if is_recording:
        return emit("status", {"message": "Already recording!"})
    
    is_recording = True
    recording_buffer = []
    threading.Thread(target=background_recording, daemon=True).start()
    emit("status", {"message": "Recording started."})

# SocketIO: Stop Recording
@socketio.on("stop_recording")
def handle_stop_recording():
    global is_recording, recording_buffer, main_info, session_histories, session_id

    if session_id not in session_histories:
        session_histories[session_id] = []

    if not is_recording:
        return emit("status", {"message": "Recording was not started."})

    is_recording = False
    emit("status", {"message": "Recording stopped. Processing..."})

    # Convert buffer to numpy array
    audio_np = np.array(recording_buffer, dtype=np.float32).flatten()

    # Directly pass to Whisper
    try:
        result = stt_model.transcribe(audio_np, language='en', fp16=False)  # Use fp16=False for better CPU support
        transcription = result["text"].strip()
        emit("transcription", {"text": transcription})
    except Exception as e:
        emit("error", {"message": f"Transcription failed: {e}"})
        return


    
    # Query LLM if transcription exists
    if transcription:
        new_prompt = extract_and_search_order(transcription,'Orders.csv')
        if(new_prompt != "NO") : 
            main_info = new_prompt

        if(main_info == "NO") : 
            query = f"You are customer care agent named Lina,and give the answer to '{transcription}'  and ask user to provide order id as he has not provided, so that you can help with their query. remove special symbols in answer like *,#,(,),etc in answer"
            session_histories[session_id].append({"role": "user", "content": query})
            # llm_response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": query}])
            llm_response = ollama.chat(model="llama3.2", messages=session_histories[session_id])
            response_text = llm_response["message"]["content"]
            session_histories[session_id].append({"role": "assistant", "content": response_text})
            emit("llm_response", {"response": response_text})
            asyncio.run(text_to_speech(response_text))
        else:
            contextualized_query = f"You are customer care agent named Lina,and give the answer to '{transcription}' only using {main_info}, such that there can be an answer within these sentences? Find the related data and provide the answer with empathy.Do not give more extra information more than user asked .remove special symbols in answer like *,#,(,),etc in answer. Respond to the user by calling their name from the data but not repeatedly."
            session_histories[session_id].append({"role": "user", "content": contextualized_query})
            # llm_response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": contextualized_query}])
            llm_response = ollama.chat(model="llama3.2", messages=session_histories[session_id])
            response_text = llm_response["message"]["content"]
            session_histories[session_id].append({"role": "assistant", "content": response_text})
            # response = ollama.chat(model=self.llm_model, messages=[{"role": "user", "content": prompt}])
            # response_text = response["message"]["content"]
            emit("llm_response", {"response": response_text})
            asyncio.run(text_to_speech(response_text))

        
    

          
            
            
# TTS with edge-tts
async def text_to_speech(text):
    audio_output = "output.mp3"
    communicate = Communicate(text, "en-US-JennyNeural")
    await communicate.save(audio_output)

    # Send audio to client
    socketio.emit("audio", {"audio_file": audio_output})

# Start server
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)



