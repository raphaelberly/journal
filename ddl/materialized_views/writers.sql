CREATE MATERIALIZED VIEW journal.writers AS (

WITH

movies AS (

  SELECT
    v.movie,
    v.grade,
    r.rating,
    v.date,
    t.title,
    unnest(string_to_array(c.writers, ',')) AS writer
  FROM journal.crew c
  INNER JOIN journal.views v
    ON c.movie = v.movie
  INNER JOIN journal.ratings r
    ON c.movie = r.movie
  INNER JOIN journal.titles t
    ON c.movie = t.movie

),

movies_with_writer_name AS (

  SELECT
    m.*,
    n.name
  FROM movies m
  INNER JOIN journal.names n
    ON m.writer = n.person

),

writers AS (

  SELECT
    m.writer,
    m.name,
    array_agg(m.title ORDER BY m.grade DESC, m.rating DESC) AS titles,
    avg(m.grade)  AS grade,
    avg(m.rating) AS rating,
    count(*)      AS count
  FROM movies_with_writer_name m
  GROUP BY 1,2

)

SELECT
  d.name,
  d.titles[1:3] AS top_3,
  d.grade,
  d.rating,
  d.count
FROM writers d

);
