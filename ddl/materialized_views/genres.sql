CREATE MATERIALIZED VIEW journal.genres AS (

WITH

movies_with_genre AS (

  SELECT
    unnest(string_to_array(t.genres, ',')) AS genre,
    v.movie,
    v.grade,
    r.rating,
    v.date,
    t.title
  FROM journal.records v
  INNER JOIN journal.ratings r
    ON v.movie = r.movie
  INNER JOIN journal.titles t
    ON v.movie = t.movie

),

genres AS (

  SELECT
    m.genre,
    array_agg(m.title ORDER BY m.grade DESC, m.rating DESC) AS titles,
    avg(m.grade)  AS grade,
    avg(m.rating) AS rating,
    count(*)      AS count
  FROM movies_with_genre m
  GROUP BY 1

)

SELECT
  g.genre       AS name,
  g.titles[1:3] AS top_3,
  g.grade,
  g.rating,
  g.count
FROM genres g

);
