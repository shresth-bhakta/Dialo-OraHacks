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

def get_customer_credit_details(customer_no):
    customer_data = pd.read_csv('customerdetails.csv')
    credit_card_data = pd.read_csv('creditcard.csv')
    
    customer = customer_data[customer_data['Customer No.'] == customer_no]
    if customer.empty:
        return "Customer not found!"
    
    customer_name = customer.iloc[0]['Name']
    eligible_credit_cards = customer.iloc[0]['Eligible Credit Cards'].split('; ')
    credit_card_details = credit_card_data[credit_card_data['Card Name'].isin(eligible_credit_cards)]
    
    result = f"Customer: {customer_name}\n\nEligible Credit Cards:\n"
    result += "".join(
        f"- {row['Card Name']} (Annual Fee: {row['Annual Fee']}, APR: {row['Interest Rate (APR)']}, Rewards: {row['Rewards']}, Credit Limit: {row['Credit Limit']})\n"
        for _, row in credit_card_details.iterrows()
    )
    
    return result

def get_customer_loan_details(customer_no):
    customer_data = pd.read_csv('customerdetails.csv')
    loan_data = pd.read_csv('loandetails.csv')
    
    customer = customer_data[customer_data['Customer No.'] == customer_no]
    if customer.empty:
        return "Customer not found!"
    
    customer_name = customer.iloc[0]['Name']
    eligible_loans = customer.iloc[0]['Eligible Loans'].split('; ')
    loan_details = loan_data[loan_data['Loan Type'].isin(eligible_loans)]
    
    result = f"Customer: {customer_name}\n\nEligible Loans:\n"
    result += "".join(
        f"- {row['Loan Type']} (Interest Rate: {row['Interest Rate']}, Loan Amount Range: {row['Loan Amount Range']}, Tenure: {row['Tenure']}, Processing Fee: {row['Processing Fee']}, Special Features: {row['Special Features']})\n"
        for _, row in loan_details.iterrows()
    )
    
    return result


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
    global is_recording, recording_buffer,  session_histories, session_id

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


    userdetails = get_customer_credit_details(103)
    # file_path = 'credit_prompt.txt'
    # with open(file_path, 'r') as file:
    #     loan_prompt = file.read()
    credit_prompt = "You are lina a credit card marketing agent convince the user to take one of the available credit credit"
    # Query LLM if transcription exists
    if transcription: 
        query = f"Use this prompt for how to give answer: {credit_prompt}, for giving the answer to {transcription} using the credit card availability details {userdetails}. Give answer in less sentences and do not use names again and again"
        session_histories[session_id].append({"role": "user", "content": query})
        # llm_response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": query}])
        llm_response = ollama.chat(model="llama3.2", messages=session_histories[session_id])
        response_text = llm_response["message"]["content"]
        session_histories[session_id].append({"role": "assistant", "content": response_text})
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
    socketio.run(app, host="0.0.0.0", port=5002, debug=True)



