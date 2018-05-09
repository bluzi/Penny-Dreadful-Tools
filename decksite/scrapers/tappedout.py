import re
import urllib
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from decksite import translation
from decksite.data import deck
from decksite.scrapers import decklist
from magic import fetcher_internal, legality
from shared import configuration
from shared.pd_exception import InvalidDataException
from shared_web import logger


DeckType = Dict[str, Any]

def scrape() -> None:
    login()
    logger.warning('Logged in to TappedOut: {is_authorised}'.format(is_authorised=is_authorised()))
    raw_decks = fetch_decks()
    for raw_deck in raw_decks:
        try:
            if is_authorised():
                raw_deck.update(fetch_deck_details(raw_deck))
            raw_deck = set_values(raw_deck)
            deck.add_deck(raw_deck)
        except InvalidDataException as e:
            logger.warning('Skipping {slug} because of {e}'.format(slug=raw_deck.get('slug', '-no slug-'), e=e))

def fetch_decks() -> List[DeckType]:
    return fetcher_internal.fetch_json('https://tappedout.net/api/deck/latest/penny-dreadful/')

def fetch_deck_details(raw_deck: DeckType) -> DeckType:
    return fetcher_internal.fetch_json('https://tappedout.net/api/collection/collection:deck/{slug}/'.format(slug=raw_deck['slug']))

def set_values(raw_deck: DeckType) -> DeckType:
    raw_deck = translation.translate(translation.TAPPEDOUT, raw_deck)
    if 'inventory' in raw_deck:
        raw_deck['cards'] = parse_inventory(raw_deck['inventory'])
    else:
        raw_decklist = fetcher_internal.fetch('{base_url}?fmt=txt'.format(base_url=raw_deck['url']))
        raw_deck['cards'] = decklist.parse(raw_decklist)
    raw_deck['source'] = 'Tapped Out'
    raw_deck['identifier'] = raw_deck['url']
    return raw_deck

def parse_inventory(inventory: List[List[Any]]) -> decklist.DecklistType:
    d: decklist.DecklistType = {'maindeck': {}, 'sideboard': {}}
    for name, board in inventory:
        # Decklists can contain editions. eg: Island (INV)
        # We can't handle these right now.
        removeset = re.match(r'([^\(]+)(\(\w\w\w\))?', name)
        if removeset is not None:
            name = removeset.group(1)
        # Same with comments
        removecomments = re.match(r'(.*?)#', name)
        if removecomments is not None:
            name = removecomments.group(1)
        # Same with foil indicators
        removefoil = re.match(r'(.*?) \*F\*', name)
        if removefoil is not None:
            name = removefoil.group(1)
        if board['b'] == 'main':
            d['maindeck'][name] = board['qty']
        elif board['b'] == 'side':
            d['sideboard'][name] = board['qty']
    return d

def is_authorised() -> bool:
    return fetcher_internal.SESSION.cookies.get('tapped') is not None

def login(user: Optional[str] = None, password: Optional[str] = None) -> None:
    if user is None:
        user = configuration.get_str('to_username')
    if password is None:
        password = configuration.get_str('to_password')
    if user == '' or password == '':
        logger.warning('No TappedOut credentials provided')
        return
    url = 'https://tappedout.net/accounts/login/'
    session = fetcher_internal.SESSION
    response = session.get(url)

    match = re.search(r"<input type='hidden' name='csrfmiddlewaretoken' value='(\w+)' />", response.text)
    if match is None:
        # Already logged in?
        return
    csrf = match.group(1)

    data = {
        'csrfmiddlewaretoken': csrf,
        'next': '/',
        'username': user,
        'password': password,
    }
    headers = {
        'referer': url,
    }
    logger.warning('Logging in to TappedOut as {0}'.format(user))
    response = session.post(url, data=data, headers=headers)
    if response.status_code == 403:
        logger.warning('Failed to log in')

def scrape_url(url: str) -> deck.Deck:
    if not url.endswith('/'):
        url += '/'
    path = urllib.parse.urlparse(url).path
    slug = path.split('/')[2]
    raw_deck: DeckType = {}
    raw_deck['slug'] = slug
    raw_deck['url'] = url
    if is_authorised():
        raw_deck.update(fetch_deck_details(raw_deck))
    else:
        raw_deck.update(parse_printable(raw_deck))
    raw_deck = set_values(raw_deck)
    vivified = decklist.vivify(raw_deck['cards'])
    errors: Dict[str, List[str]] = {}
    if 'Penny Dreadful' not in legality.legal_formats(vivified, None, errors):
        print(repr(raw_deck['cards']))
        raise InvalidDataException('Deck is not legal in Penny Dreadful - {error}'.format(error=errors.get('Penny Dreadful')))
    else:
        return deck.add_deck(raw_deck)

def parse_printable(raw_deck: DeckType) -> DeckType:
    """If we're not authorized for the TappedOut API, this method will collect name and author of a deck.
    It could also grab a date, but I haven't implemented that yet."""
    s = fetcher_internal.fetch(raw_deck['url'] + '?fmt=printable')
    soup = BeautifulSoup(s, 'html.parser')
    raw_deck['name'] = soup.find('h2').string.strip('"')
    infobox = soup.find('table', {'id': 'info_box'})
    user = infobox.find('td', string='User')
    raw_deck['user'] = user.find_next_sibling('td').string
    return raw_deck

def scrape_user(username):
    parsed = {}
    parsed['username'] = username
    s = fetcher_internal.fetch('https://tappedout.net/users/{0}/'.format(username))
    soup = BeautifulSoup(s, 'html.parser')
    mtgo = soup.find('td', string='MTGO Username')
    if mtgo is not None:
        parsed['mtgo_username'] = mtgo.find_next_sibling('td').string
    else:
        parsed['mtgo_username'] = None
    return parsed
