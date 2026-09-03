/**
 * Civic Sense — Detection & Report Submission Controller
 * Connects directly to the Flask Backend YOLO AI APIs (/api/analyze, /api/reports)
 */

let currentAnalysisResult = null;
let currentImageFile = null;
let uploadedImageFilename = null;

const input = document.getElementById("imageInput");
const box = document.getElementById("upload");
const preview = document.getElementById("preview");
const resultCard = document.getElementById("resultCard");
const resultTitle = document.getElementById("resultTitle");
const resultText = document.getElementById("resultText");
const loader = document.getElementById("loader");
const annotatedContainer = document.getElementById("annotatedContainer");
const annotatedImage = document.getElementById("annotatedImage");
const detectionTags = document.getElementById("detectionTags");
const reportFormSection = document.getElementById("reportFormSection");
const reportForm = document.getElementById("reportForm");
const confirmedCategorySelect = document.getElementById("confirmedCategory");
const getGpsBtn = document.getElementById("getGpsBtn");
const gpsStatus = document.getElementById("gpsStatus");
const latitudeInput = document.getElementById("latitude");
const longitudeInput = document.getElementById("longitude");
const submissionSuccess = document.getElementById("submissionSuccess");
const reportAnotherBtn = document.getElementById("reportAnotherBtn");

// Drag & Drop Events
input?.addEventListener("change", () => handleImage(input.files[0]));
box?.addEventListener("dragover", e => { e.preventDefault(); box.classList.add("drag"); });
box?.addEventListener("dragleave", () => box.classList.remove("drag"));
box?.addEventListener("drop", e => {
  e.preventDefault();
  box.classList.remove("drag");
  if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    handleImage(e.dataTransfer.files[0]);
  }
});

function handleImage(file) {
  if (!file || !file.type.startsWith("image/")) {
    return toast("Please select a valid image file (JPG, PNG, WEBP).");
  }

  currentImageFile = file;
  preview.src = URL.createObjectURL(file);
  preview.style.display = "block";
  
  // Reset previous views
  annotatedContainer.style.display = "none";
  detectionTags.style.display = "none";
  reportFormSection.style.display = "none";
  submissionSuccess.style.display = "none";

  loader.classList.add("show");
  resultTitle.textContent = tr("analysing");
  resultText.textContent = "Processing with YOLO AI vision models...";

  // Run backend YOLO analysis
  analyseWithBackend(file);
}

async function analyseWithBackend(file) {
  const formData = new FormData();
  formData.append("image", file);

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    loader.classList.remove("show");

    if (!data.success) {
      resultTitle.textContent = "Analysis Note";
      resultText.textContent = data.error || "Could not analyze image. Please select category manually.";
      showReportForm("Other");
      return;
    }

    const p = data.prediction;
    currentAnalysisResult = p;
    uploadedImageFilename = p.image_filename;

    const category = p.category || "Other";
    const subcategory = p.subcategory || "";
    const confidencePct = Math.round(p.confidence * 100);

    resultTitle.textContent = tr("result");
    
    // Render result HTML
    resultText.innerHTML = `
      <div style="margin-bottom:8px;">
        <span style="font-size:22px;font-weight:700;">${category}</span>
        ${subcategory ? `<span class="muted" style="margin-left:6px;font-size:14px;">(${subcategory})</span>` : ""}
      </div>
      <div class="muted" style="font-size:13px;line-height:1.5;">${p.message || "Detection complete."}</div>
      <div class="confidence" style="margin:14px 0 6px 0;"><div id="confBar" style="width:0%;"></div></div>
      <div style="display:flex;justify-content:space-between;font-size:12px;" class="muted">
        <span>Confidence</span>
        <strong style="color:var(--text);">${confidencePct}%</strong>
      </div>
    `;

    setTimeout(() => {
      const bar = document.getElementById("confBar");
      if (bar) bar.style.width = `${confidencePct}%`;
    }, 60);

    // Show annotated image if YOLO found detections
    if (p.annotated_url) {
      annotatedImage.src = p.annotated_url;
      annotatedContainer.style.display = "block";
    }

    // Show detection tags
    if (p.detections && p.detections.length > 0) {
      detectionTags.innerHTML = p.detections.map(d => 
        `<span class="tag"><b>${d.issue_type}</b> ${d.class_name ? `• ${d.class_name}` : ""} (${Math.round(d.confidence * 100)}%)</span>`
      ).join("");
      detectionTags.style.display = "flex";
    }

    toast(`${category} detected (${confidencePct}%)`);
    showReportForm(category);

  } catch (err) {
    console.error("Analysis request error:", err);
    loader.classList.remove("show");
    resultTitle.textContent = "AI Vision Note";
    resultText.textContent = "AI model returned a fallback response. You can proceed with manual category selection.";
    showReportForm("Other");
  }
}

