from enum import Enum
from os import path
#from deck_formats import AsheCardType
from requests import Response, get
from time import sleep

CARD_ART_URL_TEMPLATE = 'https://cdn.ashes.live/images/cards/{card_stub}.jpg'
CARD_ART_URL_PHG_TEMPLATE = 'https://ashesdb-media.plaidhatgames.com/images/new-cards/{card_stub}.jpg'
DECK_URL_TEMPLATE = 'https://api.ashes.live/v2/decks/shared/{share_id}'
DECK_URL_PHG_TEMPLATE = 'https://apiasheslive.plaidhatgames.com/v2/decks/shared/{share_id}'

class AsheCardType(str, Enum):
    NORMAL = 'normal'
    CONJURATION = 'conjuration'

def request_ashes(query: str) -> Response:
    r = get(query, headers = {'user-agent': 'silhouette-card-maker/0.1', 'accept': '*/*'})

    r.raise_for_status()
    sleep(0.15)

    return r

def fetch_deck_data(deck_id: str):
    try:
        deck_response = request_ashes(DECK_URL_TEMPLATE.format(share_id=deck_id))
    except:
        deck_response = request_ashes(DECK_URL_PHG_TEMPLATE.format(share_id=deck_id))
        
    data = deck_response.json()

    phoenixborn = [data.get("phoenixborn")] or []
    phoenixborn[0]['type'] = 'normal'
    
    main = data.get("cards") or []
    
    conjuration = data.get("conjurations") or []
    conjuration[0]['type'] = 'conjuration'
    deck = phoenixborn + main + conjuration

    return deck

def fetch_card_art(index: int, card_name: str, card_stub: str, quantity: int, front_img_dir: str):

    try:
        card_stub_alt = card_stub.replace('-', '_')
        card_art = request_ashes(CARD_ART_URL_PHG_TEMPLATE.format(card_stub=card_stub_alt)).content
    except:
        card_art = request_ashes(CARD_ART_URL_TEMPLATE.format(card_stub=card_stub)).content

    if card_art is not None:
        # Save image based on quantity
        for counter in range(quantity):
            image_path = path.join(front_img_dir, f'{index}{card_name}_{counter + 1}.png')

            with open(image_path, 'wb') as f:
                f.write(card_art)

def get_handle_card( card_save_dir: str ):
    def configured_fetch_card(index: int, card_name: str, card_stub: str, quantity: int, card_save_dir):
        if card_save_dir:
            save_dir = card_save_dir
        
        fetch_card_art(
            index,
            card_name,
            card_stub,
            quantity,
            save_dir
        )

    return configured_fetch_card