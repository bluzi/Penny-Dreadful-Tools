from typing import Dict, List, Optional

from decksite.data import deck, query
from decksite.database import db
from magic import oracle, rotation
from magic.models.card import Card
from shared import guarantee
from shared.container import Container
from shared.database import sqlescape


def load_cards(season_id: Optional[int] = None) -> List[Card]:
    sql = get_cards_sql(season_id)
    return load_cards_from_sql(sql)

def load_cards_by_person(person_id: int, season_id: Optional[int] = None) -> List[Card]:
    sql = get_cards_by_person_sql(person_id, season_id)
    return load_cards_from_sql(sql)

def load_cards_from_sql(sql: str) -> List[Card]:
    cs = [Container(r) for r in db().select(sql)]
    cards = oracle.cards_by_name()
    for c in cs:
        c.update(cards[c.name])
    return cs

def get_cards_sql(season_id: Optional[int] = None) -> str:
    return """
        SELECT
            name,
            SUM(num_decks) AS all_num_decks,
            SUM(wins) AS all_wins,
            SUM(losses) AS all_losses,
            SUM(draws) AS all_draws,
            SUM(wins - losses) AS record,
            SUM(perfect_runs) AS all_perfect_runs,
            SUM(tournament_wins) AS all_tournament_wins,
            SUM(tournament_top8s) AS all_tournament_top8s,
            IFNULL(ROUND((SUM(wins) / NULLIF(SUM(wins + losses), 0)) * 100, 1), '') AS all_win_percent,
            SUM(CASE WHEN `day` > {season_start} THEN num_decks ELSE 0 END) AS season_num_decks,
            SUM(CASE WHEN `day` > {season_start} THEN wins ELSE 0 END) AS season_wins,
            SUM(CASE WHEN `day` > {season_start} THEN losses ELSE 0 END) AS season_losses,
            SUM(CASE WHEN `day` > {season_start} THEN draws ELSE 0 END) AS season_draws,
            SUM(CASE WHEN `day` > {season_start} THEN perfect_runs ELSE 0 END) AS season_perfect_runs,
            SUM(CASE WHEN `day` > {season_start} THEN tournament_wins ELSE 0 END) AS season_tournament_wins,
            SUM(CASE WHEN `day` > {season_start} THEN tournament_top8s ELSE 0 END) AS season_tournament_top8s,
            IFNULL(ROUND((SUM(CASE WHEN `day` > {season_start} THEN wins ELSE 0 END) / NULLIF(SUM(CASE WHEN `day` > {season_start} THEN wins ELSE 0 END + CASE WHEN `day` > UNIX_TIMESTAMP(NOW() - INTERVAL 1 WEEK) THEN losses ELSE 0 END), 0)) * 100, 1), '') AS season_win_percent,
            SUM(CASE WHEN `day` > UNIX_TIMESTAMP(NOW() - INTERVAL 1 WEEK) THEN num_decks ELSE 0 END) AS week_num_decks,
            SUM(CASE WHEN `day` > UNIX_TIMESTAMP(NOW() - INTERVAL 1 WEEK) THEN wins ELSE 0 END) AS week_wins,
            SUM(CASE WHEN `day` > UNIX_TIMESTAMP(NOW() - INTERVAL 1 WEEK) THEN losses ELSE 0 END) AS week_losses,
            SUM(CASE WHEN `day` > UNIX_TIMESTAMP(NOW() - INTERVAL 1 WEEK) THEN draws ELSE 0 END) AS week_draws,
            SUM(CASE WHEN `day` > UNIX_TIMESTAMP(NOW() - INTERVAL 1 WEEK) THEN perfect_runs ELSE 0 END) AS week_perfect_runs,
            SUM(CASE WHEN `day` > UNIX_TIMESTAMP(NOW() - INTERVAL 1 WEEK) THEN tournament_wins ELSE 0 END) AS week_tournament_wins,
            SUM(CASE WHEN `day` > UNIX_TIMESTAMP(NOW() - INTERVAL 1 WEEK) THEN tournament_top8s ELSE 0 END) AS week_tournament_top8s,
            IFNULL(ROUND((SUM(CASE WHEN `day` > UNIX_TIMESTAMP(NOW() - INTERVAL 1 WEEK) THEN wins ELSE 0 END) / NULLIF(SUM(CASE WHEN `day` > UNIX_TIMESTAMP(NOW() - INTERVAL 1 WEEK) THEN wins ELSE 0 END + CASE WHEN `day` > UNIX_TIMESTAMP(NOW() - INTERVAL 1 WEEK) THEN losses ELSE 0 END), 0)) * 100, 1), '') AS week_win_percent
        FROM
            _card_stats AS cs
        LEFT JOIN
            ({season_table}) AS season ON season.start_date <= cs.day AND (season.end_date IS NULL OR season.end_date > cs.day)
        WHERE
            {season_query}
        GROUP BY
            name
        ORDER BY
            all_num_decks DESC,
            record,
            name
    """.format(season_table=query.season_table(), season_start=int(rotation.last_rotation().timestamp()), season_query=query.season_query(season_id))

def get_cards_by_person_sql(person_id: int, season_id: Optional[int] = None) -> List[Card]:
    where = 'd.person_id = {person_id}'.format(person_id=sqlescape(person_id))
    return """
        SELECT
            card AS name,
            {all_select},
            {season_select}, -- We use the season data on the homepage to calculate movement, even though we no longer use it on /cards/.
            {week_select}
        FROM
            (SELECT card, deck_id FROM deck_card GROUP BY card, deck_id) AS dc -- Don't make sideboard cards "count double".
        INNER JOIN
            deck AS d ON dc.deck_id = d.id
        {season_join}
        {nwdl_join}
        WHERE ({where}) AND ({season_query})
        GROUP BY
            dc.card
        ORDER BY
            all_num_decks DESC,
            SUM(dsum.wins - dsum.losses) DESC,
            name
    """.format(all_select=deck.nwdl_all_select(), season_select=deck.nwdl_season_select(), week_select=deck.nwdl_week_select(), season_join=query.season_join(), nwdl_join=deck.nwdl_join(), where=where, season_query=query.season_query(season_id))

def load_card(name: str, season_id: Optional[int] = None) -> Card:
    c = guarantee.exactly_one(oracle.load_cards([name]))
    c.decks = deck.load_decks('d.id IN (SELECT deck_id FROM deck_card WHERE card = {name})'.format(name=sqlescape(name)), season_id=season_id)
    c.all = Container()
    c.all_wins = sum(filter(None, [d.wins for d in c.decks]))
    c.all_losses = sum(filter(None, [d.losses for d in c.decks]))
    c.all_draws = sum(filter(None, [d.draws for d in c.decks]))
    if c.all_wins or c.all_losses:
        c.all_win_percent = round((c.all_wins / (c.all_wins + c.all_losses)) * 100, 1)
    else:
        c.all_win_percent = ''
    c.all_num_decks = len(c.decks)
    c.played_competitively = c.all_wins or c.all_losses or c.all_draws
    return c

def playability() -> Dict[str, float]:
    sql = """
        SELECT
            card AS name,
            COUNT(*) AS played
        FROM
            deck_card
        GROUP BY
            card
    """
    rs = [Container(r) for r in db().select(sql)]
    high = max([c.played for c in rs])
    return {c.name: (c.played / high) for c in rs}
