
CREATE MATERIALIZED VIEW journal.genres AS (

WITH

movies_with_genre AS (

  SELECT
    r.user_id,
    unnest(t.genres) AS genre,
    r.tmdb_id,
    r.grade,
    r.date,
    t.title,
    date_part('year', t.release_date)::INT AS year
  FROM journal.records r
  INNER JOIN journal.titles t
    ON r.tmdb_id = t.id

),

genres AS (

  SELECT
    m.user_id,
    m.genre,
    array_agg(m.title ORDER BY m.grade DESC, m.date DESC) AS titles,
    array_agg(m.year ORDER BY m.grade DESC, m.date DESC) AS titles_year,
    avg(m.grade)  AS grade,
    count(*)      AS count
  FROM movies_with_genre m
  GROUP BY 1,2

)

SELECT
  g.user_id,
  g.genre             AS name,
  g.titles[1:3]       AS top_3_movies,
  g.titles_year[1:3]  AS top_3_movies_year,
  g.grade,
  g.count
FROM genres g

);
