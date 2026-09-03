/**
 * Civic Sense — Reports Feed & Interactive Geospatial Map Controller
 */

let map = null;
let markersLayer = null;
let allReports = [];
let currentFilter = "all";

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  loadReports();
  setupFilters();
  setupModal();
});

function initMap() {
  const mapElement = document.getElementById("map");
  if (!mapElement) return;

  // Initialize Leaflet Map
  map = L.map("map").setView([19.076, 72.877], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
    maxZoom: 19
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);

  document.getElementById("locateBtn")?.addEventListener("click", () => {
    if (!navigator.geolocation) return toast("Geolocation not supported");
    navigator.geolocation.getCurrentPosition(
      pos => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        map.setView([lat, lon], 16);
        L.marker([lat, lon])
          .addTo(map)
          .bindPopup("<b>Your Current Location</b>")
          .openPopup();
        toast("Location found.");
      },
      () => toast("Location permission was not granted.")
    );
  });

  document.getElementById("refreshMapBtn")?.addEventListener("click", () => {
    loadReports();
    toast("Refreshed reports & map.");
  });
}

async function loadReports() {
  const container = document.getElementById("reportsContainer");
  const countText = document.getElementById("reportCountText");

  try {
    const res = await fetch("/api/reports");
    const json = await res.json();

    if (!json.success || !json.reports) {
      if (container) container.innerHTML = `<p class="muted">No reports found.</p>`;
      return;
    }

    allReports = json.reports;
    if (countText) countText.textContent = `${allReports.length} total reports`;

    renderReports();
    renderMapMarkers();

  } catch (err) {
    console.error("Failed to load reports:", err);
    if (container) container.innerHTML = `<p class="muted">Error loading reports from server.</p>`;
  }
}

function renderReports() {
  const container = document.getElementById("reportsContainer");
  if (!container) return;

  const filtered = allReports.filter(r => {
    if (currentFilter === "all") return true;
    return (r.status || "").toLowerCase() === currentFilter.toLowerCase();
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="report" style="grid-column:1/-1;text-align:center;padding:30px;">
        <p class="muted">No reports matching filter "${currentFilter}".</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(r => {
    const issueType = r.issue?.type || "Civic Issue";
    const subcategory = r.issue?.ai_prediction?.subcategory || "";
    const priority = r.priority?.level || "LOW";
    const status = r.status || "Reported";
    const dept = r.assignment?.department || "Municipal Authority";
    const dateStr = r.created_at ? new Date(r.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : "Recently";
    const imgFilename = r.image?.filename;
    const imgUrl = imgFilename ? `/uploads/${imgFilename}` : "";

    let statusBadgeClass = "";
    if (status === "Resolved" || status === "Closed") statusBadgeClass = "badge";
    else if (status === "In Progress" || status === "Assigned") statusBadgeClass = "badge yellow";
    else statusBadgeClass = "badge red";

    const priorityBadgeClass = `badge ${priority.toLowerCase()}`;

    return `
      <div class="report" style="display:flex;flex-direction:column;justify-content:space-between;gap:12px;">
        <div style="display:flex;justify-content:space-between;gap:12px;">
          <div style="flex:1;">
            <div style="display:flex;gap:6px;margin-bottom:6px;align-items:center;">
              <span class="${priorityBadgeClass}">${priority}</span>
              <span class="${statusBadgeClass}">${status.toUpperCase()}</span>
            </div>
            <h3 style="font-size:16px;font-weight:700;margin-bottom:4px;">${issueType} ${subcategory ? `<span class="muted" style="font-size:13px;">(${subcategory})</span>` : ""}</h3>
            <p style="font-size:12px;color:var(--muted);">${r.description || "No specific details provided."}</p>
            <div style="font-size:11px;color:var(--muted);margin-top:8px;">
              📍 ${r.location?.latitude ? `${r.location.latitude.toFixed(4)}, ${r.location.longitude.toFixed(4)}` : "Geotag not provided"} • 🏛️ ${dept}
            </div>
            <div style="font-size:10px;color:var(--muted);margin-top:4px;">🕒 ${dateStr} • ID: ${r.id}</div>
          </div>
          ${imgUrl ? `
            <div style="width:85px;height:85px;border-radius:14px;overflow:hidden;border:1px solid var(--line);flex-shrink:0;">
              <img src="${imgUrl}" alt="Issue photo" style="width:100%;height:100%;object-fit:cover;">
            </div>
          ` : ""}
        </div>

        <div style="display:flex;gap:8px;margin-top:4px;border-top:1px dashed var(--line);padding-top:10px;">
          <button class="btn-secondary btn-sm" onclick="openVerifyModal('${r.id}')">
            📷 Verify Repair
          </button>
          ${r.location?.latitude ? `
            <button class="btn-secondary btn-sm" onclick="focusOnMap(${r.location.latitude}, ${r.location.longitude})">
              📍 View Pin
            </button>
          ` : ""}
        </div>
      </div>
    `;
  }).join("");
}

function renderMapMarkers() {
  if (!map || !markersLayer) return;
  markersLayer.clearLayers();

  const validGpsReports = allReports.filter(r => r.location?.latitude && r.location?.longitude);

  if (validGpsReports.length > 0) {
    validGpsReports.forEach(r => {
      const lat = r.location.latitude;
      const lon = r.location.longitude;
      const issue = r.issue?.type || "Issue";
      const priority = r.priority?.level || "LOW";
      const status = r.status || "Reported";
      const imgUrl = r.image?.filename ? `/uploads/${r.image.filename}` : "";

      const popupHtml = `
        <div style="min-width:180px;font-family:'DM Sans',sans-serif;">
          <b style="font-size:14px;">${issue}</b><br>
          <span style="font-size:11px;color:#666;">Status: <b>${status}</b> • Priority: <b>${priority}</b></span>
          ${imgUrl ? `<img src="${imgUrl}" style="width:100%;height:100px;object-fit:cover;border-radius:8px;margin-top:6px;display:block;">` : ""}
          <p style="font-size:11px;margin-top:6px;">${r.description || ""}</p>
        </div>
      `;

      L.marker([lat, lon]).addTo(markersLayer).bindPopup(popupHtml);
    });

    // Center map around first geotagged report
    const first = validGpsReports[0];
    map.setView([first.location.latitude, first.location.longitude], 13);
  }
}

function focusOnMap(lat, lon) {
  if (!map) return;
  map.setView([lat, lon], 16);
  document.getElementById("map")?.scrollIntoView({ behavior: "smooth" });
}

function setupFilters() {
  const buttons = document.querySelectorAll(".filter-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilter = btn.dataset.filter;
      renderReports();
    });
  });
}

