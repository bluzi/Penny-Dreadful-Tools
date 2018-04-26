from functools import wraps
from typing import Callable, Optional

from flask import redirect, request, session, url_for

from decksite.data import person


def login_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('id') is None:
            return redirect(url_for('authenticate', target=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('admin') is None:
            return redirect(url_for('authenticate', target=request.url))
        elif session.get('admin') is False:
            return redirect(url_for('unauthorized'))
        return f(*args, **kwargs)
    return decorated_function

def logout() -> None:
    session['admin'] = None
    session['id'] = None
    session['discord_id'] = None
    session['logged_person_id'] = None
    session['person_id'] = None
    session['mtgo_username'] = None

<<<<<<< Updated upstream
def discord_id():
=======
def redirect_uri() -> str:
    uri = url_for('authenticate_callback', _external=True)
    if 'http://' in uri:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
    return uri

def discord_id() -> Optional[int]:
>>>>>>> Stashed changes
    return session.get('id')

def person_id() -> Optional[int]:
    return session.get('logged_person_id')

def mtgo_username() -> Optional[str]:
    return session.get('mtgo_username')

def login(p: person.Person) -> None:
    session['logged_person_id'] = p.id
    session['person_id'] = p.id
    session['mtgo_username'] = p.name

def hide_intro() -> bool:
    return session.get('hide_intro', False)

def load_person(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if discord_id() is not None:
            p = person.load_person_by_discord_id(discord_id())
            if p:
                login(p)
        return f(*args, **kwargs)
    return decorated_function
