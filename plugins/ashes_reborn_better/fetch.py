import os
import click

# remove thsi later
#import subprocess

from deck_formats import DeckFormat, parse_deck
from ashes import get_handle_card

front_directory = os.path.join("game", "front")
default_deck_path = os.path.join("game", "decklist", "deck.txt")
def_ashes_path = os.path.join("game", "ashes")
default_conj_path = os.path.join(def_ashes_path, "black", "front")
default_grey_path = os.path.join(def_ashes_path, "grey", "front")
default_format = 'ashes'
default_deck = '0f8855d9-3c02-45e8-8458-366cbd755a04'


@click.command()
@click.argument("deck_path", default=default_deck_path)
@click.argument("format", default=default_format, type=click.Choice([t.value for t in DeckFormat], case_sensitive=False))
@click.option("--share_url", default=default_deck, show_default=True, help="Skip the deck.txt format and just enter share url")
@click.option("--conjuration_card_dir", default=default_conj_path, show_default=True, help="Path to use to separate Conjuration Cards")
@click.option("--grey_card_dir", default=default_grey_path, show_default=True, help="Path to use to separate \"Grey Backed\" Cards")
@click.option("--delete_files_first", is_flag=True, show_default=True, default=True, help="Delete files from prior run before running again")

def cli(
    deck_path: str,
    format: DeckFormat,
    share_url: str,
    conjuration_card_dir: str,
    grey_card_dir: str,
    delete_files_first: bool
):
    
    if share_url is None or not share_url:
        if not os.path.isfile(deck_path):
            print(f"{deck_path} is not a valid file.")
            return

        with open(deck_path, "r") as deck_file:
            deck_text = deck_file.read()
            parse_deck(deck_text, format, get_handle_card(front_directory), conjuration_card_dir, grey_card_dir, delete_files_first=delete_files_first)
            
    else:
        parse_deck(share_url, format, get_handle_card(front_directory), conjuration_card_dir, grey_card_dir, delete_files_first=delete_files_first)

if __name__ == "__main__":
    #if (not "format" in locals()) or (not "format" in globals()):
    #    format = DeckFormat.ASHES.value
    #if (not "share_url" in locals()) or (not "share_url" in globals()):
    #    share_url = "https://ashesdb.plaidhatgames.com/decks/share/0f8855d9-3c02-45e8-8458-366cbd755a04/"
    cli()