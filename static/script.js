// const socket = io("http://localhost:5001");
// let isRecording = false;

// const micBtn = document.getElementById("micBtn");
// const chatBox = document.getElementById("chat");

// micBtn.addEventListener("click", () => {
//     if (!isRecording) {
//         socket.emit("start_recording");
//         micBtn.textContent = "🛑 Stop Recording";
//         micBtn.classList.remove("btn-danger");
//         micBtn.classList.add("btn-secondary");
//     } else {
//         socket.emit("stop_recording");
//         micBtn.textContent = "🎙️ Start Recording";
//         micBtn.classList.remove("btn-secondary");
//         micBtn.classList.add("btn-danger");
//     }
//     isRecording = !isRecording;
// });

// socket.on("status", (data) => {
//     console.log("Status:", data.message);
// });

// // socket.on("audio", (data) => {
// //     const audio = new Audio(data.audio_file);
// //     audio.play().catch(error => {
// //         console.error("Audio playback failed:", error);
// //     });
// // });

// socket.on("audio", (data) => {
//     // Add timestamp to bypass browser cache
//     const audioUrl = `${data.audio_file}?t=${Date.now()}`;
//     const audio = new Audio(audioUrl);
//     audio.play().catch(error => {
//         console.error("Audio playback failed:", error);
//     });
// });


// socket.on("transcription", (data) => {
//     const msg = document.createElement("div");
//     msg.className = "user-msg";
//     msg.textContent = `🗣️ You: ${data.text}`;
//     chatBox.appendChild(msg);
//     chatBox.scrollTop = chatBox.scrollHeight;
// });

// socket.on("llm_response", (data) => {
//     const msg = document.createElement("div");
//     msg.className = "llm-msg";
//     msg.textContent = `🤖 LLM: ${data.response}`;
//     chatBox.appendChild(msg);
//     chatBox.scrollTop = chatBox.scrollHeight;
// });

// socket.on("error", (data) => {
//     alert("Error: " + data.message);
// });

const socket = io("http://localhost:5001");
let isCalling = false;
let currentAudio = null;
let mediaStream = null;
let audioContext, micAnalyzer, sourceNode;

const micBtn = document.getElementById("micBtn");
const chatBox = document.getElementById("chat");

micBtn.addEventListener("click", async () => {
    if (!isCalling) {
        await startCall();
    } else {
        endCall();
    }
});

async function startCall() {
    micBtn.textContent = "❌ End Call";
    micBtn.classList.remove("btn-danger");
    micBtn.classList.add("btn-secondary");
    isCalling = true;

    // Stop audio playback if user speaks
    monitorMicForInterrupt();

    socket.emit("start_recording");
}

function endCall() {
    micBtn.textContent = "📞 Call";
    micBtn.classList.remove("btn-secondary");
    micBtn.classList.add("btn-danger");
    isCalling = false;
    socket.emit("stop_recording");

    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
    }
    if (audioContext) {
        audioContext.close();
    }
}

socket.on("status", (data) => {
    console.log("Status:", data.message);
});

socket.on("transcription", (data) => {
    const msg = document.createElement("div");
    msg.className = "user-msg";
    msg.textContent = `🗣️ You: ${data.text}`;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
});

socket.on("llm_response", (data) => {
    const msg = document.createElement("div");
    msg.className = "llm-msg";
    msg.textContent = `🤖 LLM: ${data.response}`;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
});

// socket.on("audio", (data) => {
//     const audioUrl = `${data.audio_file}?t=${Date.now()}`;
//     currentAudio = new Audio(audioUrl);
//     currentAudio.play().catch(error => {
//         console.error("Audio playback failed:", error);
//     });
// });

socket.on("audio", (data) => {
    const audioUrl = `${data.audio_file}?t=${Date.now()}`;
    currentAudio = new Audio(audioUrl);

    currentAudio.play().catch(error => {
        console.error("Audio playback failed:", error);
    });

    currentAudio.onended = () => {
        console.log("🔁 Audio finished. Starting recording again...");
        if (isCalling) {
            socket.emit("start_recording");
        }
    };
});


socket.on("silence_triggered", () => {
    console.log("🔇 Silence detected, stopping recording...");
    socket.emit("stop_recording");
});

function monitorMicForInterrupt() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaStream = stream;
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            micAnalyzer = audioContext.createAnalyser();
            sourceNode = audioContext.createMediaStreamSource(stream);
            sourceNode.connect(micAnalyzer);

            const buffer = new Uint8Array(micAnalyzer.frequencyBinCount);

            function detectSpeaking() {
                micAnalyzer.getByteFrequencyData(buffer);
                const volume = buffer.reduce((a, b) => a + b, 0) / buffer.length;
                if (volume > 20 && currentAudio && !currentAudio.paused) {
                    console.log("🎤 User interrupted. Stopping audio.");
                    currentAudio.pause();
                    currentAudio.currentTime = 0;
                    socket.emit("start_recording");
                }
                if (isCalling) requestAnimationFrame(detectSpeaking);
            }
            detectSpeaking();
        });
}