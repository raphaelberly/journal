from app import db
from app.models import Record, Title, User

MANIFEST = {
    "id": "movie-recommendation-service",
    "name": "Movie Service",
    "description": "Provides lists of recently watched movies for users.",
    "methods": [
        {
            "name": "getRecentMovies",
            "description": "Fetches a list of the most recently watched movies for a given user.",
            "parameters": [
                {
                    "name": "user_id",
                    "type": "integer",
                    "description": "The unique identifier for the user.",
                    "required": True
                },
                {
                    "name": "number_of_movies",
                    "type": "integer",
                    "description": "The maximum number of movies to return.",
                    "required": False,
                    "default": 5
                }
            ]
        }
    ]
}


def get_recent_movies_logic(user_id: int, number_of_movies: int = 5):

    query = db.session \
        .query(Record, Title) \
        .select_from(Record).join(Title) \
        .filter(Record.user_id == user_id) \
        .filter(Record.include_in_recent == True) \
        .order_by(Record.date.desc(), Record.insert_datetime_utc.desc()) \
        .limit(number_of_movies)

    user_language = User.query.get(user_id).language

    output_raw = [(record.export(), title.export(user_language)) for record, title in query.all()]

    # Return the requested number of movies, slicing the list
    return [{
        "date_added_by_user": record['date'].isoformat(),
        "grade_by_user": record['grade'],
        "title": title['title'],
        "year": title['year'],
        "genres": title['genres'],
        "duration": title['duration'],
        "director_names": title['director_names'],
        "imdb_rating": title['imdb_rating'],
    } for record, title in output_raw]


METHOD_DISPATCHER = {
    "getRecentMovies": get_recent_movies_logic,
}
