from flask import url_for

from decksite.view import View


class Achievements(View):
    def __init__(self, mtgo_username):
        super().__init__()
        self.person_url = url_for('person', person_id=mtgo_username) if mtgo_username else None
        self.league_url = url_for('signup')
