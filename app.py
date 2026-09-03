"""
CivicAI / CivicSense — Unified Web Application Server (Flask Backend)

Replaces Streamlit with a modern Flask server that:
1. Serves the Civic Sense cinematic frontend (HTML/CSS/JS).
2. Serves uploaded and annotated issue images.
3. Provides complete REST APIs for YOLO AI classification, duplicate
   detection, spam scoring, priority calculation, authority assignment,
   resolution verification, status workflow, and the civic assistant chatbot.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image

# Import existing core AI and utility modules
from ai.classifier import CivicIssueClassifier
from ai.duplicate_detector import find_duplicate_reports
from ai.priority_engine import calculate_priority
from ai.spam_detector import calculate_spam_score
from ai.resolution_verifier import verify_resolution
from utils.authority import assign_authority
from utils.report import create_report, load_reports, save_report
from utils.status import STATUSES, update_status

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("civicsense")

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOADS_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"
REPORTS_FILE = DATA_DIR / "reports.json"

UPLOADS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Initialize Flask App
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")

# Initialize AI Classifier
logger.info("Initializing Civic Issue YOLO Classifier...")
classifier = CivicIssueClassifier()
logger.info("Classifier initialized. Loaded models: %s", classifier.loaded_models)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def update_existing_report(report: dict[str, Any]) -> bool:
    """Save an updated report in reports.json."""
    reports = load_reports()
    updated = False
    for i, r in enumerate(reports):
        if r.get("id") == report.get("id"):
            reports[i] = report
            updated = True
            break
    if not updated:
        reports.append(report)

    with open(REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=4)
    return updated


# ────────────────────────────────────────────────────────────
# STATIC FRONTEND ROUTES
# ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the Civic Sense City Pulse home page."""
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/<path:path>")
def static_files(path: str):
    """Serve frontend static files (HTML, CSS, JS, etc.)."""
    file_path = FRONTEND_DIR / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(str(FRONTEND_DIR), path)
    # Check if user navigated without .html
    html_fallback = FRONTEND_DIR / f"{path}.html"
    if html_fallback.exists():
        return send_from_directory(str(FRONTEND_DIR), f"{path}.html")
    # Fallback to index.html
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    """Serve uploaded complaint or resolution images."""
    return send_from_directory(str(UPLOADS_DIR), filename)


