import streamlit as st
import base64
import os

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