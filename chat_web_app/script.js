// Keep track of the uploaded file
let uploadedFile = null;

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

async function sendMessage() {
  const input = document.getElementById("chat-input");
  const chatWindow = document.getElementById("chat-window");
  const question = input.value.trim();

  if (question === "") {
    alert("Please type a question.");
    return;
  }

  if (!uploadedFile) {
    alert("Please upload a code file first.");
    return;
  }

  // Display user's message
  const userMsg = document.createElement("div");
  userMsg.classList.add("chat-message", "user");
  userMsg.innerHTML = `<div class="chat-bubble">${question}</div>`;
  chatWindow.appendChild(userMsg);

  input.value = "";
  chatWindow.scrollTop = chatWindow.scrollHeight;

  // Show thinking indicator
  const botPlaceholder = document.createElement("div");
  botPlaceholder.classList.add("chat-message", "bot");
  botPlaceholder.innerHTML = `<div class="chat-bubble">🤖 Thinking...</div>`;
  chatWindow.appendChild(botPlaceholder);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  // Prepare form data
  const formData = new FormData();
  formData.append("question", question);
  formData.append("file", uploadedFile);

  try {
    const response = await fetch("http://localhost:8000/ask", {
      method: "POST",
      body: formData, // No 'Content-Type' header needed; browser sets it for FormData
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Display bot's answer
    botPlaceholder.innerHTML = `<div class="chat-bubble">🤖 ${data.answer}</div>`;
    chatWindow.scrollTop = chatWindow.scrollHeight;

  } catch (error) {
    console.error("Error fetching answer:", error);
    botPlaceholder.innerHTML = `<div class="chat-bubble">🤖 Sorry, something went wrong. Please check the console for details.</div>`;
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }
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

// Handle file upload
document.getElementById("file-image-upload").addEventListener("change", function () {
  const file = this.files[0];
  if (file) {
    uploadedFile = file;
    document.getElementById("file-name").textContent = `Selected: ${file.name}`;
  }
});

// Allow sending messages with Enter key
document.getElementById("chat-input").addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});