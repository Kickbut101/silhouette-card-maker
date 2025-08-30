import numpy as np
import inspect
import json
import pandas as pd
import streamlit as st
import re
import operator
import io, sys
import os

from contextlib import redirect_stdout
from streamlit_extras.pdf_viewer import (
    pdf_viewer,
)  # https://arnaudmiribel.github.io/streamlit-extras/extras/pdf_viewer/
from streamlit_option_menu import (
    option_menu,
)  # https://github.com/victoryhb/streamlit-option-menu

import click
from utilities import (
    load_saved_offset,
    offset_images,
    save_offset,
    load_user_prefs,
    CardSize,
    PaperSize,
    OffsetData
)
from create_pdf import cli, generate_pdf
from offset_pdf import offset_pdf


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
USERPREFS_JSON_PATH = "./userprefs.json"
HELP_DOCUMENTATION_URL = 'https://alan-cha.github.io/silhouette-card-maker/'

def manage_json_file(json_path: str, section=None, edits=None):
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
    else:
        # Update the section and write back
        if section is None:
            data = edits
        else:
            data[section] = edits

        with open(json_path, "w", encoding="utf8") as f:
            json.dump(data, f, indent=4)
        reload_jsons()


def reload_jsons():
    layouts_json = manage_json_file(LAYOUTS_JSON_PATH)
    try:
        offsets_data = load_saved_offset(path=OFFSET_JSON_PATH)
    except:
        pass
    if layouts_json is not None:
        st.session_state.df = pd.read_json(LAYOUTS_JSON_PATH)
        st.session_state.card_sizes_from_layouts = layouts_json["card_sizes"]
        st.session_state.paper_layouts_from_layouts = layouts_json["paper_layouts"]
    if offsets_data is not None:
        st.session_state.offsets_data = offsets_data


def validate_gen_options(options_dict):
    if options_dict['front_dir_path'] is None:
        options_dict['front_dir_path'] = ""
    if options_dict['back_dir_path'] is None:
        options_dict['back_dir_path'] = ""
    if options_dict['double_sided_dir_path'] is None:
        options_dict['double_sided_dir_path'] = ""
    if options_dict['output_path'] is None:
        options_dict['output_path'] = ""
    if options_dict['output_images'] is None:
        options_dict['output_images'] = False
    if options_dict['card_size'] is None:
        options_dict['card_size'] = ""
    if options_dict['paper_size'] is None:
        options_dict['paper_size'] = ""
    if options_dict['only_fronts'] is None:
        options_dict['only_fronts'] = False
    #if options_dict.get('crop'):
    #    temp = options_dict['crop']
    #    del options_dict['crop']
    #    options_dict['crop_string'] = temp
    #if options_dict['crop'] is None:
    #    options_dict['crop'] = ""
    if options_dict['extend_corners'] is None:
        options_dict['extend_corners'] = 0
    if options_dict['ppi'] is None:
        options_dict['ppi'] = 300
    if options_dict['quality'] is None:
        options_dict['quality'] = 100
    #if options_dict['skip_indices'] is None:
    #    options_dict['skip_indices'] = []
    if options_dict['load_offset'] is None:
        options_dict['load_offset'] = False
    if options_dict['name'] is None:
        options_dict['name'] = ""
    return options_dict

def get_click_command_options(click_command):
    """
    Returns a list of dicts with parameter names and their default values from a click command.
    
    """
    # This is dumb, I could have just called the function name + .params, 
    
    options = []
    for param in click_command.params:
        if isinstance(param, click.Option):
            options.append(
                {
                    "name": param.name,
                    "default": param.default,
                    "help": param.help,
                    "is_flag": param.is_flag,
                    "type": param.type,
                    "show_default": param.show_default,
                    "value": param.default,
                    "required": param.required,
                    "expose_value": param.expose_value
                }
            )
    return options

def convert_click_options_to_dict(options):
    
    my_dict = {}
    
    for o in options:
        if (o['value'] is not None) and (not o['value'] == ""):
            my_dict[o['name']] = o['value']
        else:
            my_dict[o['name']] = ''
        #elif o['default'] is not None:
        #    my_dict[o['name']] = o['default']
    return my_dict


def on_tab_change(key):
    pass

def save_cached_data(cachename, variable):
    st.session_state.cachename = variable

st.markdown("# Silhouette Card Maker")
if (
    ("df" not in st.session_state)
    or ("card_sizes_from_layouts" not in st.session_state)
    or ("paper_layouts_from_layouts" not in st.session_state)
    or ("offsets_data" not in st.session_state)
):
    reload_jsons()

selected_tab = option_menu(
    None,
    ["Generate PDFs", "Offsets", "Edit Settings/JSON Files"],
    icons=["suit-club-fill", "rulers", "gear"],
    on_change=on_tab_change,
    default_index=0,
    key="selected_tab",
    orientation="horizontal",
)

