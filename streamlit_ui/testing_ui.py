import streamlit as st


def render_testing_tab():
    """Render the MiscTesting tab"""
    testform = st.form(key="testform", enter_to_submit=False)
    testform.form_submit_button("Submit")
