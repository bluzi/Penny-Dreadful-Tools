from typing import Any, Dict, List

from decksite.view import View
from magic import rotation
from magic.models import Card


# pylint: disable=no-self-use
class RotationChanges(View):
    def __init__(self, cards_in: List[Card], cards_out: List[Card], playability: Dict[str, float], speculation: bool = False) -> None:
        super().__init__()
        self.sections: List[Dict[str, Any]] = []
        self.cards = cards_in + cards_out
        entries_in = [{'name': c.name, 'card': c, 'interestingness': rotation.interesting(playability, c, speculation)} for c in cards_in]
        entries_out = [{'name': c.name, 'card': c, 'interestingness': rotation.interesting(playability, c, speculation, new=False)} for c in cards_out]
        self.sections.append({'name': 'New this season', 'entries': entries_in, 'num_entries': len(entries_in)})
        self.sections.append({'name': 'Rotated out', 'entries': entries_out, 'num_entries': len(entries_out)})
        self.speculation = speculation
        self.show_interesting = True
        self.show_seasons = not speculation

    def page_title(self):
        if self.speculation:
            return 'Rotation Speculation'
        return 'Rotation Changes'
