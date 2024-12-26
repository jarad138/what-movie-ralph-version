from flask import Flask, request, render_template, session, redirect, url_for
import tmdb
import giphy
import secrets
import config
import os
import json

cfg = config.Load()

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)  # Ensure session is properly encrypted

app.secret_key = os.getenv('FLASK_SECRET_KEY')


tmdb_client = tmdb.Client(cfg.tmbd_token)

giphy_client = giphy.Client(cfg.giphy_api_key)

# in-memory storage for all games
games = {}


@app.route('/')
def homepage():
    return render_template('homepage.html')



@app.route('/search', methods=['GET'])
def search_form():
    return render_template('movie_search.html')

@app.route('/movies', methods=['GET'])
def search_movies():
    query = request.args.get('query')
    if not query:
        return "No movie name provided", 400

    try:
        # Call the API to search for the movie
        res = tmdb_client.search_movie_by_title(query)

        if isinstance(res, list):
            movies = res
        else:
            movies = res.get('results', [])

        return render_template('select_movie.html', movies=movies)
    except Exception as e:
        print("search_movies error: ", e)
        return {"error": str(e)}, 500





@app.route('/movies/actors/<movie_id>', methods=['GET'])
def get_actors_by_movie_id(movie_id):
    try:
        res = tmdb_client.get_actors_by_movie_id(movie_id)

        if isinstance(res, list):
            actors = res
        elif isinstance(res, dict):
            actors = res.get('cast', [])
        else:
            actors = []

        # Pass movie_id to the template
        return render_template('select_actors.html', actors=actors, movie_id=movie_id)
    except Exception as e:
        print("get_actors_by_movie error: ", e)
        return {"error": str(e)}, 500



@app.route('/gifs', methods=['GET'])
def search_gifs():
    actor_name = request.args.get('query')
    movie_id = request.args.get('movie_id')

    if not actor_name or not movie_id:
        return "Missing actor name or movie ID", 400

    limit = request.args.get('limit', 5)  # Set a default limit for GIFs

    try:
        res = giphy_client.gifs_search(actor_name, limit)
        gifs = res['data']  # Assume 'data' contains a list of GIF data
        return render_template('select_gif.html', gifs=gifs, actor_name=actor_name, movie_id=movie_id)
    except Exception as e:
        print("giphy error: ", e)
        return {"error": str(e)}, 500



@app.route('/gifs/submit', methods=['POST'])
def submit_gif():
    selected_gif = request.form['gif_url']
    selected_actor = request.form['actor_name']
    movie_id = request.form['movie_id']

    # if poster path is not is session then lets go get it and add it.
    # there's a better way to do this. we can just add it to the form and pass it along.
    # but this works for now. 
    if 'poster_path' not in session or 'title' not in session:
        try:
            print("fetching movie by id:", movie_id)
            movie = tmdb_client.get_movie_by_id(movie_id)
            session['poster_path'] = movie.get("poster_path")
            session['title'] = movie.get("title")
            print("poster path:", movie.get("poster_path"))
            print("title:", movie.get("title"))
        except Exception as e:
            print("get_movie_by_id error: ", e)

    if 'actor_selections' not in session:
        session['actor_selections'] = []

    if 'movie_id' not in session:
        session['movie_id'] = movie_id  # Save the movie ID in session for the redirection


    # we have to get the actors first cause what if there is already one in there.
    actor_selections = session.get('actor_selections', [])
    # Append the actor and GIF to session
    print("adding actor and gif to session:", selected_actor)
    # now we add the actors to actor_selections. 
    actor_selections.append({'actor': selected_actor, 'gif': selected_gif})
    # now we set actor_selections back to the session which will have both actors.
    session['actor_selections'] = actor_selections

    # Debugging: Check session data
    print(f"Session data after selection: {session['actor_selections']}")

    if len(session['actor_selections']) == 2:
        return redirect(url_for('submit_game'))

    return redirect(url_for('select_second_actor', movie_id=session['movie_id']))


@app.route('/select_second_actor', methods=['GET'])
def select_second_actor():
    movie_id = request.args.get('movie_id')  # Get the movie_id from the query string
    if not movie_id:
        return "Movie ID is missing", 400

    # Fetch the actors for this movie using the movie_id
    return redirect(url_for('get_actors_by_movie_id', movie_id=movie_id))


@app.route('/submit_game', methods=['GET'])
def submit_game():
    # Retrieve selections from the session
    actor_selections = session.get('actor_selections', [])

    # Debugging: Check the selections data
    print(f"Actor selections: {actor_selections}")

    # Generate a unique game link and game ID
    game_id = secrets.token_urlsafe(8)
    game_link = f"/game/{game_id}"

    # get the movie data from the session and add it to the template.
    movie = {}
    movie['title'] = session['title']
    movie['poster_path'] = session['poster_path']

    # create game object to store in memory
    game = {
        'title': session['title'],
        'poster_path': session['poster_path'],
        'actor_selections': actor_selections
    }

    # Store the selections and game ID in memory (or a database later)
    games[game_id] = game

    # Clear the session after generating the link
    session.clear()

    # Render the 'submit_game.html' template with the actor selections and game link
    return render_template('submit_game.html', game_link=game_link, selections=actor_selections, movie=movie)

@app.route('/submit_guess/<game_id>', methods=['POST'])
def submit_guess(game_id):
    # Retrieve the guess from the form
    user_guess = request.form['guess']

    # Retrieve the correct answer from the game data
    game_data = games.get(game_id)

    if not game_data:
        return "Game not found", 404

    correct_answer = "some correct answer based on game data"  # Logic to determine the correct movie

    # Check if the guess is correct
    if user_guess.lower() == correct_answer.lower():
        result = "Correct!"
    else:
        result = f"Incorrect! The correct answer was {correct_answer}"

    return render_template('guess_result.html', result=result)




@app.route("/game/<game_id>")
def get_game(game_id):
    # Retrieve the game details from memory or database
    if game_id not in games:
        return "Game not found", 404

    print("game data:", games[game_id])

    # Fetch the actor selections for the game
    actor_selections = games[game_id].get('actor_selections', [])
    return render_template('game_details.html', selections=actor_selections)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

@app.route('/reset_game', methods=['GET'])
def reset_game():
    # Clear the session
    session.pop('actor_selections', None)  # Remove actor selections from session
    
    # Redirect to the movie selection page or any other starting page
    return redirect(url_for('search_form'))  # You can change this to any start page