if selected_tab == "Generate PDFs":
    
    if (
    ("create_pdf_options" not in st.session_state)
    ):
        create_pdf_options = get_click_command_options(cli)
        st.session_state.create_pdf_options = create_pdf_options
    else:
        create_pdf_options = st.session_state.create_pdf_options


    gen_pdf_expander = st.expander("Generate PDFs", expanded=False)
    card_size = gen_pdf_expander.pills(label="Card Size", options=[c.name for c in CardSize],default="STANDARD")
    paper_size = gen_pdf_expander.pills(label="Paper Size", options=[p.name for p in PaperSize],default="LETTER")
    
    gen_pdf_form = gen_pdf_expander.form(key="gen_pdf_form", enter_to_submit=False)

    gen_pdf_form.link_button("create_pdf.py Documentation Page", 'https://alan-cha.github.io/silhouette-card-maker/docs/create/', icon=":material/live_help:")

    gpcol1, gpcol2, gpcol3 = gen_pdf_form.columns([1, 1, 1])
    
    optional = gpcol3.expander("Additional Options", expanded=False)

    # gen_pdf_form.write(list(map(operator.itemgetter("type"), create_pdf_options)))

    for opt in create_pdf_options:
        if isinstance(opt["type"], click.types.StringParamType):
            if opt["show_default"] is True:
                if re.search(r"directory|path", opt["help"]):
                    opt["value"] = gpcol1.text_input(
                        label=opt["help"],
                        value=opt['value'],
                        placeholder=opt['default'],
                        key=opt["name"],
                    )
                else:
                    opt["value"] = gpcol1.text_input(
                        label=opt["help"],
                        value=opt["value"],
                        placeholder=opt["default"],
                        key=opt["name"],
                    )
            else:
                opt["value"] = optional.text_input(
                    label=opt["help"],
                    value=opt["value"],
                    placeholder=opt["default"],
                    key=opt["name"],
                )
                
        elif isinstance(opt["type"], click.types.BoolParamType):
            if opt["is_flag"]:
                if opt["show_default"] is True:
                    opt["value"] = gpcol3.toggle(
                        label=opt["help"], value=opt["value"], key=opt["name"]
                    )
                else:
                    opt["value"] = optional.toggle(
                        label=opt["help"], value=opt["value"], key=opt["name"]
                    )

        elif isinstance(opt["type"], click.types.IntRange):
            num_input_kwargs = {
                "label": opt["help"],
                "value": opt["value"],
                "key": opt["name"],
            }

            if getattr(opt["type"], "max", None) is not None:
                num_input_kwargs["max_value"] = opt["type"].max

            if getattr(opt["type"], "min", None) is not None:
                num_input_kwargs["min_value"] = opt["type"].min

            opt["value"] = gpcol2.number_input(**num_input_kwargs)

        elif isinstance(opt["type"], click.types.IntParamType):
            pass
        elif isinstance(opt["type"], click.types.FloatParamType):
            pass
        elif isinstance(opt["type"], click.types.Choice):
            if re.search(r"card_size", opt["name"]):
                opt["value"] = CardSize[card_size].value
            if re.search(r"paper_size", opt["name"]):
                opt["value"] = PaperSize[paper_size].value
        else:
            pass
    gen_pdf_only_save = gen_pdf_form.toggle(label="Just save my values (Don't Submit)")
    gen_pdf_form_submit = gen_pdf_form.form_submit_button(label="Create PDFs", on_click=save_cached_data, args=("create_pdf_options",create_pdf_options))

    if gen_pdf_form_submit:
        if not gen_pdf_only_save:
            create_pdf_options_dict = convert_click_options_to_dict(create_pdf_options)
            del create_pdf_options_dict["version"]
            
            create_pdf_options_dict = validate_gen_options(create_pdf_options_dict)
            
            print(create_pdf_options_dict)
            cli.callback(**create_pdf_options_dict)
            st.success("PDF Generation Sent")
        # Maybe bug? I think one of these two are not working.
        st.session_state.create_pdf_options = create_pdf_options
        save_cached_data("create_pdf_options",create_pdf_options)


