import streamlit as st
from agents.extraction_agent import ExtractionAgent
from agents.risk_flagger_agent import RiskFlaggerAgent
from agents.reporting_agent import ReportingAgent
from core.file_utils import save_json_audit
from pathlib import Path
import json

st.set_page_config(page_title="Compliance Risk Dashboard", layout="wide")
st.title("🛡 Autonomous Compliance Risk Dashboard")

st.markdown("Upload latest **MNRE regulation** and your **internal compliance policy** to begin risk comparison.")

col1, col2 = st.columns(2)

uploaded_mnre = col1.file_uploader("📤 Upload MNRE Regulation PDF", type=["pdf"])
uploaded_sop = col2.file_uploader("📤 Upload Internal Policy PDF", type=["pdf"])

if uploaded_mnre and uploaded_sop:
    st.success("✅ Files received. Extracting...")

    # Run ExtractionAgent for both PDFs
    mnre_agent = ExtractionAgent(uploaded_mnre)
    mnre_data = mnre_agent.run()
    mnre_path = save_json_audit(mnre_data, uploaded_mnre.name, folder="streamlit_app/extracted")

    sop_agent = ExtractionAgent(uploaded_sop)
    sop_data = sop_agent.run()
    sop_path = save_json_audit(sop_data, uploaded_sop.name, folder="streamlit_app/extracted")

    st.subheader("📄 Extracted Content")
    with st.expander("MNRE Regulation Data"):
        st.json(mnre_data)
    with st.expander("Internal Policy Data"):
        st.json(sop_data)

    st.subheader("🔍 Compare for Compliance Risk")
    if st.button("🚨 Run Risk Comparison"):
        flagger = RiskFlaggerAgent(mnre_path, sop_path)
        flagged = flagger.compare()
        st.success("Comparison complete ✅")

        st.metric("Compliance Score", f"{flagged.get('compliance_score', 'N/A')}%")
        st.write("### ⚠️ Risk Flags")
        for flag in flagged.get("risk_flags", []):
            st.warning(flag)

        # Generate reports
        reporter = ReportingAgent()
        filename = Path(uploaded_mnre.name).stem + "__vs__" + Path(uploaded_sop.name).stem
        pdf_path = reporter.generate_pdf(flagged, filename)
        excel_path = reporter.generate_excel(flagged, filename)

        st.subheader("📥 Download Reports")
        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF Report", f, file_name=f"{filename}.pdf", mime="application/pdf")
        with open(excel_path, "rb") as f:
            st.download_button("Download Excel Report", f, file_name=f"{filename}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
import streamlit as st
from agents.extraction_agent import ExtractionAgent
from agents.risk_flagger_agent import RiskFlaggerAgent
from agents.reporting_agent import ReportingAgent
from core.file_utils import save_json_audit
from pathlib import Path
import json

st.set_page_config(page_title="Compliance Risk Dashboard", layout="wide")
st.title("🛡 Autonomous Compliance Risk Dashboard")

st.markdown("Upload latest **MNRE regulation** and your **internal compliance policy** to begin risk comparison.")

col1, col2 = st.columns(2)

uploaded_mnre = col1.file_uploader("📤 Upload MNRE Regulation PDF", type=["pdf"])
uploaded_sop = col2.file_uploader("📤 Upload Internal Policy PDF", type=["pdf"])

if uploaded_mnre and uploaded_sop:
    st.success("✅ Files received. Extracting...")

    # Run ExtractionAgent for both PDFs
    mnre_agent = ExtractionAgent(uploaded_mnre)
    mnre_data = mnre_agent.run()
    mnre_path = save_json_audit(mnre_data, uploaded_mnre.name, folder="streamlit_app/extracted")

    sop_agent = ExtractionAgent(uploaded_sop)
    sop_data = sop_agent.run()
    sop_path = save_json_audit(sop_data, uploaded_sop.name, folder="streamlit_app/extracted")

    st.subheader("📄 Extracted Content")
    with st.expander("MNRE Regulation Data"):
        st.json(mnre_data)
    with st.expander("Internal Policy Data"):
        st.json(sop_data)

    st.subheader("🔍 Compare for Compliance Risk")
    if st.button("🚨 Run Risk Comparison"):
        flagger = RiskFlaggerAgent(mnre_path, sop_path)
        flagged = flagger.compare()
        st.success("Comparison complete ✅")

        st.metric("Compliance Score", f"{flagged.get('compliance_score', 'N/A')}%")
        st.write("### ⚠️ Risk Flags")
        for flag in flagged.get("risk_flags", []):
            st.warning(flag)

        # Generate reports
        reporter = ReportingAgent()
        filename = Path(uploaded_mnre.name).stem + "__vs__" + Path(uploaded_sop.name).stem
        pdf_path = reporter.generate_pdf(flagged, filename)
        excel_path = reporter.generate_excel(flagged, filename)

        st.subheader("📥 Download Reports")
        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF Report", f, file_name=f"{filename}.pdf", mime="application/pdf")
        with open(excel_path, "rb") as f:
            st.download_button("Download Excel Report", f, file_name=f"{filename}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
