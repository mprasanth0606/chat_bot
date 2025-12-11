
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
