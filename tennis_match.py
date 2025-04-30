PLAYER_1 = 0
PLAYER_2 = 1 

class TennisGame:
    def __init__(self):
        self.points = [0, 15, 30, 40]
        self.score = [0, 0]
        self.advantage = None
        self.winner = None

    def point_won_by(self, player_index, sudden_death=False):
        opponent = 1 - player_index
        if self.winner:
            return self.winner

        if self.score[player_index] == 40 and self.score[opponent] < 40:
            self.winner = player_index
        elif self.score[player_index] == 40 and self.score[opponent] == 40:
            if sudden_death:
                self.winner = player_index
            else:
                if self.advantage == player_index:
                    self.winner = player_index
                elif self.advantage == opponent:
                    self.advantage = None
                else:
                    self.advantage = player_index
        else:
            self.score[player_index] = self.points[self.points.index(self.score[player_index]) + 1]

        return self.winner

    def reset(self):
        self.score = [0, 0]
        self.advantage = None
        self.winner = None


class TennisSet:
    def __init__(self):
        self.games = [0, 0]
        self.winner = None

    def game_won_by(self, player_index):
        self.games[player_index] += 1
        opponent = 1 - player_index
        if self.games[player_index] >= 6 and (self.games[player_index] - self.games[opponent]) >= 2:
            self.winner = player_index

    def reset(self):
        self.games = [0, 0]
        self.winner = None


class TennisMatch:
    def __init__(self, player1, player2, sudden_death=False, best_of=3):
        self.players = [player1, player2]
        self.sets_won = [0, 0]
        self.best_of = best_of
        self.current_game = TennisGame()
        self.current_set = TennisSet()
        self.match_winner = None
        self.history = []
        self.snapshots = []
        self.sudden_death = sudden_death

    def point_won_by(self, player_index):
        if self.match_winner:
            return

        # 🛑 Take a snapshot BEFORE applying changes
        self.take_snapshot()

        game_winner = self.current_game.point_won_by(player_index, self.sudden_death)
        if game_winner is not None:
            self.current_set.game_won_by(game_winner)
            self.history.append(f"Game won by {self.players[game_winner]}")
            self.current_game.reset()

            if self.current_set.winner is not None:
                self.sets_won[self.current_set.winner] += 1
                self.history.append(f"Set won by {self.players[self.current_set.winner]}")

                if self.sets_won[self.current_set.winner] > self.best_of // 2:
                    self.match_winner = self.players[self.current_set.winner]
                    self.history.append(f"Match won by {self.match_winner}")
                self.current_set.reset()


    def get_score_display(self):
        g = self.current_game
        p1_score, p2_score = g.score
        s = f"SETS: {self.sets_won[PLAYER_1]} - {self.sets_won[PLAYER_2]}<br>"
        s += f"GAMES: {self.current_set.games[PLAYER_1]} - {self.current_set.games[PLAYER_2]}<br>"

        if g.winner is None:
            s += "SCORE: "
            if p1_score == p2_score == 40 and g.advantage is None:
                s += "Deuce"
                if self.sudden_death:
                    s += "<br>No-Ad Scoring. Next point decides the game."
            elif g.advantage is not None:
                s += f"Advantage {self.players[g.advantage]}"
            else:
                s += f"{p1_score} - {p2_score}"
        else:
            s += f"Game won by {self.players[g.winner]}"
        return s
    
    # def get_score_display(self):
    #     g = self.current_game
    #     p1_score, p2_score = g.score
    #     s = "Sets:<br>"
    #     s += f"{self.players[PLAYER_1]} {self.sets_won[PLAYER_1]} - {self.sets_won[PLAYER_2]} {self.players[PLAYER_1]}<br>"
    #     s += "Games:<br>"
    #     s += f"{self.players[PLAYER_1]} {self.current_set.games[PLAYER_1]} - {self.current_set.games[PLAYER_2]} {self.players[PLAYER_2]}<br>"

    #     if g.winner is None:
    #         if p1_score == p2_score == 40 and g.advantage is None:
    #             s += "Game: Deuce"
    #             if self.sudden_death:
    #                 s += "<br>No-Ad Scoring. Next point decides the game."
    #         elif g.advantage is not None:
    #             s += f"Game: Advantage {self.players[g.advantage]}"
    #         else:
    #             s += "Points:<br>"
    #             s += f"{self.players[PLAYER_1]} {p1_score} - {p2_score} {self.players[PLAYER_2]}"
    #     else:
    #         s += f"Game won by {self.players[g.winner]}"
    #     return s
    
    def take_snapshot(self):
        snapshot = {
            "sets_won": list(self.sets_won),
            "games": list(self.current_set.games),
            "score": list(self.current_game.score),
            "advantage": self.current_game.advantage,
            "game_winner": self.current_game.winner,
            "set_winner": self.current_set.winner,
            "match_winner": self.match_winner,
            "history": list(self.history)
        }
        self.snapshots.append(snapshot)

            # ⚡️ Keep only the last 5 snapshots
        if len(self.snapshots) > 5:
            self.snapshots.pop(0)

    def undo(self):
        if self.snapshots:
            snapshot = self.snapshots.pop()
            self.sets_won = snapshot["sets_won"]
            self.current_set.games = snapshot["games"]
            self.current_game.score = snapshot["score"]
            self.current_game.advantage = snapshot["advantage"]
            self.current_game.winner = snapshot["game_winner"]
            self.current_set.winner = snapshot["set_winner"]
            self.match_winner = snapshot["match_winner"]
            self.history = snapshot["history"]


    def get_history(self):
        return self.history
    

    def to_dict(self):
        """For serialization.
        """
        return {
            "players": self.players,
            "sets_won": self.sets_won,
            "current_game": {
                "score": self.current_game.score,
                "advantage": self.current_game.advantage,
                "winner": self.current_game.winner
            },
            "current_set": {
                "games": self.current_set.games,
                "winner": self.current_set.winner
            },
            "match_winner": self.match_winner,
            "history": self.history,
            "snapshots": self.snapshots,
            "sudden_death": self.sudden_death
        }

    @classmethod
    def from_dict(cls, data):
        """For deserialization.
        """
        match = cls(data["players"][PLAYER_1], data["players"][PLAYER_2], sudden_death=data.get("sudden_death", False))
        match.sets_won = data["sets_won"]
        match.current_game.score = data["current_game"]["score"]
        match.current_game.advantage = data["current_game"]["advantage"]
        match.current_game.winner = data["current_game"]["winner"]
        match.current_set.games = data["current_set"]["games"]
        match.current_set.winner = data["current_set"]["winner"]
        match.match_winner = data["match_winner"]
        match.history = data["history"]
        match.snapshots = data.get("snapshots", [])
        return match

    
    