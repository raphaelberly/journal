
CREATE MATERIALIZED VIEW journal.persons AS (

WITH raw AS (

SELECT
  r.username,
  p.person,
  n.name,
  p.role,
  t.title,
  t.year,
  t.genres,
  r.grade,
  r.date,
  rt.rating
FROM journal.principals p
INNER JOIN journal.records r
  ON p.movie = r.movie
INNER JOIN journal.titles t
  ON p.movie = t.movie
  AND NOT (t.genres LIKE '%Animation%' AND p.role IN ('actor', 'actress'))
INNER JOIN journal.names n
  ON p.person = n.person
INNER JOIN journal.ratings rt
  ON p.movie = rt.movie

),

persons_and_roles AS (

  SELECT
    r.username,
    r.person,
    r.name,
    r.role,
    array_agg(r.title ORDER BY r.grade DESC, r.rating DESC, r.date DESC)  AS titles,
    array_agg(r.year ORDER BY r.grade DESC, r.rating DESC, r.date DESC)   AS titles_year,
    avg(r.grade)                                                          AS grade,
    avg(r.rating)                                                         AS rating,
    count(*)                                                              AS count
  FROM raw r
  GROUP BY 1,2,3,4

)

SELECT
  d.username,
  d.person AS id,
  d.role,
  d.name,
  d.titles[1:3]       AS top_3_movies,
  d.titles_year[1:3]  AS top_3_movies_year,
  d.grade,
  d.rating,
  d.count
FROM persons_and_roles d

);
