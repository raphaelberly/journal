CREATE MATERIALIZED VIEW journal.tops AS (

WITH
thresholds AS (
  SELECT * FROM (
    VALUES ('actor', 6), ('actress', 5), ('composer', 5), ('director', 4), ('genre', 10)
  ) t1 (role, threshold)
),
tops AS (
  SELECT p.*
  FROM journal.top_persons p
  UNION
  SELECT
    g.user_id, 'genre' AS role, g.name, g.top_3_movies, g.top_3_movies_year, g.grade, g.count, NULL AS count_principal
  FROM journal.top_genres g
),
tops_ranked AS (
  SELECT
    t.*,
    row_number() OVER (PARTITION BY t.user_id, t.role ORDER BY t.count DESC
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS rank
  FROM tops t
  ORDER BY t.role, t.count DESC
),
tops_ranked_enriched AS (
  SELECT
    r.*,
    max(r.count * (r.rank = 10)::INT) OVER (PARTITION BY r.user_id, r.role ORDER BY r.count DESC
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS value
  FROM tops_ranked r
  ORDER BY r.role, r.count DESC
)

SELECT
  t.user_id,
  t.role,
  t.name,
  t.top_3_movies,
  t.top_3_movies_year,
  t.grade,
  t.count,
  t.count_principal,
  least(value, th.threshold) AS count_threshold
FROM tops_ranked_enriched t
INNER JOIN thresholds th
USING(role)
WHERE coalesce(t.count_principal, t.count) >= least(value, th.threshold)
ORDER BY t.role, t.grade DESC

);
