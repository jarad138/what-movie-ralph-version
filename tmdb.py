from urllib.parse import quote
import functools
import requests


class Client:
    token: str = ""
    def __init__(self, token):
        if not token:
            raise Exception("Token is required")
        self.token = "Bearer " + token

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": self.token,
        }

    # https://developer.themoviedb.org/reference/search-movie
    @functools.cache
    def search_movie_by_title(self, title: str):
        encoded_title = quote(title)
        url = f"https://api.themoviedb.org/3/search/movie?query={encoded_title}"
        headers = self.get_headers()

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("error:", response.text)
            raise Exception(f"Failed to fetch data: {response.status_code}")

        data = response.json()
        fields_to_keep = {"id", "title", "popularity", "poster_path", "release_date"}
        movies = sorted(data['results'], key=lambda x: x['popularity'], reverse=True)
        return filter_fields(movies, fields_to_keep)

    # https://developer.themoviedb.org/reference/movie-credits
    @functools.cache
    def get_actors_by_movie_id(self, movie_id: str, limit: int = 10):
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
        headers = self.get_headers()

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("error:", response.text)
            raise Exception(f"Failed to fetch data: {response.status_code}")

        data = response.json()

        actors = sorted(data['cast'], key=lambda x: x['popularity'], reverse=True)

        # update profile_path with full url
        for actor in actors:
            if actor.get("profile_path"):
                actor["profile_path"] = f"https://image.tmdb.org/t/p/w200{actor['profile_path']}"

        fields_to_keep = {"id", "character", "name", "popularity", "poster_path", "profile_path"}

        return filter_fields(actors, fields_to_keep)[:limit]

    @functools.cache
    def get_actor(self, actor_id: str):
        url = f"https://api.themoviedb.org/3/person/{actor_id}"
        headers = self.get_headers()

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("error:", response.text)
            raise Exception(f"Failed to fetch data: {response.status_code}")

        data = response.json()
        return data


def filter_fields(data, fields_to_keep):
    return [
        {key: value for key, value in item.items() if key in fields_to_keep}
        for item in data
    ]
