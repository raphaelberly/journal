from datetime import datetime


class TitleConverter(object):

    @staticmethod
    def json_to_table(item: dict) -> dict:
        title = {
            'id': item['id'],
            'imdb_id': item.get('imdb_id'),
            'title': item['title'],
            'release_date': datetime.strptime(item['release_date'], '%Y-%m-%d'),
            'original_title': item['original_title'],
            'original_language': item['original_language'],
            'director_names': [item['name'] for item in item['credits'].get('crew', []) if item['job'] == 'Director'],
            'director_ids': [item['id'] for item in item['credits'].get('crew', []) if item['job'] == 'Director'],
            'genres': [genre['name'] for genre in item.get('genres', [])],
            'top_cast_names': [item['name'] for item in item['credits'].get('cast', [])[:3]],
            'top_cast_ids': [item['id'] for item in item['credits'].get('cast', [])[:3]],
            'poster_path': item.get('poster_path'),
            'runtime': item.get('runtime'),
            'revenue': item.get('revenue'),
            'budget': item.get('budget'),
            'tagline': item.get('tagline'),
            'imdb_rating': item.get('imdb_rating'),
        }
        return title

    @staticmethod
    def table_to_front(item: dict, language: str = 'fr') -> dict:
        title = {
            'id': item['id'],
            'imdb_id': item.get('imdb_id'),
            'title': item['original_title'] if item['original_language'] == language else item['title'],
            'year': item['release_date'].year,
            'genres': item['genres'][:3],
            'top_cast_names': item['top_cast_names'],
            'top_cast_ids': item['top_cast_ids'],
            'director_names': item['director_names'],
            'director_ids': item['director_ids'],
            'duration': f'{item["runtime"] // 60}h {item["runtime"] % 60}min' if item.get('runtime') else None,
            'poster_url': 'https://image.tmdb.org/t/p/w200' + item['poster_path'] if item.get('poster_path') else None,
            'imdb_rating': item.get('imdb_rating'),
        }
        return title

    @staticmethod
    def json_to_front(item: dict, language: str = 'fr') -> dict:
        title = {
            'id': item['id'],
            'imdb_id': item.get('imdb_id'),
            'title': item['original_title'] if item['original_language'] == language else item['title'],
            'year': item['release_date'][:4],
            'genres': [genre['name'] for genre in item.get('genres', [])[:3]],
            'top_cast_names': [item['name'] for item in item['credits'].get('cast', [])[:4]],
            'top_cast_ids': [item['id'] for item in item['credits'].get('cast', [])[:4]],
            'director_names': [item['name'] for item in item['credits'].get('crew', []) if item['job'] == 'Director'],
            'director_ids': [item['id'] for item in item['credits'].get('crew', []) if item['job'] == 'Director'],
            'duration': f'{item["runtime"] // 60}h {item["runtime"] % 60}min' if item.get('runtime') else None,
            'poster_url': 'https://image.tmdb.org/t/p/w200' + item['poster_path'] if item.get('poster_path') else None,
            'imdb_rating': item.get('imdb_rating'),
        }
        return title


class CrewConverter:

    CREW_ROLES = {
        'Director': 'director',
        'Original Music Composer': 'composer'
    }

    @classmethod
    def crew_generator(cls, item):
        for i, actor in enumerate(item['credits'].get('cast', [])):
            yield ({
                'id': actor['id'],
                'name': actor['name'],
                'gender': actor['gender'],
                'profile_path': actor['profile_path'],
            }, {
                'id': actor['credit_id'],
                'tmdb_id': item['id'],
                'person_id': actor['id'],
                'role': 'actress' if actor['gender'] == 1 else 'actor',
                'cast_rank': i + 1,
            })
        for crew_member in item['credits'].get('crew', []):
            if crew_member['job'] in cls.CREW_ROLES.keys():
                yield ({
                    'id': crew_member['id'],
                    'name': crew_member['name'],
                    'gender': crew_member['gender'],
                    'profile_path': crew_member['profile_path'],
                }, {
                     'id': crew_member['credit_id'],
                     'tmdb_id': item['id'],
                     'person_id': crew_member['id'],
                     'role': cls.CREW_ROLES[crew_member['job']],
                     'cast_rank': None,
                })
