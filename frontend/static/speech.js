(function () {
  const questionInput = document.getElementById("question");
  const speakButton = document.getElementById("speak-button");
  const speechStatus = document.getElementById("speech-status");

  if (!questionInput || !speakButton || !speechStatus) {
    return;
  }

  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!Recognition) {
    speakButton.disabled = true;
    speechStatus.textContent = "Voice input is not supported in this browser.";
    return;
  }

  const recognition = new Recognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.addEventListener("start", () => {
    speakButton.disabled = true;
    speechStatus.textContent = "Listening...";
  });

  recognition.addEventListener("result", (event) => {
    const transcript = event.results[0][0].transcript;
    questionInput.value = transcript;
    speechStatus.textContent = "Voice captured. Review the question, then click Send.";
    questionInput.focus();
  });

  recognition.addEventListener("error", (event) => {
    speechStatus.textContent = `Voice input error: ${event.error}.`;
  });

  recognition.addEventListener("end", () => {
    speakButton.disabled = false;
    if (speechStatus.textContent === "Listening...") {
      speechStatus.textContent = "No speech was captured. Try again.";
    }
  });

  speakButton.addEventListener("click", () => {
    speechStatus.textContent = "";
    recognition.start();
  });
})();
