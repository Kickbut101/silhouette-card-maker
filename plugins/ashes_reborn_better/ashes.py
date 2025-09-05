from os import path
from requests import Response, get
from time import sleep

CARD_ART_URL_TEMPLATE = 'https://cdn.ashes.live/images/cards/{card_stub}.jpg'
CARD_ART_URL_PHG_TEMPLATE = 'https://ashesdb-media.plaidhatgames.com/images/new-cards/{card_stub}.jpg'
DECK_URL_TEMPLATE = 'https://api.ashes.live/v2/decks/shared/{share_id}'
DECK_URL_PHG_TEMPLATE = 'https://apiasheslive.plaidhatgames.com/v2/decks/shared/{share_id}'

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
    main = data.get("cards") or []
    conjuration = data.get("conjurations") or []
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

def get_handle_card(
    front_img_dir: str
):
    def configured_fetch_card(index: int, card_name: str, card_stub: str, quantity: int):
        fetch_card_art(
            index,
            card_name,
            card_stub,
            quantity,
            front_img_dir
        )

    return configured_fetch_card