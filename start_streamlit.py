from streamlit_extras.pdf_viewer import (
    pdf_viewer,
)  # https://arnaudmiribel.github.io/streamlit-extras/extras/pdf_viewer/
from streamlit_option_menu import (
    option_menu,
)  # https://github.com/victoryhb/streamlit-option-menu

import os
import subprocess
import importlib.util
import click

from utilities import *
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
    [
        "Run Plugin",
        "Generate PDFs",
        "Offsets",
        "Edit Settings/JSON Files",
        "MiscTesting",
    ],
    icons=["download", "suit-club-fill", "rulers", "gear", "bug"],
    on_change=on_tab_change,
    default_index=0,
    key="selected_tab",
    orientation="horizontal",
)

if selected_tab == "Run Plugin":
    st.markdown("## Run Plugin")

    # Get available plugins
    plugins_dir = "plugins"
    available_plugin_dirs = [
        d
        for d in os.listdir(plugins_dir)
        if os.path.isdir(os.path.join(plugins_dir, d))
    ]

    # Create mapping of display names to directory names
    plugin_options = {
        get_plugin_display_name(plugin_dir): plugin_dir
        for plugin_dir in available_plugin_dirs
    }

    plugin_expander = st.expander("Card Fetching", expanded=True)

    with plugin_expander:
        # Plugin selection with user-friendly names
        selected_plugin_display = st.selectbox(
            "Select Card Game Plugin",
            list(plugin_options.keys()),
            help="Choose the card game plugin to use for fetching card images",
        )

        # Get the actual directory name from the selected display name
        selected_plugin = plugin_options[selected_plugin_display]

        # Deck list management
        decklist_dir = os.path.join("game", "decklist")
        os.makedirs(decklist_dir, exist_ok=True)

        # Get existing deck files
        existing_files = [
            f
            for f in os.listdir(decklist_dir)
            if f.endswith((".txt", ".ydk", ".ydke"))
            and os.path.isfile(os.path.join(decklist_dir, f))
        ]

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Select Existing Deck")
            selected_file = st.selectbox(
                "Choose existing deck file",
                [""] + existing_files,
                help="Select a previously uploaded deck file",
            )

        with col2:
            st.subheader("Upload New Deck")
            uploaded_file = st.file_uploader(
                "Upload deck file",
                type=["txt", "ydk", "ydke"],
                help="Upload a new deck file (.txt, .ydk, or .ydke)",
            )

            if uploaded_file is not None:
                # Save uploaded file to decklist directory
                file_path = os.path.join(decklist_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"File {uploaded_file.name} uploaded successfully!")
                st.rerun()  # Refresh to show the new file in the dropdown

        # Determine which file to use
        deck_file_path = None
        if uploaded_file is not None:
            deck_file_path = os.path.join(decklist_dir, uploaded_file.name)
        elif selected_file:
            deck_file_path = os.path.join(decklist_dir, selected_file)

        if deck_file_path:
            st.info(f"Selected deck file: {os.path.basename(deck_file_path)}")

            fetch_file = os.path.join(plugins_dir, selected_plugin, "fetch.py")
            if os.path.exists(fetch_file):

                try:
                    import sys

                    plugin_path = os.path.join(plugins_dir, selected_plugin)

                    if plugin_path not in sys.path:
                        sys.path.insert(0, plugin_path)

                    try:
                        spec = importlib.util.spec_from_file_location(
                            "deck_formats",
                            os.path.join(
                                plugins_dir, selected_plugin, "deck_formats.py"
                            ),
                        )
                        deck_formats_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(deck_formats_module)

                        if hasattr(deck_formats_module, "DeckFormat"):
                            format_options = [
                                fmt.value for fmt in deck_formats_module.DeckFormat
                            ]
                            selected_format = st.selectbox(
                                "Deck Format",
                                format_options,
                                help="Select the format of your deck file",
                            )
                        else:
                            selected_format = st.text_input(
                                "Deck Format",
                                help="Enter the deck format (plugin doesn't define standard formats)",
                            )
                    finally:
                        # Remove the plugin path from sys.path to avoid conflicts
                        if plugin_path in sys.path:
                            sys.path.remove(plugin_path)

                except Exception as e:
                    st.warning(
                        f"Could not load deck formats for {selected_plugin}: {e}"
                    )
                    selected_format = st.text_input(
                        "Deck Format", help="Enter the deck format manually"
                    )

                # Try to import the plugin's fetch CLI to get optional arguments
                plugin_options = []
                try:
                    import sys

                    plugin_path = os.path.join(plugins_dir, selected_plugin)

                    # Temporarily add the plugin directory to Python path
                    if plugin_path not in sys.path:
                        sys.path.insert(0, plugin_path)

                    try:
                        spec = importlib.util.spec_from_file_location(
                            "fetch", fetch_file
                        )
                        fetch_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(fetch_module)

                        if hasattr(fetch_module, "cli"):
                            plugin_options = get_click_command_options(fetch_module.cli)

                            # Filter out the required arguments (deck_path and format)
                            plugin_options = [
                                opt
                                for opt in plugin_options
                                if opt["name"] not in ["deck_path", "format"]
                            ]
                    finally:
                        # Remove the plugin path from sys.path to avoid conflicts
                        if plugin_path in sys.path:
                            sys.path.remove(plugin_path)

                        if plugin_options:
                            st.subheader("Plugin Options")

                            # Create columns for organizing options
                            opt_col1, opt_col2 = st.columns(2)

                            for i, opt in enumerate(plugin_options):
                                # Alternate between columns
                                current_col = opt_col1 if i % 2 == 0 else opt_col2

                                with current_col:
                                    if isinstance(
                                        opt["type"], click.types.StringParamType
                                    ):
                                        if opt.get("multiple", False):
                                            # Handle multiple values (like prefer_set)
                                            opt["value"] = st.text_input(
                                                label=opt["help"] or opt["name"],
                                                value="",
                                                placeholder="Enter multiple values separated by commas",
                                                key=f"plugin_opt_{opt['name']}",
                                                help=(
                                                    f"Multiple values allowed. {opt['help']}"
                                                    if opt["help"]
                                                    else "Multiple values allowed"
                                                ),
                                            )
                                        else:
                                            opt["value"] = st.text_input(
                                                label=opt["help"] or opt["name"],
                                                value=opt.get("default", ""),
                                                key=f"plugin_opt_{opt['name']}",
                                            )

                                    elif isinstance(
                                        opt["type"], click.types.BoolParamType
                                    ):
                                        if opt.get("is_flag", False):
                                            opt["value"] = st.checkbox(
                                                label=opt["help"] or opt["name"],
                                                value=opt.get("default", False),
                                                key=f"plugin_opt_{opt['name']}",
                                            )

                                    elif isinstance(opt["type"], click.types.IntRange):
                                        num_input_kwargs = {
                                            "label": opt["help"] or opt["name"],
                                            "value": opt.get("default", 0),
                                            "key": f"plugin_opt_{opt['name']}",
                                        }

                                        if (
                                            hasattr(opt["type"], "max")
                                            and opt["type"].max is not None
                                        ):
                                            num_input_kwargs["max_value"] = opt[
                                                "type"
                                            ].max
                                        if (
                                            hasattr(opt["type"], "min")
                                            and opt["type"].min is not None
                                        ):
                                            num_input_kwargs["min_value"] = opt[
                                                "type"
                                            ].min

                                        opt["value"] = st.number_input(
                                            **num_input_kwargs
                                        )

                                    elif isinstance(
                                        opt["type"], click.types.IntParamType
                                    ):
                                        opt["value"] = st.number_input(
                                            label=opt["help"] or opt["name"],
                                            value=opt.get("default", 0),
                                            step=1,
                                            key=f"plugin_opt_{opt['name']}",
                                        )

                                    elif isinstance(
                                        opt["type"], click.types.FloatParamType
                                    ):
                                        opt["value"] = st.number_input(
                                            label=opt["help"] or opt["name"],
                                            value=float(opt.get("default", 0.0)),
                                            key=f"plugin_opt_{opt['name']}",
                                        )

                                    elif isinstance(opt["type"], click.types.Choice):
                                        opt["value"] = st.selectbox(
                                            label=opt["help"] or opt["name"],
                                            options=opt["type"].choices,
                                            index=(
                                                0
                                                if opt.get("default") is None
                                                else opt["type"].choices.index(
                                                    opt["default"]
                                                )
                                            ),
                                            key=f"plugin_opt_{opt['name']}",
                                        )

                                    else:
                                        # Fallback for unknown types
                                        opt["value"] = st.text_input(
                                            label=opt["help"] or opt["name"],
                                            value=str(opt.get("default", "")),
                                            key=f"plugin_opt_{opt['name']}",
                                        )

                except Exception as e:
                    st.info(f"Could not load plugin options for {selected_plugin}: {e}")

                # Generate Cards button
                if st.button("Generate Cards", type="primary"):
                    if selected_format:
                        try:
                            # Prepare command to run the plugin's fetch.py
                            cmd = [
                                "python",
                                fetch_file,
                                deck_file_path,
                                selected_format,
                            ]

                            # Add optional arguments
                            for opt in plugin_options:
                                if "value" in opt and opt["value"]:
                                    option_name = (
                                        f"--{opt['name']}"  # Keep underscores as-is
                                    )

                                    if isinstance(
                                        opt["type"], click.types.BoolParamType
                                    ) and opt.get("is_flag", False):
                                        # For boolean flags, only add the flag if True
                                        if opt["value"]:
                                            cmd.append(option_name)
                                    elif opt.get("multiple", False) and isinstance(
                                        opt["value"], str
                                    ):
                                        # Handle multiple values (split by comma)
                                        for value in opt["value"].split(","):
                                            value = value.strip()
                                            if value:
                                                cmd.extend([option_name, value])
                                    else:
                                        # Regular option with value
                                        cmd.extend([option_name, str(opt["value"])])

                            with st.spinner(
                                f"Fetching cards using {selected_plugin} plugin..."
                            ):
                                # Show the command being executed (for debugging)
                                st.code(" ".join(cmd))

                                # Run the fetch command
                                result = subprocess.run(
                                    cmd, capture_output=True, text=True, cwd=os.getcwd()
                                )

                                if result.returncode == 0:
                                    st.success("Cards fetched successfully!")
                                    if result.stdout:
                                        st.text_area(
                                            "Output:", result.stdout, height=200
                                        )
                                else:
                                    st.error("Error fetching cards:")
                                    if result.stderr:
                                        st.text_area(
                                            "Error:", result.stderr, height=200
                                        )
                                    if result.stdout:
                                        st.text_area(
                                            "Output:", result.stdout, height=200
                                        )

                        except Exception as e:
                            st.error(f"Failed to run plugin: {e}")
                    else:
                        st.warning("Please select a deck format")
            else:
                st.error(f"Plugin {selected_plugin} does not have a fetch.py file")
        else:
            st.info("Please select or upload a deck file to continue")