elif selected_tab == "Offsets":
    
    if (
    ("offset_pdf_options" not in st.session_state)
    ):
        offset_pdf_options = get_click_command_options(offset_pdf)
        st.session_state.offset_pdf_options = offset_pdf_options
    else:
        offset_pdf_options = st.session_state.offset_pdf_options
    
    offset_pdf_expander = st.expander("Adjust Offsets", expanded=False)
    offset_pdf_form = offset_pdf_expander.form(key="offset_pdf_form", enter_to_submit=False)
    
    try:
        if st.session_state.offsets_data:
            temp_offset = st.session_state.offsets_data
            for o in offset_pdf_options:
                if o['name'] == "x_offset":
                    o['value'] = temp_offset.x_offset
                elif o['name'] == "y_offset":
                    o['value'] = temp_offset.y_offset

        offset_pdf_form.link_button("offset_pdf.py Documentation Page", 'https://alan-cha.github.io/silhouette-card-maker/docs/offset/', icon=":material/live_help:")

        opcol1, opcol2 = offset_pdf_form.columns([1, 1])
        
        for opt in offset_pdf_options:

            if isinstance(opt["type"], click.types.StringParamType):
                opt["value"] = opcol1.text_input(
                    label=opt["help"],
                    value=opt['value'],
                    placeholder=opt['default'],
                    key=opt["name"],
                )
                    
            elif isinstance(opt["type"], click.types.BoolParamType):
                if opt["is_flag"]:
                    opt["value"] = opcol2.toggle(
                        label=opt["help"], value=opt["value"], key=opt["name"]
                    )

            elif isinstance(opt["type"], click.types.IntRange):
                num_input_kwargs = {
                    "label": opt["help"],
                    "value": opt["value"],
                    "key": opt["name"],
                }

                if getattr(opt["type"], "max", None) is not None:
                    num_input_kwargs["max_value"] = opt["type"].max

                if getattr(opt["type"], "min", None) is not None:
                    num_input_kwargs["min_value"] = opt["type"].min

                opt["value"] = opcol2.number_input(**num_input_kwargs)

            elif isinstance(opt["type"], click.types.IntParamType):
                num_input_kwargs = {
                    "label": opt["help"],
                    "value": opt["value"],
                    "key": opt["name"],
                    "step": 1
                }
                if getattr(opt["type"], "max", None) is not None:
                    num_input_kwargs["max_value"] = opt["type"].max

                if getattr(opt["type"], "min", None) is not None:
                    num_input_kwargs["min_value"] = opt["type"].min

                opt["value"] = opcol1.number_input(**num_input_kwargs)
            elif isinstance(opt["type"], click.types.FloatParamType):
                pass
            elif isinstance(opt["type"], click.types.Choice):
                if re.search(r"card_size|paper_size", opt["name"]):
                    pass
                else:
                    print(f"Choice, {opt['name']}")

            else:
                pass
        gen_offset_only_save = offset_pdf_form.toggle(label="Just save my values (Don't Submit)")
    except:
        offset_pdf_form.write("No Offset data loaded/found.")
        pass
    
    running_log_placeholder = st.empty()
    
    if (offset_pdf_form.form_submit_button("Submit/Save")):
        if not gen_offset_only_save:
            offset_pdf_options_dict = convert_click_options_to_dict(offset_pdf_options)
            offset_pdf.callback(**offset_pdf_options_dict)
            offset_pdf_expander.info("PDF Generation Sent")
        # Maybe bug? I think one of these two are not working.
        st.session_state.offset_pdf_options = offset_pdf_options
        save_cached_data("offset_pdf_options",offset_pdf_options)
            
        
    
elif selected_tab == "Edit Settings/JSON Files":
    st.markdown("## Card Size Definitions")

    card_size_editor = st.expander("Show/Edit", icon=":material/info:")
    card_size_data = unedited_card_data = st.session_state.card_sizes_from_layouts
    edited_card_sizes = card_size_editor.data_editor(card_size_data, num_rows="fixed")
    card_size_data = ""
    col1, col2 = card_size_editor.columns(2)
    col1.button(
        "Save",
        key="cscol1",
        on_click=manage_json_file,
        args=(LAYOUTS_JSON_PATH, "card_sizes", edited_card_sizes),
    )
    col2.button(
        "Undo Changes",
        key="cscol2",
        on_click=manage_json_file,
        args=(LAYOUTS_JSON_PATH, "card_sizes", unedited_card_data),
    )

    st.markdown("## Offset Data")

    offset_expander = st.expander("Show/Edit", icon=":material/info:")
    offsets_data = unedited_offsets_data = st.session_state.offsets_data
    edited_offsets_data = offset_expander.data_editor(offsets_data, num_rows="fixed")
    offsets_data = ""
    col1, col2 = offset_expander.columns(2)
    col1.button(
        "Save",
        key="oscol1",
        on_click=manage_json_file,
        args=(OFFSET_JSON_PATH, None, edited_offsets_data),
    )
    col2.button(
        "Undo Changes",
        key="oscol2",
        on_click=manage_json_file,
        args=(OFFSET_JSON_PATH, None, unedited_offsets_data),
    )

    st.markdown("## Page Layout Definitions (Data editor doesn't like this data yet)")


#offset_pdf_formdata
#offset_pdf_form

# if __name__ == '__main__':
#    os.system("echo py -m streamlit run .\start_streamlit.py")
