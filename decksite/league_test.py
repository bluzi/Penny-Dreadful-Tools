from decksite import league
from shared import dtutil


def test_determine_end_of_league() -> None:
    next_rotation = dtutil.parse('2018-02-01 00:00:00', '%Y-%m-%d %H:%M:%S', dtutil.WOTC_TZ)
    start_date = dtutil.parse('2017-11-01 00:00:00', '%Y-%m-%d %H:%M:%S', dtutil.WOTC_TZ)
    end_date = league.determine_end_of_league(start_date, next_rotation)
    assert dtutil.dt2ts(end_date) == 1512115199
    start_date = dtutil.parse('2017-10-31 11:59:59.999', '%Y-%m-%d %H:%M:%S.%f', dtutil.WOTC_TZ)
    end_date = league.determine_end_of_league(start_date, next_rotation)
    assert dtutil.dt2ts(end_date) == 1512115199

def test_determine_end_of_league_with_rotation() -> None:
    next_rotation = dtutil.parse('2018-07-13 00:00:00', '%Y-%m-%d %H:%M:%S', dtutil.WOTC_TZ)
    start_date = dtutil.parse('2018-05-31 11:04:15', '%Y-%m-%d %H:%M:%S', dtutil.WOTC_TZ)
    end_date = league.determine_end_of_league(start_date, next_rotation)
    assert dtutil.dt2ts(end_date) == dtutil.dt2ts(next_rotation) - 1
    start_date = dtutil.parse('2018-07-13 00:00:00', '%Y-%m-%d %H:%M:%S', dtutil.WOTC_TZ)
    end_date = league.determine_end_of_league(start_date, next_rotation)
    assert end_date == dtutil.parse('2018-07-31 23:59:59', '%Y-%m-%d %H:%M:%S', dtutil.WOTC_TZ)
    start_date = dtutil.parse('2018-08-01 00:00:00', '%Y-%m-%d %H:%M:%S', dtutil.WOTC_TZ)
    end_date = league.determine_end_of_league(start_date, next_rotation)
    assert end_date == dtutil.parse('2018-08-31 23:59:59', '%Y-%m-%d %H:%M:%S', dtutil.WOTC_TZ)

def test_determine_league_name() -> None:
    end_date = dtutil.ts2dt(1512115199).astimezone(dtutil.WOTC_TZ)
    assert league.determine_league_name(end_date) == 'League November 2017'
