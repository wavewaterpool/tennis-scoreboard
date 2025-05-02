from flask import Flask, render_template, request, redirect, session, url_for, send_file
from tennis_match import TennisMatch
import json
import io

app = Flask(__name__)
app.secret_key = "secret_sekreto"

@app.get("/")
def index():      
    return render_template("index.html")

@app.post("/start")
def start_match():
    p1 = request.form["player1"]
    p2 = request.form["player2"]
    sudden_death = bool(request.form.get("sudden_death"))
    tiebreak_enabled = bool(request.form.get("tiebreak_enabled"))
    num_sets = int(request.form.get("num_sets", 3))
    
    match = TennisMatch(
        p1, 
        p2, 
        sudden_death=sudden_death, 
        best_of=num_sets,
        tiebreak_enabled=tiebreak_enabled)
    save_match_to_session(match)
    return redirect("/match")

@app.route("/match", methods=["GET"])
def match_view():
    match = load_match()
    if not match:
        return redirect("/")
    return render_template(
        "match.html",
        match=match,
        score=match.get_score_display(),
        history=match.get_history(),
        winner=match.match_winner,
        p1=match.players[0],
        p2=match.players[1]
    )


@app.route("/adjust", methods=["GET", "POST"])
def adjust_score():
    match = load_match()
    if not match:
        return redirect("/")

    if request.method == "POST":
        try:
            game_p1 = int(request.form["game_p1"])
            game_p2 = int(request.form["game_p2"])
            set_p1 = int(request.form["set_p1"])
            set_p2 = int(request.form["set_p2"])
            point_p1 = int(request.form["point_p1"])
            point_p2 = int(request.form["point_p2"])

            match.current_set.games = [game_p1, game_p2]
            match.sets_won = [set_p1, set_p2]
            match.current_game.score = [point_p1, point_p2]
            match.current_game.advantage = None
            match.current_game.winner = None
            match.current_set.winner = None
            match.match_winner = None
            match.history.append("Manual score adjustment made.")
            save_match_to_session(match)

        except Exception as e:
            print(f"Error adjusting: {e}")
        return redirect("/match")

    return render_template("adjust.html", match=match)

@app.route("/load", methods=["POST"])
def load_match_file():
    file = request.files.get("matchfile")
    if not file:
        return redirect("/")

    try:
        file_content = file.read()
        match_data = json.loads(file_content)
        match = TennisMatch.from_dict(match_data)
        save_match_to_session(match)
        return render_template("match.html", match=match)
    except Exception as e:
        print(f"Error loading match: {e}")
        return redirect("/")

@app.route("/save")
def save_match_file():
    match = load_match()
    if not match:
        return redirect("/")

    # Create in-memory file
    match_data = json.dumps(match.to_dict(), indent=4)
    buffer = io.BytesIO()
    buffer.write(match_data.encode("utf-8"))
    buffer.seek(0)

    filename = f"{match.players[0]}_vs_{match.players[1]}_match.json"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/json"
    )

@app.route("/undo")
def undo():
    match = load_match()
    if match:
        match.undo()
        save_match_to_session(match)
    return redirect("/match")


# @app.route("/point/<int:player>")
@app.post("/point/<int:player>")
def point(player):
    match = load_match()
    print(f"inside point route -> tennis game type: {type(match.current_game)}")
    if match:
        """add a logic here when tiebreak mode is True"""
        match.point_won_by(player)
        save_match_to_session(match)
    return redirect("/match")

@app.route("/reset")
def reset():
    match = load_match()
    if match:
        match = TennisMatch(
            match.players[0], 
            match.players[1], 
            sudden_death=match.sudden_death, 
            best_of=match.best_of, 
            tiebreak_enabled=match.tiebreak_enabled)
        save_match_to_session(match)
    return redirect("/match")


def load_match():
    if "match" in session:
        data = json.loads(session["match"])
        return TennisMatch.from_dict(data)
    return None

def save_match_to_session(match):
    session["match"] = json.dumps(match.to_dict())



if __name__ == "__main__":
    app.run(host="192.168.0.187", debug=True)