function setupModal() {
  const modal = document.getElementById("verifyModal");
  const closeBtn = document.getElementById("closeModalBtn");
  const verifyForm = document.getElementById("verifyForm");

  closeBtn?.addEventListener("click", () => modal.classList.remove("show"));
  modal?.addEventListener("click", e => {
    if (e.target === modal) modal.classList.remove("show");
  });

  verifyForm?.addEventListener("submit", async e => {
    e.preventDefault();
    const reportId = document.getElementById("verifyReportId").value;
    const fileInput = document.getElementById("afterImageInput");
    const resultBox = document.getElementById("verifyResult");
    const submitBtn = document.getElementById("verifySubmitBtn");

    if (!fileInput.files || fileInput.files.length === 0) {
      return toast("Please select an after-repair image.");
    }

    const formData = new FormData();
    formData.append("after_image", fileInput.files[0]);

    submitBtn.disabled = true;
    submitBtn.innerHTML = "Analysing Visual Change...";

    try {
      const res = await fetch(`/api/reports/${reportId}/verify`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();

      submitBtn.disabled = false;
      submitBtn.innerHTML = "🤖 Run AI Verification ↗";

      if (!data.success) {
        resultBox.style.display = "block";
        resultBox.style.color = "var(--red)";
        resultBox.textContent = data.error || "Verification error.";
        return;
      }

      const v = data.verification;
      resultBox.style.display = "block";
      resultBox.innerHTML = `
        <div style="font-weight:700;color:${v.verified ? 'var(--green)' : 'var(--yellow)'};">
          ${v.verified ? '✅ Resolution Verified by AI' : '⚠️ Resolution Inconclusive'}
        </div>
        <p style="margin-top:4px;">${v.message}</p>
        <div style="font-size:11px;color:var(--muted);margin-top:4px;">
          Image Similarity: ${(v.similarity * 100).toFixed(1)}%
        </div>
      `;

      toast(v.verified ? "Resolution successfully verified!" : "Verification completed.");
      loadReports();

    } catch (err) {
      console.error("Verification failed:", err);
      submitBtn.disabled = false;
      submitBtn.innerHTML = "🤖 Run AI Verification ↗";
      toast("Error running verification.");
    }
  });
}

function openVerifyModal(reportId) {
  const modal = document.getElementById("verifyModal");
  const idInput = document.getElementById("verifyReportId");
  const resultBox = document.getElementById("verifyResult");
  const fileInput = document.getElementById("afterImageInput");

  if (idInput) idInput.value = reportId;
  if (resultBox) { resultBox.style.display = "none"; resultBox.textContent = ""; }
  if (fileInput) fileInput.value = "";
  if (modal) modal.classList.add("show");
}
