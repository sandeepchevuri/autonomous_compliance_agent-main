from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
import asyncio
from pathlib import Path

from core.cleaner import delete_old_audit_logs
from core.config import AUDIT_DIR, RETENTION_DAYS, CLEANUP_INTERVAL_SECONDS
from core.file_utils import save_json_audit
from agents.extraction_agent import ExtractionAgent
from agents.monitoring_agent import monitor_and_download_top_pdf
from agents.analyzing_agent import AnalyzingAgent
from agents.reporting_agent import ReportingAgent
from agents.company_policy_agent import CompanyPolicyAgent


from fastapi import Form
from agents.risk_flagger_agent import RiskFlaggerAgent

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[Startup] RETENTION_DAYS set to {RETENTION_DAYS}")
    async def cleanup_loop():
        while True:
            delete_old_audit_logs()
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)

    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()

app = FastAPI(
    title="Autonomous Compliance Agent API",
    description="APIs for regulatory monitoring, compliance document analysis, and reporting automation.",
    version="1.0.0",
    lifespan=lifespan
)

# ────────────────────────────────────────────────
# 📡 Regulatory Monitoring Endpoint
# ────────────────────────────────────────────────
@app.get("/regulations/monitor", tags=["Regulatory Monitoring"], summary="Monitor & Fetch Regulation PDFs")
async def monitor_regulations():
    """
    Scrapes known regulatory websites (MNRE, SECI, CERC), finds policy update PDFs, and downloads the most recent one.
    """
    return monitor_and_download_top_pdf([
        "https://mnre.gov.in/en/monthly-updates/?utm_source"
        # "https://seci.co.in/category/monthly-reports",
        # "https://cercind.gov.in/whatsnew.html"
    ])

# ────────────────────────────────────────────────


# 🧠 Analyze Downloaded PDF Endpoint
# ────────────────────────────────────────────────
@app.get("/documents/analyze-latest", tags=["Compliance Analysis"], summary="Analyze Latest Downloaded Regulation PDF")
async def analyze_latest_pdf():
    """
    Analyzes the most recently downloaded PDF from monitored regulatory sources and saves extracted data.
    """
    agent = AnalyzingAgent()
    result = agent.analyze_latest()

    if "error" not in result:
        audit_path = save_json_audit(result, result["filename"])
        result["audit_saved_to"] = audit_path
        result["download_url"] = f"/documents/audit/{os.path.basename(audit_path)}"

    return result

# 📄 PDF Upload Endpoint
# ────────────────────────────────────────────────
# @app.post("/documents/upload", tags=["Compliance Analysis"], summary="Upload & Analyze a PDF")
# async def upload_pdf(file: UploadFile = File(...)):
#     """
#     Uploads a regulatory document (PDF) and extracts obligations, penalties, dates, and entities.
#     """
#     if file.content_type != "application/pdf":
#         raise HTTPException(status_code=400, detail="Only PDF files are supported.")

#     agent = ExtractionAgent(file)
#     result = agent.run()
#     audit_path = save_json_audit(result, file.filename)
#     result["audit_saved_to"] = audit_path
#     result["download_url"] = f"/documents/audit/{os.path.basename(audit_path)}"
#     return result

# 

