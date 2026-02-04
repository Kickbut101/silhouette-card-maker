import os
import click
from create_pdf import generate_pdf, cli
from utilities import CardSize, PaperSize

def get_click_command_options1(click_command):
    """
    Returns a list of dicts with parameter names and their default values from a click command.
    """
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

test = get_click_command_options1(cli)

for opt in test:
    if isinstance(opt['type'], click.types.StringParamType):
        print("STRING BITCHHHH")
        print(f"{opt['name']}")
    elif isinstance(opt['type'], click.types.BoolParamType):
        print("BOOOOOOOOOL")
        print(f"{opt['name']}")
    elif isinstance(opt['type'], click.types.IntRange):
        print("IntRange")
        print(f"{opt['name']}")
    elif isinstance(opt['type'], click.types.IntParamType):
        print("INTTT")
        print(f"{opt['name']}")
    elif isinstance(opt['type'], click.types.FloatParamType):
        print("FLOAT")
        print(f"{opt['name']}")
    elif isinstance(opt['type'], click.types.Choice):
        print("Choice")
        print(f"{opt['name']}")
    else:
        print("Catchall")
        print(f"{opt['name']}")