from decksite.view import View
from shared.container import Container


# pylint: disable=no-self-use
class Archetypes(View):
    def __init__(self, archetypes, all_matchups) -> None:
        min_matches_for_matchups_grid = 50
        super().__init__()
        self.archetypes = archetypes
        self.decks = []
        self.roots = [a for a in self.archetypes if a.is_root]
        self.show_seasons = True

        # We need to prepare the roots so we have the archetype tree available for traversal.
        # This is possibly a sign that something is in the wrong place.
        for r in self.roots:
            self.prepare_archetype(r, self.archetypes)

        for a in self.archetypes:
            a.matchups = []
            matchups = [m for m in all_matchups if m.archetype_id == a.id]
            if len(matchups) < min_matches_for_matchups_grid:
                a.show_in_matchups_grid = False
                continue
            a.show_in_matchups_grid = True
            matchups_by_id = {b.id: b for b in matchups}
            for root in self.roots:
                for b in root.archetype_tree:
                    mu = matchups_by_id.get(b.id)
                    if mu and mu.all_wins + mu.all_losses > 0:
                        mu.has_data = True
                        mu.all_win_percent = float(mu.all_win_percent)
                        mu.color_cell = True
                        mu.hue = 120 if mu.all_win_percent >= 50 else 0
                        mu.saturation = abs(mu.all_win_percent - 50) + 50
                        mu.lightness = 80
                        mu.opponent_archetype = b
                    else:
                        mu = Container()
                        mu.has_data = False
                        mu.all_win_percent = None
                        mu.color_cell = False
                        mu.opponent_archetype = b
                    a.matchups.append(mu)

        # Now we have traversed the tree and worked out which archetypes we are going to show, annotate matchups with that information.
        for a in self.archetypes:
            for mu in a.matchups:
                mu.show_in_matchups_grid = mu.opponent_archetype.show_in_matchups_grid

        self.num_archetypes = len([mu for mu in self.archetypes[0].matchups if mu.show_in_matchups_grid]) if self.archetypes else 0

    def page_title(self):
        return 'Archetypes'