@app.post("/upload-company-policy/")
async def upload_internal_policy(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    agent = CompanyPolicyAgent(file)
    result = agent.extract_and_save()
    return result


from agents.risk_flagger_agent import RiskFlaggerAgent

@app.get("/flag-compliance-risk/latest", tags=["Risk Analysis"], summary="Compare Latest MNRE & Internal Policy JSONs")
async def flag_latest_compliance_risks():
    """
    Automatically compares the latest extracted MNRE regulation file
    with the latest internal policy file and flags compliance risks.
    """
    from pathlib import Path

    internal_dir = Path("audit_logs/internal")
    external_dir = Path("audit_logs")

    # Get latest internal file
    internal_files = list(internal_dir.glob("*.json"))
    if not internal_files:
        raise HTTPException(status_code=404, detail="No internal policy files found.")
    latest_internal = max(internal_files, key=lambda f: f.stat().st_mtime)

    # Get latest external file (excluding the internal folder)
    external_files = [f for f in external_dir.glob("*.json") if "internal" not in str(f)]
    if not external_files:
        raise HTTPException(status_code=404, detail="No external regulation files found.")
    latest_external = max(external_files, key=lambda f: f.stat().st_mtime)

    # Run risk comparison
    agent = RiskFlaggerAgent(str(latest_external), str(latest_internal))
    result = agent.compare()

    # Include which files were compared
    result["compared_files"] = {
        "external": latest_external.name,
        "internal": latest_internal.name
    }
    return result


from agents.risk_flagger_agent import RiskFlaggerAgent
from agents.reporting_agent import ReportingAgent
from pathlib import Path

@app.post("/report-and-notify", tags=["Automation"], summary="Analyze, Generate Report, Flag Risk (No Email)")
async def report_and_notify_demo():
    # Step 1: Load latest MNRE (external) and internal JSONs
    external_dir = Path("audit_logs")
    internal_dir = Path("audit_logs/internal")

    internal_files = list(internal_dir.glob("*.json"))
    external_files = [f for f in external_dir.glob("*.json") if "internal" not in str(f)]

    if not internal_files or not external_files:
        raise HTTPException(status_code=404, detail="Missing required input files.")

    latest_internal = max(internal_files, key=lambda f: f.stat().st_mtime)
    latest_external = max(external_files, key=lambda f: f.stat().st_mtime)

    # Step 2: Run comparison
    flagger = RiskFlaggerAgent(str(latest_external), str(latest_internal))
    flagged = flagger.compare()

    # Step 3: Generate reports (PDF/Excel)
    reporter = ReportingAgent()
    filename = Path(latest_external).stem + "__vs__" + Path(latest_internal).stem

    flagged["filename"] = filename  # required by ReportingAgent
    excel_path = reporter.generate_excel(flagged, filename)
    pdf_path = reporter.generate_pdf(flagged, filename)

    # Step 4: Return all in response
    return {
        "message": "Risk analysis completed, reports generated.",
        "compliance_score": flagged.get("compliance_score"),
        "risk_flags": flagged.get("risk_flags"),
        "report_files": {
            "excel": str(excel_path),
            "pdf": str(pdf_path)
        },
        "compared_files": {
            "external": Path(latest_external).name,
            "internal": Path(latest_internal).name
        }
    }


# @app.post("/report-and-notify", tags=["Automation"], summary="Analyze, Generate Report, Simulate Notification")
# async def report_and_notify_demo():
#     analyzer = AnalyzingAgent()
#     data = analyzer.analyze_latest()

#     if "error" in data:
#         return {"status": "failed", "error": data["error"]}

#     filename = Path(data["filename"]).stem
#     reporter = ReportingAgent()
#     excel_path = reporter.generate_excel(data, filename)
#     pdf_path = reporter.generate_pdf(data, filename)

#     return {
#         "status": "success",
#         "message": "Analysis complete. Reports generated and notification simulated.",
#         "filename": data["filename"],
#         "excel_report": str(excel_path),
#         "pdf_report": str(pdf_path),
#         "simulated_email_to": "compliance@yourdomain.com"
#     }


# from agents.company_policy_agent import CompanyPolicyAgent

# @app.post("/upload-company-policy/")
# async def upload_internal_policy(file: UploadFile = File(...)):
#     if file.content_type != "application/pdf":
#         raise HTTPException(status_code=400, detail="Only PDF files are supported.")

#     agent = CompanyPolicyAgent(file)
#     result = agent.extract_and_save()
#     return result


# ────────────────────────────────────────────────
# 📥 JSON Download Endpoint
# ────────────────────────────────────────────────
@app.get("/documents/audit/{filename}", tags=["Audit Logs"], summary="Download Extracted Audit JSON")
async def download_json(filename: str):
    """
    Downloads a previously extracted compliance audit result in JSON format.
    """
    file_path = AUDIT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audit log not found.")
    return FileResponse(path=file_path, filename=filename, media_type='application/json')
