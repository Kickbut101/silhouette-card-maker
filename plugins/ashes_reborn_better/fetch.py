import os
import click

# remove thsi later
#import subprocess

from deck_formats import DeckFormat, parse_deck
from ashes import get_handle_card

front_directory = os.path.join("game", "front")
default_deck_path = os.path.join("game", "decklist", "deck.txt")


@click.command()
@click.argument("deck_path", default=default_deck_path)
@click.argument("format", type=click.Choice([t.value for t in DeckFormat], case_sensitive=False))
@click.option("--share_url", show_default=True, help="Skip the deck.txt format and just enter share url")

def cli(
    deck_path: str,
    format: DeckFormat,
    share_url: str
):
    
    if share_url is None or not share_url:
        if not os.path.isfile(deck_path):
            print(f"{deck_path} is not a valid file.")
            return

        with open(deck_path, "r") as deck_file:
            deck_text = deck_file.read()
            parse_deck(deck_text, format, get_handle_card(front_directory))
            
    else:
        parse_deck(share_url, format, get_handle_card(front_directory))

if __name__ == "__main__":
    cli()
    #cli()
    #deck='game\\decklist\\deck.txt'
    #form = DeckFormat['ASHES']
    #url='https://ashes.live/decks/share/d1abcb36-f6c4-49df-89f2-6a9cdbd34cec/'
    
    #cli(deck,DeckFormat.ASHES,url)
    #cli(deck_path='game\\decklist\\deck.txt', format=DeckFormat.ASHES, share_url='https://ashes.live/decks/share/d1abcb36-f6c4-49df-89f2-6a9cdbd34cec/')
    #subprocess.run(["python", "plugins\\ashes_reborn_better\\fetch.py", "ashes"])