elif selected_tab == "Generate PDFs":

    if "create_pdf_options" not in st.session_state:
        create_pdf_options = get_click_command_options(cli)
        st.session_state.create_pdf_options = create_pdf_options
    else:
        create_pdf_options = st.session_state.create_pdf_options

    gen_pdf_expander = st.expander("Generate PDFs", expanded=False)
    card_size = gen_pdf_expander.pills(
        label="Card Size", options=[c.name for c in CardSize], default="STANDARD"
    )
    paper_size = gen_pdf_expander.pills(
        label="Paper Size", options=[p.name for p in PaperSize], default="LETTER"
    )

    gen_pdf_form = gen_pdf_expander.form(key="gen_pdf_form", enter_to_submit=False)

    gen_pdf_form.link_button(
        "create_pdf.py Documentation Page",
        "https://alan-cha.github.io/silhouette-card-maker/docs/create/",
        icon=":material/live_help:",
    )

    gpcol1, gpcol2, gpcol3 = gen_pdf_form.columns([1, 1, 1])

    optional = gpcol3.expander("Additional Options", expanded=False)

    for opt in create_pdf_options:
        if isinstance(opt["type"], click.types.StringParamType):
            if opt["show_default"] is True:
                if re.search(r"directory|path", opt["help"]):
                    opt["value"] = gpcol1.text_input(
                        label=opt["help"],
                        value=opt["value"],
                        placeholder=opt["default"],
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
    gen_pdf_form_submit = gen_pdf_form.form_submit_button(
        label="Create PDFs",
        on_click=save_cached_data,
        args=("create_pdf_options", create_pdf_options),
    )

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
        save_cached_data("create_pdf_options", create_pdf_options)

elif selected_tab == "Offsets":

    if "offset_pdf_options" not in st.session_state:
        offset_pdf_options = get_click_command_options(offset_pdf)
        st.session_state.offset_pdf_options = offset_pdf_options
    else:
        offset_pdf_options = st.session_state.offset_pdf_options

    offset_pdf_expander = st.expander("Adjust Offsets", expanded=False)
    offset_pdf_form = offset_pdf_expander.form(
        key="offset_pdf_form", enter_to_submit=False
    )

    try:
        if st.session_state.offsets_data:
            temp_offset = st.session_state.offsets_data
            for o in offset_pdf_options:
                if o["name"] == "x_offset":
                    o["value"] = temp_offset.x_offset
                elif o["name"] == "y_offset":
                    o["value"] = temp_offset.y_offset

        offset_pdf_form.link_button(
            "offset_pdf.py Documentation Page",
            "https://alan-cha.github.io/silhouette-card-maker/docs/offset/",
            icon=":material/live_help:",
        )

        opcol1, opcol2 = offset_pdf_form.columns([1, 1])

        for opt in offset_pdf_options:

            if isinstance(opt["type"], click.types.StringParamType):
                opt["value"] = opcol1.text_input(
                    label=opt["help"],
                    value=opt["value"],
                    placeholder=opt["default"],
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
                    "step": 1,
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
        gen_offset_only_save = offset_pdf_form.toggle(
            label="Just save my values (Don't Submit)"
        )
    except:
        offset_pdf_form.write("No Offset data loaded/found.")
        pass

    running_log_placeholder = st.empty()

    if offset_pdf_form.form_submit_button("Submit/Save"):
        if not gen_offset_only_save:
            offset_pdf_options_dict = convert_click_options_to_dict(offset_pdf_options)
            offset_pdf.callback(**offset_pdf_options_dict)
            offset_pdf_expander.info("PDF Generation Sent")
        # Maybe bug? I think one of these two are not working.
        st.session_state.offset_pdf_options = offset_pdf_options
        save_cached_data("offset_pdf_options", offset_pdf_options)

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
    try:
        offsets_data = unedited_offsets_data = st.session_state.offsets_data
        edited_offsets_data = offset_expander.data_editor(
            offsets_data, num_rows="fixed"
        )
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
    except:
        offset_expander.write("No Offset data loaded/found.")
    st.markdown("## Page Layout Definitions (Data editor doesn't like this data yet)")

elif selected_tab == "MiscTesting":
    testform = st.form(key="testform", enter_to_submit=False)
    testform.form_submit_button("Submit")
