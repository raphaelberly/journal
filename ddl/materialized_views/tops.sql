CREATE MATERIALIZED VIEW journal.tops AS (

WITH
thresholds AS (
  SELECT * FROM (
    VALUES ('actor', 5), ('actress', 4), ('composer', 4), ('director', 3), ('producer', 4), ('writer', 4), ('genre', 10)
  ) t1 (role, threshold)
),
tops AS (
  SELECT p.*
  FROM journal.persons p
  UNION
  SELECT
    g.username, g.name AS id, 'genre' AS role, g.name, g.top_3_movies, g.top_3_movies_year, g.grade, g.rating, g.count
  FROM journal.genres g
),
tops_ranked AS (
  SELECT
    t.*,
    row_number() OVER (PARTITION BY t.username, t.role ORDER BY t.count DESC
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS rank
  FROM tops t
  ORDER BY t.role, t.count DESC
),
tops_ranked_enriched AS (
  SELECT
    r.*,
    max(r.count * (r.rank = 10)::INT) OVER (PARTITION BY r.username, r.role ORDER BY r.count DESC
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS value
  FROM tops_ranked r
  ORDER BY r.role, r.count DESC
)
SELECT
  t.username,
  t.id,
  t.role,
  t.name,
  t.top_3_movies,
  t.top_3_movies_year,
  t.grade,
  t.rating,
  t.count,
  least(value, th.threshold) AS count_threshold
FROM tops_ranked_enriched t
INNER JOIN thresholds th
USING(role)
WHERE t.count >= least(value, th.threshold)
ORDER BY t.role, t.grade DESC

);
