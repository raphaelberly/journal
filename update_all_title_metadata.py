from time import sleep

from tqdm import tqdm

from app import db
from app.dbutils import upsert_title_metadata
from app.models import Title
from lib.tmdb import Tmdb


# Initialize Tmdb instance
tmdb = Tmdb()

# Load all titles present in the db
title_ids = [title_id for title_id, in db.session.query(Title.id).all()]

# Update all titles one after the other
errors = []
for title_id in tqdm(title_ids):
    title = tmdb.get(title_id)
    try:
        upsert_title_metadata(item=title)
    except Exception:
        errors.append(errors)
    sleep(0.2)

# Commit changes if everything went well
db.session.commit()

# Log errors if any
if errors:
    print(f'Could not update titles: {errors}')
