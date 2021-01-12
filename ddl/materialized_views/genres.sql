
CREATE MATERIALIZED VIEW journal.top_genres AS (

WITH

movies_with_genre AS (

  SELECT
    r.user_id,
    unnest(t.genres) AS genre,
    r.tmdb_id,
    r.grade,
    r.date,
    CASE WHEN t.original_language = u.language THEN t.original_title ELSE t.title END AS title,
    date_part('year', t.release_date)::INT AS year
  FROM journal.records r
  INNER JOIN journal.titles t
    ON r.tmdb_id = t.id
  INNER JOIN journal.users u
    ON r.user_id = u.id

),

genres AS (

  SELECT
    m.user_id,
    m.genre,
    array_agg(m.title ORDER BY m.grade DESC, m.date DESC)   AS title_names,
    array_agg(m.year ORDER BY m.grade DESC, m.date DESC)    AS title_years,
    array_agg(m.tmdb_id ORDER BY m.grade DESC, m.date DESC) AS title_ids,
    avg(m.grade)  AS grade,
    count(*)      AS count
  FROM movies_with_genre m
  GROUP BY 1,2

)

SELECT
  g.user_id,
  g.genre             AS name,
  g.title_names[1:3]  AS top_3_movie_names,
  g.title_years[1:3]  AS top_3_movie_years,
  g.title_ids[1:3]    AS top_3_movie_ids,
  g.grade,
  g.count
FROM genres g

);
