import re
import sys, os

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
parent = os.path.dirname(parent)
# adding the parent directory to 
# the sys.path.
sys.path.append(parent)

from enum import Enum
from _collections_abc import Set
from clean_up import *
from typing import Callable, Tuple
from ashes import fetch_deck_data, get_handle_card


GUID_REGEX_PATTERN = r'.*(([a-fA-F0-9]{8})-?([a-fA-F0-9]{4})-?([a-fA-F0-9]{4})-?([a-fA-F0-9]{4})-?([a-fA-F0-9]{12})).*'

card_data_tuple = Tuple[str, str, int] # name, image, quantity

class DeckFormat(str, Enum):
    ASHES = 'ashes'

def parse_deck_helper(
        deck_text: str,
        handle_card: Callable,
        deck_splitter: Callable,
        is_card_line: Callable,
        extract_card_data: Callable,
        conjuration_card_dir, 
        grey_card_dir
    ) -> None:
    error_lines = []
    index = 0
    for line in deck_splitter(deck_text):
        if is_card_line(line):
            index = index + 1
            
            name, stub, quantity, ctype = extract_card_data(line)

            print(f'Index: {index}, quantity: {quantity}, stub: {stub}, name: {name}')
            try:
                if (grey_card_dir is not None) and (conjuration_card_dir is not None):
                    if ctype == 'normal':
                        dir = grey_card_dir
                    elif ctype == 'conjuration':
                        dir = conjuration_card_dir
                    handle_card(index, name, stub, quantity, dir)
                else:
                    handle_card(index, name, stub, quantity)
            except Exception as e:
                print(f'Error: {e}')
                error_lines.append((line, e))
        else:
            print(f'Skipping: "{line}"')

    if len(error_lines) > 0:
        print(f'Errors: {error_lines}')

def parse_ashes(deck_text: str, handle_card: Callable, conjuration_card_dir, grey_card_dir):

    def is_ashes_deck(deck_url: str) -> bool:
        return bool(re.match(GUID_REGEX_PATTERN, deck_url))

    def is_ashes_line(line) -> bool:
        return line.get("name") and line.get("stub")

    def extract_ashes_card_data(line) -> card_data_tuple:
        if is_ashes_line(line):
            quantity = line.get("count") or 1
            name = line.get("name")
            stub = line.get("stub")
            cardtype = line.get("type")

            return (name, stub, quantity, cardtype)

    def split_ashes_deck(deck_text: str) -> Set[str]:
        text_iterable = deck_text.strip().split('\n')
        decks = []
        for text in text_iterable:
            if is_ashes_deck(text):
                match = re.match(GUID_REGEX_PATTERN,text)
                deck = fetch_deck_data(match.group(1))
                decks += deck
        return deck

    parse_deck_helper(deck_text, handle_card, split_ashes_deck, is_ashes_line, extract_ashes_card_data, conjuration_card_dir, grey_card_dir)

def parse_deck(deck_text: str, format: DeckFormat, handle_card: Callable, conjuration_card_dir, grey_card_dir, delete_files_first):
    if format == DeckFormat.ASHES:
        # Had to inverse thsi, for some fucking reason
        if not (delete_files_first):
            delete_files.callback(dirs=[conjuration_card_dir,grey_card_dir], root='game')
        
        parse_ashes(deck_text, handle_card, conjuration_card_dir, grey_card_dir)
    else:
        raise ValueError('Unrecognized deck format.')

if __name__ == '__main__':
    parse_deck()
    #parse_deck('https://ashes.live/decks/share/d1abcb36-f6c4-49df-89f2-6a9cdbd34cec/',DeckFormat.ASHES,get_handle_card(os.path.join("game", "front")))