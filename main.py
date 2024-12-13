from flask import Flask, request, render_template, session, redirect, url_for
import tmdb
import giphy
import secrets
import config
import os

cfg = config.Load()

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)  # Ensure session is properly encrypted

app.secret_key = os.getenv('FLASK_SECRET_KEY')


tmdb_client = tmdb.Client(cfg.tmbd_token)

giphy_client = giphy.Client(cfg.giphy_api_key)

# in-memory storage for all games
games = {}

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
        print(res)  # Print the response to check its structure

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
        print(res)

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
    movie_id = request.form['movie_id']  # Assume the movie_id is passed from the form

    # Save the selection in the session
    if 'actor_selections' not in session:
        session['actor_selections'] = []
    
    if 'movie_id' not in session:
        session['movie_id'] = movie_id  # Save the movie ID in session for the redirection
    
    # Append the actor and GIF selection to session
    session['actor_selections'].append({'actor': selected_actor, 'gif': selected_gif})

    # Debugging: Check session data
    print(f"Session data after selection: {session['actor_selections']}, Movie ID: {session['movie_id']}")

    # If two actors have been selected, proceed to the final submission
    if len(session['actor_selections']) == 2:
        return redirect(url_for('submit_game'))

    # Otherwise, redirect to select the second actor
    return redirect(url_for('select_second_actor', movie_id=session['movie_id']))  # Redirect to select second actor

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

    # Generate a unique game link and game ID
    game_id = secrets.token_urlsafe(8)
    game_link = f"/game/{game_id}"

    # Store the selections and game ID in memory (or a database)
    games[game_id] = actor_selections

    # Clear the session after generating the link
    session.clear()

    # Render the 'submit_game.html' template with the actor selections and game link
    return render_template('submit_game.html', game_link=game_link, selections=actor_selections)


@app.route("/game/<game_id>")
def get_game(game_id):
    # Retrieve the game details from memory or database
    if game_id not in games:
        return "Game not found", 404

    # Fetch the actor selections for the game
    actor_selections = games[game_id]
    return render_template('game_details.html', selections=actor_selections)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

@app.route('/reset_game', methods=['GET'])
def reset_game():
    # Clear the session
    session.pop('actor_selections', None)  # Remove actor selections from session
    
    # Redirect to the movie selection page or any other starting page
    return redirect(url_for('search_form'))  # You can change this to any start page
