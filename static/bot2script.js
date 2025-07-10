const socket = io("http://localhost:5002");
let isRecording = false;
let currentAudio = null;


const micBtn = document.getElementById("micBtn");
const chatBox = document.getElementById("chat");

// micBtn.addEventListener("click", () => {
//   if (!isRecording) {
//     socket.emit("start_recording");
//     micBtn.textContent = "🛑 Stop Recording";
//     micBtn.classList.remove("btn-danger");
//     micBtn.classList.add("btn-secondary");
//   } else {
//     socket.emit("stop_recording");
//     micBtn.textContent = "🎙️ Start Recording";
//     micBtn.classList.remove("btn-secondary");
//     micBtn.classList.add("btn-danger");
//   }
//   isRecording = !isRecording;
// });

micBtn.addEventListener("click", () => {
  if (!isRecording) {
      // 🛑 Stop playing current audio before recording
      if (currentAudio) {
          currentAudio.pause();
          currentAudio.currentTime = 0;
      }

      socket.emit("start_recording");
      micBtn.textContent = "🛑 Stop Recording";
      micBtn.classList.remove("btn-danger");
      micBtn.classList.add("btn-secondary");
  } else {
      socket.emit("stop_recording");
      micBtn.textContent = "🎙️ Start Recording";
      micBtn.classList.remove("btn-secondary");
      micBtn.classList.add("btn-danger");
  }
  isRecording = !isRecording;
});


// socket.on("audio", (data) => {
//   // Add timestamp to bypass browser cache
//   const audioUrl = `${data.audio_file}?t=${Date.now()}`;
//   const audio = new Audio(audioUrl);
//   audio.play().catch(error => {
//       console.error("Audio playback failed:", error);
//   });
// });

socket.on("audio", (data) => {
  const audioUrl = `${data.audio_file}?t=${Date.now()}`;
  currentAudio = new Audio(audioUrl);
  currentAudio.play().catch(error => {
      console.error("Audio playback failed:", error);
  });
});


socket.on("status", (data) => {
  console.log("Status:", data.message);
});

socket.on("transcription", (data) => {
  const msgWrapper = document.createElement("div");
  msgWrapper.style.display = "flex";
  msgWrapper.style.flexDirection = "column";
  msgWrapper.style.alignItems = "flex-start";
  msgWrapper.style.marginBottom = "20px";

  const label = document.createElement("div");
  label.textContent = "🗣️ You";
  label.style.fontSize = "0.85rem";
  label.style.color = "#999";
  label.style.marginBottom = "4px";
  label.style.marginLeft = "5px";

  const msg = document.createElement("div");
  msg.className = "user-msg";
  msg.textContent = data.text;
  msg.style.padding = "12px 16px";
  msg.style.borderRadius = "15px";
  msg.style.backgroundColor = "#e6f0ff";
  msg.style.maxWidth = "75%";
  msg.style.border = "1px solid #ccc";
  msg.style.alignSelf = "flex-start";

  msgWrapper.appendChild(label);
  msgWrapper.appendChild(msg);
  chatBox.appendChild(msgWrapper);
  chatBox.scrollTop = chatBox.scrollHeight;
});


socket.on("llm_response", (data) => {
  const msgWrapper = document.createElement("div");
  msgWrapper.style.display = "flex";
  msgWrapper.style.flexDirection = "column";
  msgWrapper.style.alignItems = "flex-end";
  msgWrapper.style.marginBottom = "30px";
  msgWrapper.style.position = "relative";

  const msg = document.createElement("div");
  msg.className = "llm-msg";
  msg.textContent = data.response;
  msg.style.padding = "12px 16px";
  msg.style.borderRadius = "15px";
  msg.style.backgroundColor = "#e8f5e9";
  msg.style.maxWidth = "75%";
  msg.style.border = "1px solid #ccc";
  msg.style.alignSelf = "flex-end";
  msg.style.position = "relative"; // Required for inner absolute positioning

  // Label wrapper inside the message bubble (bottom-right)
  const labelWrapper = document.createElement("div");
  labelWrapper.style.display = "flex";
  labelWrapper.style.alignItems = "center";
  labelWrapper.style.position = "absolute";
  labelWrapper.style.bottom = "-22px";
  labelWrapper.style.right = "5px";

  const labelText = document.createElement("span");
  labelText.textContent = "Dialo";
  labelText.style.fontSize = "0.85rem";
  labelText.style.color = "#999";
  labelText.style.marginRight = "6px";

  const logo = document.createElement("img");
  logo.src = "/static/newdialo.png";
  logo.alt = "Dialo Logo";
  logo.style.height = "18px";

  labelWrapper.appendChild(labelText);
  labelWrapper.appendChild(logo);

  msg.appendChild(labelWrapper);
  msgWrapper.appendChild(msg);
  chatBox.appendChild(msgWrapper);
  chatBox.scrollTop = chatBox.scrollHeight;
});


// Dark mode toggle
const toggleBtn = document.getElementById('toggle-dark');
toggleBtn.addEventListener('click', () => {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  toggleBtn.textContent = newTheme === 'dark' ? '☀️' : '🌙';
});

// Load preferred theme on page load
document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
    toggleBtn.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
  }
});
