let recordedChunks = [];
let mediaRecorder = null;
let recordedBlob = null;

// 🎙️ Start microphone recording
function startMicRecording() {
  navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    recordedChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = e => {
      if (e.data.size > 0) recordedChunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
      recordedBlob = new Blob(recordedChunks, { type: 'audio/webm' }); // Correct MIME type
      const preview = document.getElementById("preview");
      preview.src = URL.createObjectURL(recordedBlob);
      preview.classList.remove("hidden");
    };

    mediaRecorder.start();
    console.log("🎙️ Recording Started...");

    // Change button text and color to indicate recording
    const recordButton = document.querySelector("button[onclick='startMicRecording()']");
    recordButton.innerHTML = "🎙️ Recording...";
    recordButton.classList.remove("bg-blue-600", "hover:bg-blue-700");
    recordButton.classList.add("bg-red-600", "hover:bg-red-700");
  });
}

// 🛑 Stop microphone recording
function stopMicRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    console.log("🛑 Recording Completed.");

    // Reset the button back to its original state
    const recordButton = document.querySelector("button[onclick='startMicRecording()']");
    recordButton.innerHTML = "🎙️️ Recording Started...";
    recordButton.classList.remove("bg-red-600", "hover:bg-red-700");
    recordButton.classList.add("bg-blue-600", "hover:bg-blue-700");
  }
}


// 📤 Upload both files and get comparison result
async function uploadAndCompare() {
  const referenceFile = document.getElementById("referenceInput").files[0];
  const uploadedUserFile = document.getElementById("userInput").files[0];

  if (!referenceFile) {
    alert("Upload Reference Song");
    return;
  }

  const userFile = uploadedUserFile || recordedBlob;
  if (!userFile) {
    alert("Please Record your voice or upload an audio file");
    return;
  }

  const formData = new FormData();
  formData.append("original", referenceFile, "reference.wav");
  formData.append("recorded", userFile, "recorded.webm");  // ✅ use webm for correct format

  const response = await fetch("/compare_audio", {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    alert("Error Matching Pitches");
    return;
  }

  const data = await response.json();

  if (data.image) {
    const imageUrl = 'data:image/png;base64,' + data.image;
    const img = document.getElementById("comparisonImage");
    img.src = imageUrl;
    img.classList.remove("hidden");
  }

  if (data.swara_similarity !== undefined) {
    const scoreDiv = document.getElementById("swaraScore");
    scoreDiv.innerText = `🎼 Pitch Matching Accuracy: ${(data.swara_similarity * 100).toFixed(2)}%`;
    scoreDiv.classList.remove("hidden");
  }
}
