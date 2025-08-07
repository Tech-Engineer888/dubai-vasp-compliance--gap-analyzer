import streamlit as st
import gap_analyzer
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Dubai VASP Gap Analyzer",
    page_icon="🔐",
    layout="wide"
)

# Header
st.title("🚀 Dubai VASP Compliance Gap Analyzer")
st.markdown("""
_AI-powered audit for DMCC/VARA license applications_  
Find regulatory gaps before they cost you $500K+ in fines
""")

# API Key Setup
with st.expander("🔑 API Configuration"):
    pdfco_key = st.text_input("PDF.co API Key", os.getenv("PDFCO_API_KEY", ""), type="password")
    openai_key = st.text_input("OpenAI API Key", os.getenv("OPENAI_API_KEY", ""), type="password")

# File Upload
uploaded_file = st.file_uploader("Upload VASP Application PDF", type="pdf")
url_input = st.text_input("Or enter document URL")

# Analysis Trigger
if st.button("🔍 Analyze Compliance Gaps", type="primary", disabled=not (pdfco_key and openai_key)):
    if not (uploaded_file or url_input):
        st.warning("Please upload a file or enter URL")
        st.stop()
    
    with st.spinner("🚀 Analyzing document - this takes 2-5 minutes..."):
        # Process file
        file_path = url_input if url_input else uploaded_file.name
        if uploaded_file:
            with open(uploaded_file.name, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        # Run analysis
        results = gap_analyzer.analyze_document(
            file_path, 
            pdfco_key,
            openai_key
        )
        
        # Display results
        if "error" in results:
            st.error(f"Analysis failed: {results['error']}")
            st.stop()
        
        st.success(f"✅ Analysis complete: {results['summary']}")
        
        # Show critical gaps
        st.subheader("🚨 Critical Compliance Gaps")
        for gap in results['gaps']:
            if gap['criticality'] in ['critical', 'high']:
                with st.expander(f"{gap['id']}: {gap['requirement']} ({gap['criticality'].upper()})"):
                    st.markdown(f"**Analysis**: {gap['analysis']}")
                    st.markdown(f"**Reference**: {gap['reference']}")
        
        # Show medium gaps
        st.subheader("⚠️ Medium Priority Gaps")
        medium_gaps = [g for g in results['gaps'] if g['criticality'] == 'medium']
        for gap in medium_gaps:
            st.markdown(f"**{gap['id']}**: {gap['requirement']}")
        
        # Show passed checks
        st.subheader("✅ Passed Compliance Checks")
        st.write(", ".join(results['matched_rules']) if results['matched_rules'] else "None found")
        
        # Generate report
        report = f"# VASP Compliance Gap Report\n\n"
        report += f"**Document Analyzed**: {file_path}\n\n"
        for gap in results['gaps']:
            report += f"## {gap['id']}: {gap['requirement']}\n"
            report += f"- **Criticality**: {gap['criticality'].upper()}\n"
            report += f"- **Analysis**: {gap['analysis']}\n"
            report += f"- **Reference**: {gap['reference']}\n\n"
        
        # Download button
        b64 = base64.b64encode(report.encode()).decode()
        href = f'<a href="data:file/txt;base64,{b64}" download="vasp_gap_report.md">📥 Download Full Report</a>'
        st.markdown(href, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
**Next Steps**:  
1. [Get PDF.co API Key](https://pdf.co/pricing)  
2. [Get OpenAI API Key](https://platform.openai.com/api-keys)  
3. [Deploy on Streamlit Cloud](https://streamlit.io/cloud)  
""")
