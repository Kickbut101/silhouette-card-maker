import streamlit as st
import os
#from streamlit_extras.floating_button import floating_button # https://arnaudmiribel.github.io/streamlit-extras/extras/floating_button/
from streamlit_extras.pdf_viewer import pdf_viewer  # https://arnaudmiribel.github.io/streamlit-extras/extras/pdf_viewer/

def render_testing_tab():
    view_pdfs_expander = st.expander(label="View PDFs", expanded=False)
    view_pdfs_dir_input = view_pdfs_expander.text_input(label="Directory to list PDFs", value="./game/output", placeholder="./game/output")
    
    # Still buggy, doesn't auto update after file is deleted.
    try:
        files = os.listdir(view_pdfs_dir_input)
        filtered = [f for f in files if f.endswith('.pdf')]
        if len(filtered) == 0:
            view_pdfs_expander.write("No PDF files found in directory")
        for f in filtered:
            try:
                view_pdfs_ind_pdf_expander = view_pdfs_expander.expander(label=f, expanded=False)
                col1, col2, col3 = view_pdfs_ind_pdf_expander.columns([1,1,6])
                with view_pdfs_ind_pdf_expander:
                    if (col1.button("Delete this file")):
                        os.remove((os.path.join(view_pdfs_dir_input,f)))
                    pdf_viewer((os.path.join(view_pdfs_dir_input,f)))
            except:
                view_pdfs_ind_pdf_expander.write("No file")
    except:
        filtered = []
        view_pdfs_expander.write("Invalid Directory")