function showReportForm(suggestedCategory) {
  // Pre-select category in dropdown
  if (confirmedCategorySelect) {
    const options = Array.from(confirmedCategorySelect.options).map(o => o.value);
    if (options.includes(suggestedCategory)) {
      confirmedCategorySelect.value = suggestedCategory;
    } else {
      confirmedCategorySelect.value = "Other";
    }
  }
  reportFormSection.style.display = "block";
}

// Geolocation Handling
getGpsBtn?.addEventListener("click", () => {
  if (!navigator.geolocation) {
    gpsStatus.textContent = "Geolocation is not supported by your browser.";
    return toast("Geolocation not supported");
  }

  gpsStatus.textContent = "Acquiring coordinates...";
  navigator.geolocation.getCurrentPosition(
    pos => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      latitudeInput.value = lat.toFixed(6);
      longitudeInput.value = lon.toFixed(6);
      gpsStatus.textContent = `Captured: ${lat.toFixed(4)}, ${lon.toFixed(4)}`;
      toast("Location captured successfully.");
    },
    err => {
      gpsStatus.textContent = "Location permission denied or unavailable.";
      toast("Could not acquire location.");
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
});

// Report Submission
reportForm?.addEventListener("submit", async e => {
  e.preventDefault();

  const submitBtn = document.getElementById("submitReportBtn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = "Submitting Report...";

  const confirmedCategory = confirmedCategorySelect.value;
  const description = document.getElementById("description").value;
  const latitude = latitudeInput.value ? parseFloat(latitudeInput.value) : null;
  const longitude = longitudeInput.value ? parseFloat(longitudeInput.value) : null;

  const payload = new FormData();
  payload.append("confirmed_category", confirmedCategory);
  payload.append("description", description);
  if (latitude !== null) payload.append("latitude", latitude);
  if (longitude !== null) payload.append("longitude", longitude);
  if (uploadedImageFilename) payload.append("image_filename", uploadedImageFilename);
  if (currentAnalysisResult) payload.append("ai_result", JSON.stringify(currentAnalysisResult));

  // If image was not uploaded via /api/analyze, append raw file
  if (!uploadedImageFilename && currentImageFile) {
    payload.append("image", currentImageFile);
  }

  try {
    const res = await fetch("/api/reports", {
      method: "POST",
      body: payload
    });

    const data = await res.json();
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<span>${tr("submitReport")}</span> ↗`;

    if (!data.success) {
      return toast("Submission failed: " + (data.error || "Unknown error"));
    }

    const report = data.report;
    toast("Civic report submitted successfully!");

    // Hide form & show summary
    reportFormSection.style.display = "none";
    submissionSuccess.style.display = "block";

    document.getElementById("sumId").textContent = report.id;
    const pLevel = (report.priority && report.priority.level) || "MEDIUM";
    const pBadge = document.getElementById("sumPriority");
    pBadge.textContent = `${pLevel} (Score: ${report.priority?.score ?? '--'})`;
    pBadge.className = `badge ${pLevel.toLowerCase()}`;

    document.getElementById("sumDept").textContent = report.assignment?.department || "General Civic";
    document.getElementById("sumAuthority").textContent = report.assignment?.authority_name || "Municipal Authority";

    if (report.duplicates && report.duplicates.is_duplicate) {
      document.getElementById("sumDuplicateRow").style.display = "flex";
    } else {
      document.getElementById("sumDuplicateRow").style.display = "none";
    }

  } catch (err) {
    console.error("Submission error:", err);
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<span>${tr("submitReport")}</span> ↗`;
    toast("Error submitting report. Please try again.");
  }
});

// Report Another Button
reportAnotherBtn?.addEventListener("click", () => {
  currentAnalysisResult = null;
  currentImageFile = null;
  uploadedImageFilename = null;
  preview.src = "";
  preview.style.display = "none";
  annotatedContainer.style.display = "none";
  detectionTags.style.display = "none";
  reportFormSection.style.display = "none";
  submissionSuccess.style.display = "none";
  document.getElementById("description").value = "";
  resultTitle.textContent = tr("result");
  resultText.textContent = tr("noResult");
  input.value = "";
});
