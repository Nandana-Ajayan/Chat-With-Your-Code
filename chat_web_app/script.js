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

  if (question === "") return;

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

  try {
    let response;
    // If a file is uploaded, use the FormData endpoint
    if (uploadedFile) {
      const formData = new FormData();
      formData.append("question", question);
      formData.append("file", uploadedFile);
      
      response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        body: formData,
      });

    } else {
      // If no file is uploaded, use the new text-only endpoint
      response = await fetch("http://localhost:8000/ask_text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: question }),
      });
    }

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Display bot's answer
    botPlaceholder.innerHTML = `<div class="chat-bubble">🤖 ${data.answer}</div>`;
    chatWindow.scrollTop = chatWindow.scrollHeight;

  } catch (error) {
    console.error("Error fetching answer:", error);
    botPlaceholder.innerHTML = `<div class="chat-bubble">🤖 Sorry, something went wrong. Please check the console.</div>`;
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


// --- NEW AND IMPROVED EVENT HANDLING ---

// Wait for the entire webpage to be loaded before running any script
document.addEventListener('DOMContentLoaded', (event) => {
  
  // Attach functions to buttons
  document.getElementById('continue-btn').addEventListener('click', continueChat);
  document.getElementById('send-btn').addEventListener('click', sendMessage);
  document.getElementById('speak-btn').addEventListener('click', startVoice);

  // Handle file upload
  document.getElementById('file-image-upload').addEventListener('change', function () {
    const file = this.files[0];
    if (file) {
      uploadedFile = file;
      document.getElementById('file-name').textContent = `Selected: ${file.name}`;
      // Give a visual cue to the user
      alert(`📁 File "${file.name}" is ready to be used with your next question.`);
    }
  });

  // Allow sending messages with the Enter key in the chat input
  document.getElementById('chat-input').addEventListener('keypress', function (e) {
      if (e.key === 'Enter') {
          e.preventDefault(); // Stop the default Enter key action
          sendMessage();
      }
  });

});