import datetime
import sys
from enum import Enum
from typing import Any, Dict, List, Tuple

import inflect
from dateutil import rrule  # type: ignore # dateutil stubs are incomplete

from decksite.data import Deck
from shared import dtutil
from shared.container import Container

# pylint: disable=invalid-name
TournamentDate = Tuple[str, datetime.datetime]

class TimeDirection(Enum):
    BEFORE = 1
    AFTER = 2

def next_tournament_info() -> Dict[str, Any]:
    return tournament_info(TimeDirection.AFTER)

def previous_tournament_info() -> Dict[str, Any]:
    return tournament_info(TimeDirection.BEFORE, units=1)

def tournament_info(time_direction: TimeDirection, units: int = 2) -> Dict[str, Any]:
    day, time = get_nearest_tournament(time_direction)
    next_tournament_time_precise = abs(dtutil.dt2ts(time) - dtutil.dt2ts(dtutil.now()))
    near = next_tournament_time_precise < 18000 # Threshold for near: 5 hours in seconds
    next_tournament_time = dtutil.display_time(next_tournament_time_precise, units)
    return {
        'next_tournament_name': 'Penny Dreadful {day}'.format(day=day),
        'next_tournament_time': next_tournament_time,
        'next_tournament_time_precise': next_tournament_time_precise,
        'near': near
    }

def get_nearest_tournament(time_direction: TimeDirection = TimeDirection.AFTER) -> TournamentDate:
    start = dtutil.now(dtutil.GATHERLING_TZ)
    if time_direction == TimeDirection.AFTER:
        index = 0
    else:
        index = -1
        start = start - datetime.timedelta(days=7)

    dates = get_all_next_tournament_dates(start, index=index)
    return sorted(dates, key=lambda t: t[1])[index]

def get_all_next_tournament_dates(start: datetime.datetime, index: int = 0) -> List[TournamentDate]:
    apac_start = start.astimezone(tz=dtutil.APAC_SERIES_TZ)
    until = start + datetime.timedelta(days=7)
    pdsat_time = ('Saturday', rrule.rrule(rrule.WEEKLY, byhour=13, byminute=30, bysecond=0, dtstart=start, until=until, byweekday=rrule.SA)[index])
    apds_time = ('APAC Sunday', rrule.rrule(rrule.WEEKLY, byhour=16, byminute=0, bysecond=0, dtstart=apac_start, until=until, byweekday=rrule.SU)[index])
    pds_time = ('Sunday', rrule.rrule(rrule.WEEKLY, byhour=13, byminute=30, bysecond=0, dtstart=start, until=until, byweekday=rrule.SU)[index])
    pdm_time = ('Monday', rrule.rrule(rrule.WEEKLY, byhour=19, byminute=0, bysecond=0, dtstart=start, until=until, byweekday=rrule.MO)[index])
    pdt_time = ('Thursday', rrule.rrule(rrule.WEEKLY, byhour=19, byminute=0, bysecond=0, dtstart=start, until=until, byweekday=rrule.TH)[index])
    return [pdsat_time, apds_time, pds_time, pdm_time, pdt_time]

def prize(d: Deck):
    return prize_by_finish(d.get('finish') or sys.maxsize)

def prize_by_finish(f: int):
    if f == 1:
        return 4
    elif f == 2:
        return 3
    elif f <= 4:
        return 2
    elif f <= 8:
        return 1
    return 0

def prizes_by_finish(multiplier: int = 1):
    prizes, finish, p = [], 1, inflect.engine()
    while True:
        pz = prize_by_finish(finish)
        if not pz:
            break
        prizes.append({'finish': p.ordinal(finish), 'prize': pz * multiplier})
        finish += 1
    return prizes

def all_series_info() -> List[Container]:
    info = get_all_next_tournament_dates(dtutil.now(dtutil.GATHERLING_TZ))
    return [
        Container({
            'name': 'Penny Dreadful Saturdays',
            'hosts': ['back_alley_g', 'bigm'],
            'display_time': '1:30pm Eastern',
            'time': info[0][1],
            'chat_room': '#PDS',
            'sponsor_name': 'Cardhoarder'
        }),
        Container({
            'name': 'APAC Penny Dreadful Sundays',
            'hosts': ['stash86', 'silasary'],
            'display_time': '4pm Japan Standard Time',
            'time': info[1][1],
            'chat_room': '#PDS',
            'sponsor_name': None
        }),
        Container({
            'name': 'Penny Dreadful Sundays',
            'hosts': ['bakert99', 'littlefield', 'mrsad'],
            'display_time': '1:30pm Eastern',
            'time': info[2][1],
            'chat_room': '#PDS',
            'sponsor_name': 'Cardhoarder'
        }),
        Container({
            'name': 'Penny Dreadful Mondays',
            'hosts': ['stash86', 'silasary'],
            'display_time': '7pm Eastern',
            'time': info[3][1],
            'chat_room': '#PDM',
            'sponsor_name': 'Cardhoarder'
        }),
        Container({
            'name': 'Penny Dreadful Thursdays',
            'hosts': ['silasary', 'stash86'],
            'display_time': '7pm Eastern',
            'time': info[4][1],
            'chat_room': '#PDT',
            'sponsor_name': 'Cardhoarder'
        })
    ]
