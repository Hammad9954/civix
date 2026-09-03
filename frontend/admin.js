/**
 * Civic Sense — Authority Control Panel Controller
 */

let reportsData = [];

document.addEventListener("DOMContentLoaded", () => {
  loadAdminReports();

  document.getElementById("filterDept")?.addEventListener("change", applyFilters);
  document.getElementById("filterPriority")?.addEventListener("change", applyFilters);
  document.getElementById("filterStatus")?.addEventListener("change", applyFilters);
  document.getElementById("reloadAdminBtn")?.addEventListener("click", () => {
    loadAdminReports();
    toast("Reloaded tickets.");
  });
});

async function loadAdminReports() {
  const tbody = document.getElementById("adminTableBody");
  try {
    const res = await fetch("/api/reports");
    const json = await res.json();
    if (!json.success || !json.reports) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;">No reports loaded.</td></tr>`;
      return;
    }

    reportsData = json.reports;
    applyFilters();
  } catch (err) {
    console.error("Failed to load admin reports:", err);
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--red);">Error connecting to backend API.</td></tr>`;
  }
}

function applyFilters() {
  const deptFilter = document.getElementById("filterDept").value;
  const priorityFilter = document.getElementById("filterPriority").value;
  const statusFilter = document.getElementById("filterStatus").value;

  const filtered = reportsData.filter(r => {
    const dept = (r.assignment?.department || "General Civic Department").trim();
    const priority = (r.priority?.level || "LOW").toUpperCase();
    const status = (r.status || "Reported").trim();

    if (deptFilter !== "all" && dept.toLowerCase() !== deptFilter.toLowerCase()) return false;
    if (priorityFilter !== "all" && priority !== priorityFilter) return false;
    if (statusFilter !== "all" && status.toLowerCase() !== statusFilter.toLowerCase()) return false;

    return true;
  });

  renderAdminTable(filtered);
}

function renderAdminTable(reports) {
  const tbody = document.getElementById("adminTableBody");
  if (!tbody) return;

  if (reports.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:30px;" class="muted">No complaints match the current filter selection.</td></tr>`;
    return;
  }

  tbody.innerHTML = reports.map(r => {
    const priority = (r.priority?.level || "LOW").toUpperCase();
    const status = r.status || "Reported";
    const dept = r.assignment?.department || "Unassigned";
    const authority = r.assignment?.authority_name || "Municipal Authority";
    const imgUrl = r.image?.filename ? `/uploads/${r.image.filename}` : "";
    const isDup = r.duplicates?.is_duplicate;
    const spamScore = r.spam?.score ?? "--";
    const priorityScore = r.priority?.score ?? "--";

    const pBadgeClass = `badge ${priority.toLowerCase()}`;

    return `
      <tr>
        <td>
          <b style="font-family:'Space Grotesk';font-size:13px;">${r.id}</b>
          <div style="font-size:10px;color:var(--muted);">${new Date(r.created_at).toLocaleDateString()}</div>
          ${r.reporter_id ? `<div style="font-size:10px;color:var(--text);font-family:'Space Grotesk';font-weight:600;margin-top:2px;">👤 ${r.reporter_id}</div>` : ""}
        </td>
        <td>
          ${imgUrl ? `
            <div style="width:55px;height:55px;border-radius:10px;overflow:hidden;border:1px solid var(--line);">
              <a href="${imgUrl}" target="_blank">
                <img src="${imgUrl}" alt="Thumbnail" style="width:100%;height:100%;object-fit:cover;">
              </a>
            </div>
          ` : `<span class="muted" style="font-size:11px;">No photo</span>`}
        </td>
        <td>
          <div style="font-weight:700;">${r.issue?.type || "Issue"}</div>
          <div style="font-size:11px;color:var(--muted);max-width:250px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
            ${r.description || "No description"}
          </div>
          <div style="font-size:10px;color:var(--muted);margin-top:2px;">
            ${r.location?.latitude ? `📍 ${r.location.latitude.toFixed(4)}, ${r.location.longitude.toFixed(4)}` : "No GPS"}
          </div>
        </td>
        <td>
          <span class="${pBadgeClass}">${priority}</span>
          <div style="font-size:10px;color:var(--muted);margin-top:4px;">Score: ${priorityScore}</div>
        </td>
        <td>
          <div style="font-weight:600;font-size:12px;">${dept}</div>
          <div style="font-size:10px;color:var(--muted);">${authority}</div>
        </td>
        <td>
          <div style="font-size:11px;">
            ${isDup ? `<span style="color:var(--yellow);font-weight:700;">⚠️ Duplicate</span>` : `<span style="color:var(--green);">✓ Unique</span>`}
          </div>
          <div style="font-size:10px;color:var(--muted);margin-top:2px;">Spam: ${spamScore}</div>
        </td>
        <td>
          <select class="form-select btn-sm" onchange="updateTicketStatus('${r.id}', this.value)" style="min-width:130px;padding:6px 10px;">
            <option value="Reported" ${status === "Reported" ? "selected" : ""}>Reported</option>
            <option value="Under Review" ${status === "Under Review" ? "selected" : ""}>Under Review</option>
            <option value="Assigned" ${status === "Assigned" ? "selected" : ""}>Assigned</option>
            <option value="In Progress" ${status === "In Progress" ? "selected" : ""}>In Progress</option>
            <option value="Resolved" ${status === "Resolved" ? "selected" : ""}>Resolved</option>
            <option value="Closed" ${status === "Closed" ? "selected" : ""}>Closed</option>
          </select>
        </td>
      </tr>
    `;
  }).join("");
}

async function updateTicketStatus(reportId, newStatus) {
  try {
    const res = await fetch(`/api/reports/${reportId}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    if (data.success) {
      toast(`Status updated to "${newStatus}"`);
      // Update local array
      const item = reportsData.find(r => r.id === reportId);
      if (item) item.status = newStatus;
    } else {
      toast("Failed to update status: " + (data.error || "Unknown error"));
    }
  } catch (err) {
    console.error("Status update error:", err);
    toast("Network error updating status.");
  }
}
