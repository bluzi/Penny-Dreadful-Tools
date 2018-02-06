from flask import url_for
from flask_babel import gettext

from decksite.view import View
from .. import babel

# pylint: disable=no-self-use
class AboutPdm(View):
    def __init__(self):
        self.about_url = url_for('about')

    def subtitle(self):
        return gettext('About')

    def languages(self) -> str:
        return ", ".join([locale.display_name for locale in babel.list_translations()])

    def TT_TRANSLATED_INTO(self) -> str:
        return gettext("This site is currently translated into:")

    def TT_HELP_TRANSLATE(self) -> str:
        return gettext("Help us translate the site into your language")
