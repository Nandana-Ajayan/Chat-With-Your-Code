function continueChat() {
  const name = document.getElementById("user-input").value.trim();

  if (name === "") {
    alert("Please enter your name!");
    return;
  }

  document.getElementById("welcome-screen").classList.add("hidden");
  document.getElementById("chat-screen").classList.remove("hidden");
  document.getElementById("user-name").textContent = name;
}

function sendMessage() {
  const input = document.getElementById("chat-input");
  const chatWindow = document.getElementById("chat-window");

  if (input.value.trim() === "") return;

  const userMsg = document.createElement("div");
  userMsg.classList.add("chat-message", "user");
  userMsg.innerHTML = `<div class="chat-bubble">${input.value}</div>`;
  chatWindow.appendChild(userMsg);

  const botMsg = document.createElement("div");
  botMsg.classList.add("chat-message", "bot");
  botMsg.innerHTML = `<div class="chat-bubble">🤖 I'm just a placeholder. Real AI coming soon!</div>`;
  chatWindow.appendChild(botMsg);

  input.value = "";
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function startVoice() {
  if (!('webkitSpeechRecognition' in window)) {
    alert("Your browser doesn't support voice input.");
    return;
  }

  const recognition = new webkitSpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.start();

  recognition.onresult = function (event) {
    const transcript = event.results[0][0].transcript;
    document.getElementById("chat-input").value = transcript;
    sendMessage();
  };

  recognition.onerror = function (event) {
    if (event.error === "no-speech") {
      alert("🎤 No speech detected! Please speak clearly into the mic.");
    } else {
      alert("Voice error: " + event.error);
    }
  };
}

// Upload event
document.getElementById("file-image-upload").addEventListener("change", function () {
  const file = this.files[0];
  if (file) {
    alert(`📁 File "${file.name}" uploaded!`);
    // TODO: Add preview or backend logic
  }
});
