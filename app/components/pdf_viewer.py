import streamlit as st
import base64
import os
from core.auth import database, models  

def display_pdf_viewer(temp_dir):
    if not st.session_state.get('uploaded_files'):
        return
    
    try:
        first_file = st.session_state.uploaded_files[0]
        file_path = os.path.join(temp_dir, first_file.name)
        
        with open(file_path, "rb") as f:
           base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" height="600" type="application/pdf"
                style="border-radius: 10px;">
        </iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Visualisation impossible : {str(e)}")

 # pdf_viewer.py

 

def display_pdf_viewer_by_id(doc_id: int):
    """Pré-visualise le PDF dont l’id est donné (table documents)."""
    db = database.SessionLocal()
    doc = db.get(models.Document, doc_id)
    if not doc:
        st.error("Document introuvable.")
        return

    try:
        with open(doc.path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        st.markdown(
            f"""
            <iframe src="data:application/pdf;base64,{base64_pdf}"
                    width="100%" height="600" type="application/pdf"
                    style="border-radius:10px;">
            </iframe>
            """,
            unsafe_allow_html=True,
        )
    except Exception as exc:
        st.warning(f"Visualisation impossible : {exc}")
