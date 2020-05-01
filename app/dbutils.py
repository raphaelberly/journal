from datetime import datetime
from typing import List, Optional

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.declarative import DeclarativeMeta

from app import db
from app.models import Title, Person, Credit
from lib.tmdb import TitleConverter, CrewConverter


def _upsert(table_model: DeclarativeMeta, records: List[dict], exclude: Optional[List[str]] = None):
    # Get list of primary keys
    primary_keys = [key.name for key in inspect(table_model).primary_key]
    # Assemble upsert statement
    statement = insert(table_model).values([{**record, 'update_datetime_utc': datetime.utcnow()} for record in records])
    cols_to_update = {col.name: col for col in statement.excluded if (not col.primary_key and col.name not in exclude)}
    upsert_statement = statement.on_conflict_do_update(index_elements=primary_keys, set_=cols_to_update)
    # Execute statement
    db.session.execute(upsert_statement)


def upsert(table_model: DeclarativeMeta, record: dict, exclude: Optional[List[str]] = None):
    return _upsert(table_model, [record], exclude)


def upsert_bulk(table_model: DeclarativeMeta, records: List[dict], exclude: Optional[List[str]] = None):
    return _upsert(table_model, records, exclude)


def upsert_title_metadata(item):
    # Parse title metadata and upsert to database
    title = TitleConverter.json_to_table(item)
    upsert(Title, title, ['insert_datetime_utc'])
    # Parse credits and persons metadata and upsert to database
    persons, credits = [], []
    for person, credit in CrewConverter.crew_generator(item):
        persons.append(person)
        credits.append(credit)
    upsert_bulk(Person, persons, ['insert_datetime_utc'])
    upsert_bulk(Credit, credits, ['insert_datetime_utc'])
    # Commit changes
    db.session.commit()
