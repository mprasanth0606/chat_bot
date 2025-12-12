
/* --- Your existing JS unchanged except bubble UI updated --- */

function appendChat(sender, text) {
    const container = document.getElementById("chatContainer");
    const div = document.createElement("div");

    if (sender === "user") {
        div.className = "user-msg";
        div.textContent = text;
    } else {
        div.className = "bot-msg";
        div.innerHTML = text;
    }

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}
let isRecording = false;
async function recordAudio() {
    const mic = document.getElementById("micWrapper");

    if (!isRecording) {

        // 🔥 Remove old chat text immediately
        document.getElementById("chatInput").value = "";

        isRecording = true;
        mic.classList.add("recording");

        const res = await fetch("/record-mic", { method:"POST" });
        const data = await res.json();

        // 🔥 Insert new speech-to-text
        document.getElementById("chatInput").value = data.text;

        isRecording = false;
        mic.classList.remove("recording");
    }
}

let selectedVoice = "Rain";

function toggleVoiceMenu() {
    const menu = document.getElementById("voiceMenu");
    menu.style.display = menu.style.display === "none" ? "block" : "none";
}

function setVoice(voice) {
    selectedVoice = voice;
    document.getElementById("voiceMenu").style.display = "none";
}

async function playOutput() {
    const text = document.getElementById("chatInput").value;
    if (!text.trim()) return;

    const res = await fetch("/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text, voice: selectedVoice })
    });

    const audioBlob = await res.blob();
    const url = URL.createObjectURL(audioBlob);
    const audio = new Audio(url);
    audio.play();
}

async function sendQuestion() {
    const input = document.getElementById("chatInput");
    const text = input.value.trim();
    if (!text) return;

    // Append question to chat container
    appendChat("user", text);

    // Send text to RAG API
    const res = await fetch("/ask-rag", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text })
    });
    const data = await res.json();

    // Append answer to chat container
    appendChat("bot", data.answer);

    // Play TTS audio
    const ttsRes = await fetch("/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: data.answer, voice: selectedVoice })
    });
    const audioBlob = await ttsRes.blob();
    const url = URL.createObjectURL(audioBlob);
    const audio = new Audio(url);
    audio.play();

    // Clear input
    input.value = "";
}

function appendChat(sender, text) {
    const container = document.getElementById("chatContainer");
    const div = document.createElement("div");
    div.className = sender;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight; // auto-scroll
}
 isRecording = false;
let mediaRecorder;
let audioChunks = [];
let recordTimerInterval;
let seconds = 0;
let recordedAudioBlob = null;

async function recordAudio() {
    recordControls.querySelector("button[onclick*='true']").style.display = "block";
    recordControls.querySelector("button[onclick*='false']").style.display = "block";
    if (isRecording) return;

    isRecording = true;
    audioChunks = [];
    seconds = 0;
    document.getElementById("recordControls").style.display = "flex";
    document.getElementById("micWrapper").classList.add("recording");

    recordTimerInterval = setInterval(() => {
        seconds++;
        const min = String(Math.floor(seconds/60)).padStart(2,'0');
        const sec = String(seconds%60).padStart(2,'0');
        document.getElementById("recordTimer").textContent = `${min}:${sec}`;
    }, 1000);

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
}

async function finishRecording(save) {
    clearInterval(recordTimerInterval);
    isRecording = false;

    // Hide ✔ and ✖ during conversion
    recordControls.querySelector("button[onclick*='true']").style.display = "none";
    recordControls.querySelector("button[onclick*='false']").style.display = "none";

    mediaRecorder.stop();
    mediaRecorder.onstop = async () => {
        if (!save) {
            audioChunks = [];
            recordedAudioBlob = null;
            document.getElementById("recordControls").style.display = "none";
            document.getElementById("micWrapper").classList.remove("recording");
            return;
        }

        recordedAudioBlob = new Blob(audioChunks, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("file", recordedAudioBlob, "recorded.webm");

        const res = await fetch("/convert", { method: "POST", body: formData });
        const data = await res.json();
        document.getElementById("chatInput").value = data.text;
        document.getElementById("micWrapper").classList.remove("recording");

        recordedAudioBlob = null;
        audioChunks = [];
        document.getElementById("recordControls").style.display = "none";
    };
}