# ────────────────────────────────────────────────────────────
# API: CITY STATS & PULSE
# ────────────────────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Return aggregated live stats for City Pulse."""
    try:
        reports = load_reports()
        total = len(reports)
        resolved = sum(1 for r in reports if r.get("status") in ["Resolved", "Closed"])
        in_progress = sum(1 for r in reports if r.get("status") in ["In Progress", "Assigned", "Under Review"])
        critical = sum(1 for r in reports if r.get("priority", {}).get("level") == "CRITICAL")
        
        # Unique zones/locations
        locations = set()
        for r in reports:
            loc = r.get("location", {})
            lat = loc.get("latitude")
            lon = loc.get("longitude")
            if lat is not None and lon is not None:
                locations.add((round(lat, 3), round(lon, 3)))
        active_zones = max(len(locations), 1 if total > 0 else 0)

        # Issue categories distribution
        category_counts = {}
        for r in reports:
            cat = r.get("issue", {}).get("type") or "Other"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0.0

        return jsonify({
            "success": True,
            "data": {
                "total": total,
                "resolved": resolved,
                "in_progress": in_progress,
                "critical": critical,
                "active_zones": active_zones,
                "resolution_rate": resolution_rate,
                "category_counts": category_counts,
                "recent_reports": sorted(
                    reports,
                    key=lambda x: x.get("created_at", ""),
                    reverse=True
                )[:5]
            }
        })
    except Exception as e:
        logger.error("Failed to calculate stats: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ────────────────────────────────────────────────────────────
# API: AI IMAGE ANALYSIS (YOLO)
# ────────────────────────────────────────────────────────────

@app.route("/api/analyze", methods=["POST"])
def analyze_image():
    """Run YOLO models on an uploaded image and return detections & predictions."""
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "File type not supported"}), 400

    try:
        # Save temporary file
        raw_name = secure_filename(file.filename) or "upload.jpg"
        unique_name = f"{uuid.uuid4().hex[:8]}_{raw_name}"
        saved_path = UPLOADS_DIR / unique_name
        file.save(str(saved_path))

        # Open image with PIL
        pil_image = Image.open(str(saved_path)).convert("RGB")

        # Run classifier
        prediction = classifier.predict(pil_image)

        # If annotated image was generated, save it
        annotated_url = None
        if prediction.get("annotated_image") is not None:
            ann_name = f"ann_{unique_name}"
            ann_path = UPLOADS_DIR / ann_name
            prediction["annotated_image"].save(str(ann_path))
            annotated_url = f"/uploads/{ann_name}"

        # Clean non-serializable fields
        cleaned_prediction = {
            "available": prediction.get("available", False),
            "category": prediction.get("category"),
            "subcategory": prediction.get("subcategory"),
            "confidence": prediction.get("confidence", 0.0),
            "probabilities": prediction.get("probabilities", {}),
            "model": prediction.get("model"),
            "message": prediction.get("message"),
            "detections": prediction.get("detections", []),
            "image_filename": unique_name,
            "image_url": f"/uploads/{unique_name}",
            "annotated_url": annotated_url,
        }

        return jsonify({"success": True, "prediction": cleaned_prediction})
    except Exception as e:
        logger.exception("Image analysis failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ────────────────────────────────────────────────────────────
# API: REPORTS MANAGEMENT
# ────────────────────────────────────────────────────────────

@app.route("/api/reports", methods=["GET"])
def list_reports():
    """Retrieve all reports with optional filtering."""
    try:
        reports = load_reports()

        # Query Filters
        status_filter = request.args.get("status")
        priority_filter = request.args.get("priority")
        dept_filter = request.args.get("department")
        category_filter = request.args.get("category")

        filtered = []
        for r in reports:
            if status_filter and r.get("status", "").lower() != status_filter.lower():
                continue
            if priority_filter and r.get("priority", {}).get("level", "").upper() != priority_filter.upper():
                continue
            if dept_filter and r.get("assignment", {}).get("department", "").lower() != dept_filter.lower():
                continue
            if category_filter and r.get("issue", {}).get("type", "").lower() != category_filter.lower():
                continue
            filtered.append(r)

        # Sort newest first
        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return jsonify({"success": True, "reports": filtered, "count": len(filtered)})
    except Exception as e:
        logger.error("Failed to list reports: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/<report_id>", methods=["GET"])
def get_report(report_id: str):
    """Retrieve a single report by ID."""
    reports = load_reports()
    for r in reports:
        if r.get("id") == report_id:
            return jsonify({"success": True, "report": r})
    return jsonify({"success": False, "error": "Report not found"}), 404


@app.route("/api/reports", methods=["POST"])
def submit_report():
    """Submit a new civic issue report with AI enrichment."""
    try:
        data = request.form.to_dict() if request.form else (request.get_json() or {})

        confirmed_category = data.get("confirmed_category") or data.get("issue_type") or "Other"
        description = data.get("description", "").strip()

        # Latitude & Longitude
        latitude = None
        longitude = None
        try:
            if data.get("latitude") is not None and str(data.get("latitude")).strip() != "":
                latitude = float(data.get("latitude"))
            if data.get("longitude") is not None and str(data.get("longitude")).strip() != "":
                longitude = float(data.get("longitude"))
        except (ValueError, TypeError):
            latitude, longitude = None, None

        # Image handling: either passed as existing filename/path or uploaded directly
        image_filename = data.get("image_filename")
        image_path = None

        if "image" in request.files and request.files["image"].filename != "":
            img_file = request.files["image"]
            raw_name = secure_filename(img_file.filename) or "issue.jpg"
            unique_name = f"{uuid.uuid4().hex[:8]}_{raw_name}"
            target_path = UPLOADS_DIR / unique_name
            img_file.save(str(target_path))
            image_filename = unique_name
            image_path = str(target_path)
        elif image_filename:
            target_path = UPLOADS_DIR / image_filename
            if target_path.exists():
                image_path = str(target_path)

        # Parse AI prediction if provided
        ai_result_raw = data.get("ai_result")
        ai_result = {}
        if isinstance(ai_result_raw, str):
            try:
                ai_result = json.loads(ai_result_raw)
            except Exception:
                ai_result = {}
        elif isinstance(ai_result_raw, dict):
            ai_result = ai_result_raw

        # 1. Base Report Creation
        report = create_report(
            issue_type=confirmed_category,
            ai_result=ai_result,
            confirmed_category=confirmed_category,
            description=description,
            image_filename=image_filename,
            image_path=image_path,
            latitude=latitude,
            longitude=longitude
        )

        # 2. Existing Reports for Duplicate & Spam checks
        existing_reports = load_reports()

        # 3. Duplicate Detection
        duplicate_matches = find_duplicate_reports(report, existing_reports)
        report["duplicates"] = {
            "is_duplicate": len(duplicate_matches) > 0,
            "matches": duplicate_matches
        }

        # 4. Spam Detection
        spam_result = calculate_spam_score(report, existing_reports)
        report["spam"] = spam_result

        # 5. Priority Scoring
        priority = calculate_priority(report, duplicate_count=len(duplicate_matches))
        report["priority"] = priority

        # 6. Authority Assignment
        authority = assign_authority(report)
        report["assignment"] = authority

        # 7. Persistence
        save_report(report)

        logger.info("Report %s submitted successfully for category '%s'", report["id"], confirmed_category)

        return jsonify({
            "success": True,
            "message": "Civic report registered successfully",
            "report": report
        }), 201

    except Exception as e:
        logger.exception("Error submitting report: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/<report_id>/status", methods=["POST"])
def change_report_status(report_id: str):
    """Update status of an existing report (Authority / Admin)."""
    try:
        data = request.get_json() or {}
        new_status = data.get("status")

        if not new_status or new_status not in STATUSES:
            return jsonify({
                "success": False,
                "error": f"Invalid status. Allowed statuses: {', '.join(STATUSES)}"
            }), 400

        reports = load_reports()
        target_report = None
        for r in reports:
            if r.get("id") == report_id:
                target_report = r
                break

        if not target_report:
            return jsonify({"success": False, "error": "Report not found"}), 404

        target_report = update_status(target_report, new_status)
        update_existing_report(target_report)

        return jsonify({
            "success": True,
            "message": f"Status updated to '{new_status}'",
            "report": target_report
        })
    except Exception as e:
        logger.error("Failed to update status for %s: %s", report_id, e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/<report_id>/verify", methods=["POST"])
def verify_report_resolution(report_id: str):
    """Verify repair completion by comparing before and after images."""
    if "after_image" not in request.files:
        return jsonify({"success": False, "error": "No after-repair image provided"}), 400

    file = request.files["after_image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename"}), 400

    reports = load_reports()
    target_report = None
    for r in reports:
        if r.get("id") == report_id:
            target_report = r
            break

    if not target_report:
        return jsonify({"success": False, "error": "Report not found"}), 404

    before_path = target_report.get("image", {}).get("path")
    if not before_path or not Path(before_path).exists():
        return jsonify({"success": False, "error": "Original before-image not found on server"}), 400

    try:
        raw_name = secure_filename(file.filename) or "after.jpg"
        after_name = f"after_{report_id}_{uuid.uuid4().hex[:6]}_{raw_name}"
        after_path = UPLOADS_DIR / after_name
        file.save(str(after_path))

        verification = verify_resolution(before_path, str(after_path))

        target_report["resolution"] = {
            "after_image": str(after_path),
            "after_image_url": f"/uploads/{after_name}",
            "image_similarity": verification.get("similarity"),
            "ai_verified": verification.get("verified"),
            "citizen_confirmed": None,
            "message": verification.get("message")
        }

        # If verified, progress status
        if verification.get("verified"):
            target_report["status"] = "Resolved"
            if "status_history" not in target_report:
                target_report["status_history"] = []
            target_report["status_history"].append({
                "status": "Resolved",
                "timestamp": datetime.now().isoformat()
            })

        update_existing_report(target_report)

        return jsonify({
            "success": True,
            "verification": verification,
            "report": target_report
        })
    except Exception as e:
        logger.exception("Resolution verification error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/<report_id>/confirm", methods=["POST"])
def citizen_confirm_resolution(report_id: str):
    """Citizen confirms or rejects repair resolution."""
    data = request.get_json() or {}
    confirmed = data.get("confirmed")

    if confirmed is None:
        return jsonify({"success": False, "error": "'confirmed' boolean required"}), 400

    reports = load_reports()
    target_report = None
    for r in reports:
        if r.get("id") == report_id:
            target_report = r
            break

    if not target_report:
        return jsonify({"success": False, "error": "Report not found"}), 404

    if "resolution" not in target_report or target_report["resolution"] is None:
        target_report["resolution"] = {}

    target_report["resolution"]["citizen_confirmed"] = bool(confirmed)

    new_status = "Closed" if confirmed else "In Progress"
    target_report["status"] = new_status
    if "status_history" not in target_report:
        target_report["status_history"] = []
    target_report["status_history"].append({
        "status": new_status,
        "timestamp": datetime.now().isoformat()
    })

    update_existing_report(target_report)

    return jsonify({
        "success": True,
        "message": f"Issue updated to '{new_status}' based on citizen confirmation",
        "report": target_report
    })


# ────────────────────────────────────────────────────────────
# API: CIVIC ASSISTANT CHATBOT (Ollama / Fallback)
# ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are CivicSense AI, an intelligent civic assistant inside the CivicSense application.
You can answer general questions and civic-related questions.

IMPORTANT RULES:
- Answer the user's CURRENT question directly, warmly and professionally.
- Do not assume they are reporting a pothole unless they mention it.
- If the user says hello, simply greet them warmly.
- If the user asks about civic problems (potholes, garbage, streetlights, waterlogging, road damage),
  guide them on how CivicSense automatically detects and routes them to the right municipal authority.
- Keep answers concise, clear and formatted nicely with bullet points where helpful.
"""

@app.route("/api/chat", methods=["POST"])
def civic_chat():
    """Civic Assistant conversational endpoint."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"success": False, "error": "Message cannot be empty"}), 400

    # Build messages list
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-8:]:  # keep recent conversation window
        if "role" in h and "content" in h:
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    # Attempt Ollama chat
    try:
        import ollama
        response = ollama.chat(
            model="llama3.2:3b",
            messages=messages
        )
        reply = response["message"]["content"]
        return jsonify({"success": True, "reply": reply})
    except Exception as e:
        logger.warning("Ollama chat unavailable: %s. Using intelligent fallback.", e)
        # Civic Fallback response logic
        lower = message.lower()
        if any(w in lower for w in ["hi", "hello", "hey", "greetings"]):
            reply = (
                "Hello! I am **CivicSense AI**, your smart civic assistant. "
                "You can ask me how to report civic issues, track current repairs, "
                "or learn about our municipal departments and AI detection capabilities."
            )
        elif "pothole" in lower or "road" in lower:
            reply = (
                "To report a pothole or road damage:\n"
                "1. Go to the **Detect** page.\n"
                "2. Upload or snap a photo of the road surface.\n"
                "3. Our AI vision model will automatically identify the pothole/crack with confidence scoring.\n"
                "4. Confirm your GPS location and hit Submit. It will be routed directly to the **Municipal Roads Authority**."
            )
        elif "garbage" in lower or "waste" in lower or "trash" in lower:
            reply = (
                "For overflowing waste or litter:\n"
                "Upload an image on the **Detect** page. Our AI classifier categorizes the waste "
                "and routes the ticket to the **Municipal Sanitation Authority** with calculated priority."
            )
        elif "light" in lower or "streetlight" in lower:
            reply = (
                "Streetlight outages can cause safety hazards at night. "
                "Submit a report under **Damaged Streetlight**; it will be assigned with HIGH priority "
                "to the **Municipal Electrical Authority**."
            )
        elif "status" in lower or "track" in lower or "report" in lower:
            reply = (
                "You can track all community reports in real-time on our **Reports** page, "
                "complete with interactive map pins, priority indicators, and verification statuses."
            )
        elif "authority" in lower or "admin" in lower:
            reply = (
                "Municipal officers can use the **Authority Panel** to filter issues by department, "
                "prioritize critical complaints, assign work orders, and verify repairs."
            )
        else:
            reply = (
                f"I received your question: \"{message}\". "
                "CivicSense connects citizens directly with city authorities through automated "
                "AI vision detection, duplicate clustering, and priority scoring. "
                "Feel free to ask about reporting potholes, garbage, streetlights, or checking issue status!"
            )

        return jsonify({"success": True, "reply": reply, "is_fallback": True})


# ────────────────────────────────────────────────────────────
# SERVER ENTRY POINT
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=======================================================")
    print(f"🏙️  CIVIC SENSE WEB APPLICATION IS RUNNING")
    print(f"👉  Local URL: http://localhost:{port}")
    print(f"👉  Frontend:  {FRONTEND_DIR}")
    print(f"👉  Loaded AI Models: {classifier.loaded_models}")
    print(f"=======================================================\n")
    app.run(host=host, port=port, debug=False)