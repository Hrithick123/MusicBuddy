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
      recordedBlob = new Blob(recordedChunks, { type: 'audio/webm' });
      const preview = document.getElementById("preview");
      preview.src = URL.createObjectURL(recordedBlob);
      preview.classList.remove("hidden");
    };

    mediaRecorder.start();
    console.log("🎙️ Recording Started...");

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

    const recordButton = document.querySelector("button[onclick='startMicRecording()']");
    recordButton.innerHTML = "🎙️ Start Recording";
    recordButton.classList.remove("bg-red-600", "hover:bg-red-700");
    recordButton.classList.add("bg-blue-600", "hover:bg-blue-700");
  }
}

// 📤 Upload both files and get comparison result
async function uploadAndCompare() {
  const uploadedReference = document.getElementById("referenceInput").files[0];
  const selectedSample = document.getElementById("sampleSelect").value;
  const uploadedUserFile = document.getElementById("userInput").files[0];

  let referenceFile;

  if (uploadedReference) {
    referenceFile = uploadedReference;
  } else if (selectedSample) {
    const response = await fetch(selectedSample);
    const blob = await response.blob();
    referenceFile = new File([blob], "sample_reference.mp3", { type: blob.type });
  } else {
    alert("Please upload or select a reference song.");
    return;
  }

  const userFile = uploadedUserFile || recordedBlob;
  if (!userFile) {
    alert("Please record your voice or upload an audio file.");
    return;
  }

  const formData = new FormData();
  formData.append("original", referenceFile, "reference.wav");
  formData.append("recorded", userFile, "recorded.webm");

  const res = await fetch("/compare_audio", {
    method: "POST",
    body: formData
  });

  if (!res.ok) {
    alert("Error Matching Pitches");
    return;
  }

  const data = await res.json();

  if (data.image) {
    const img = document.getElementById("comparisonImage");
    img.src = 'data:image/png;base64,' + data.image;
    img.classList.remove("hidden");
  }

  if (data.swara_similarity !== undefined) {
    const scoreDiv = document.getElementById("swaraScore");
    scoreDiv.innerText = `🎼 Pitch Matching Accuracy: ${(data.swara_similarity * 100).toFixed(2)}%`;
    scoreDiv.classList.remove("hidden");
  }
}

// 🎧 Show uploaded reference preview
document.getElementById("referenceInput").addEventListener("change", function () {
  const file = this.files[0];
  const audio = document.getElementById("referencePreview");
  if (file) {
    audio.src = URL.createObjectURL(file);
    audio.classList.remove("hidden");

    // Reset sample select if uploading custom file
    document.getElementById("sampleSelect").value = "";
    document.getElementById("samplePreview").classList.add("hidden");
  }
});

// 🎧 Play sample from dropdown
function playSampleReference() {
  const selected = document.getElementById("sampleSelect").value;
  const preview = document.getElementById("samplePreview");

  if (selected) {
    preview.src = selected;
    preview.classList.remove("hidden");

    // Clear uploaded input
    document.getElementById("referenceInput").value = "";
    document.getElementById("referencePreview").classList.add("hidden");
  } else {
    preview.classList.add("hidden");
  }
}
