import numpy as np
import inspect
import json
import pandas as pd
import streamlit as st

from streamlit_extras.pdf_viewer import (pdf_viewer)  # https://arnaudmiribel.github.io/streamlit-extras/extras/pdf_viewer/
from streamlit_option_menu import (option_menu)  # https://github.com/victoryhb/streamlit-option-menu

from create_pdf import generate_pdf


st.set_page_config(
    page_title="Silhouette Card Maker",
    page_icon="🃏",
    initial_sidebar_state="collapsed",
    layout="wide",
    menu_items={  # Items in the built-in 3 dot menu top right. Not adjustable.
        "Get Help": "https://alan-cha.github.io/silhouette-card-maker/docs",
        "About": "https://github.com/Alan-Cha/silhouette-card-maker",
    },
)

LAYOUTS_JSON_PATH = "./assets/layouts.json"
OFFSET_JSON_PATH = "./calibration/data/offset_data.json"
json_dirty = {
    "layouts": False,
    "offset_data": False,
}

def get_function_params_defaults(func):
    """
    Returns a dict of parameter names and their default values for a function.
    If no default, value is None.
    """
    sig = inspect.signature(func)
    params = {}
    for name, param in sig.parameters.items():
        if param.default is inspect.Parameter.empty:
            params[name] = None
        else:
            params[name] = param.default
    return params

def dynamic_class_from_func(func):
    """
    Returns a class with __init__ that sets attributes for each parameter in func.
    """
    params = get_function_params_defaults(func)
    class DynamicSettings:
        def __init__(self, **kwargs):
            for key, default in params.items():
                setattr(self, key, kwargs.get(key, default))
    return DynamicSettings

CreatePDFSettings = dynamic_class_from_func(generate_pdf)
settings = CreatePDFSettings(card_size="standard", output_path="output.pdf")
print(settings.card_size)  # "standard"
print(settings.output_path)  # "output.pdf"

def manage_json_file(json_path: str, section = None, edits = None):
    """
    Reads or writes edits to a section of layouts.json.
    If edits is None, returns the section.
    If edits is provided, updates the section and writes the file.
    """
    with open(json_path, "r", encoding="utf8") as f:
        data = json.load(f)
        
    if edits is None:
        if section is None:
            return data
        # Just read and return the section
        return data.get(section, None)
    
    #elif any(json_dirty.values()):
    else:
        # Update the section and write back
        if section is None:
            data = edits
        else:
            data[section] = edits
            
        with open(json_path, "w", encoding="utf8") as f:
            json.dump(data, f, indent=4)
        reload_layouts()

def reload_layouts():
    layouts_json = manage_json_file(LAYOUTS_JSON_PATH)
    offsets_json = manage_json_file(OFFSET_JSON_PATH)
    if layouts_json is not None:
        st.session_state.df = pd.read_json(LAYOUTS_JSON_PATH)
        st.session_state.card_sizes_from_layouts = layouts_json["card_sizes"]
        st.session_state.paper_layouts_from_layouts = layouts_json["paper_layouts"]
    if offsets_json is not None:
        st.session_state.offset_data = offsets_json


def on_tab_change(key):
    print(f"{key}")
    #st.session_state[key] = selected_tab
    #if key

st.markdown("# Silhouette Card Maker")
if (('df' not in st.session_state) or 
    ('card_sizes_from_layouts' not in st.session_state) or 
    ('paper_layouts_from_layouts' not in st.session_state) or
    ('offset_data' not in st.session_state)
):
    reload_layouts()

selected_tab = option_menu(
    None,
    ["Generate PDFs", "Offsets", "Settings", "Edit JSON Files"],
    icons=["suit-club-fill", "rulers", "gear", ""],
    on_change=on_tab_change,
    default_index=0,
    key="selected_tab",
    orientation="horizontal",
)

if selected_tab == "Generate PDFs":
    gen_pdf_expander = st.expander("Generate PDFs", expanded=False)
    gen_pdf_form = gen_pdf_expander.form(key="gen_pdf_form")
    gen_pdf_form.write("NERDD")
    gen_pdf_form.form_submit_button("WOW")
        
    
elif selected_tab == "Offsets":
    st.write("You're a fucking loser")
elif selected_tab == "Settings":
    st.write("You're a fucking loser")
elif selected_tab == "Edit JSON Files":
    st.markdown("## Card Size Definitions")
    
    card_size_editor = st.expander("Show/Edit", icon=":material/info:")
    card_size_data = unedited_card_data = st.session_state.card_sizes_from_layouts
    edited_card_sizes = card_size_editor.data_editor(
            card_size_data,
            num_rows="fixed"
        )
    card_size_data = ''
    col1, col2 = card_size_editor.columns(2)
    col1.button('Save', key="cscol1", on_click=manage_json_file, args=(LAYOUTS_JSON_PATH, "card_sizes", edited_card_sizes))
    col2.button('Undo Changes', key="cscol2", on_click=manage_json_file, args=(LAYOUTS_JSON_PATH, "card_sizes", unedited_card_data))
    
    st.markdown("## Offset Data")
    
    offset_expander = st.expander("Show/Edit", icon=":material/info:")
    offset_data = unedited_offset_data = st.session_state.offset_data
    edited_offset_data = offset_expander.data_editor(
            offset_data,
            num_rows="fixed"
        )
    offset_data = ''
    col1, col2 = offset_expander.columns(2)
    col1.button('Save', key="oscol1", on_click=manage_json_file, args=(OFFSET_JSON_PATH, None, edited_offset_data))
    col2.button('Undo Changes', key="oscol2", on_click=manage_json_file, args=(OFFSET_JSON_PATH, None, unedited_offset_data))
    
    st.markdown("## Page Layout Definitions (Data editor doesn't like this data yet)")
    
    #paper_layout_editor = st.expander("Show/Edit", icon=":material/info:")
    #paper_layout_data = unedited_paper_layout_data = st.session_state.paper_layouts_from_layouts
    #edited_paper_layout = paper_layout_editor.data_editor(
    #        paper_layout_data,
    #        num_rows="fixed",
    #        column_config={
    #            "name": "Layout Name"}
    #    )
    #paper_layout_data = ''
    #col1, col2 = paper_layout_editor.columns(2)
    #col1.button('Save', key="plcol1", on_click=manage_json_file, args=(LAYOUTS_JSON_PATH, "paper_layouts", edited_paper_layout))
    #col2.button('Undo Changes', key="plcol2", on_click=manage_json_file, args=(LAYOUTS_JSON_PATH, "paper_layouts", unedited_paper_layout_data))