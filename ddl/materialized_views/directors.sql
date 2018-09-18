CREATE MATERIALIZED VIEW journal.directors AS (

WITH

movies AS (

  SELECT
    v.movie,
    v.grade,
    r.rating,
    v.date,
    t.title,
    unnest(string_to_array(c.directors, ',')) AS director
  FROM journal.crew c
  INNER JOIN journal.records v
    ON c.movie = v.movie
  INNER JOIN journal.ratings r
    ON c.movie = r.movie
  INNER JOIN journal.titles t
    ON c.movie = t.movie

),

movies_with_director_name AS (

  SELECT
    m.*,
    n.name
  FROM movies m
  INNER JOIN journal.names n
    ON m.director = n.person

),

directors AS (

  SELECT
    m.director,
    m.name,
    array_agg(m.title ORDER BY m.grade DESC, m.rating DESC) AS titles,
    avg(m.grade)  AS grade,
    avg(m.rating) AS rating,
    count(*)      AS count
  FROM movies_with_director_name m
  GROUP BY 1,2

)

SELECT
  d.director AS id,
  d.name,
  d.titles[1:3] AS top_3,
  d.grade,
  d.rating,
  d.count
FROM directors d

);
