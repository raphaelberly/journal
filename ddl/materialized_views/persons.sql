
CREATE MATERIALIZED VIEW journal.top_persons AS (

WITH credits_enriched AS (

  SELECT
    c.*,
    t.title,
    date_part('year', t.release_date)::INT AS year,
    CASE
      WHEN c.role NOT IN ('actress', 'actor') THEN NULL
      WHEN 'Animation' = ANY(t.genres) THEN FALSE
      WHEN c.cast_rank <= 5 THEN TRUE
      WHEN ntile(10) OVER (PARTITION BY c.tmdb_id ORDER BY c.cast_rank) = 1 AND c.cast_rank <= 12 THEN TRUE
    ELSE FALSE END AS principal
  FROM journal.credits c
  INNER JOIN journal.titles t
    ON c.tmdb_id = t.id

),

persons_and_roles AS (

  SELECT
    r.user_id,
    c.role,
    c.person_id,
    p.name,
    array_agg(c.title ORDER BY r.grade DESC, r.date DESC)                       AS titles,
    array_agg(c.year ORDER BY r.grade DESC, r.date DESC)                        AS titles_year,
    max(r.date)                                                                 AS last_added,
    count(*)                                                                    AS count,
    sum(CASE WHEN c.principal THEN 1 ELSE 0 END)                                AS count_principal,
    sum(CASE WHEN coalesce(c.principal, TRUE) THEN 1 ELSE 0.5 END * r.grade)
      / sum(CASE WHEN coalesce(c.principal, TRUE) THEN 1 ELSE 0.5 END)          AS grade
  FROM journal.records r
  INNER JOIN credits_enriched c
    ON r.tmdb_id = c.tmdb_id
  INNER JOIN journal.persons p
    ON c.person_id = p.id
  GROUP BY 1,2,3,4

)

SELECT
  d.user_id,
  d.role,
  d.name,
  d.titles[1:3]       AS top_3_movies,
  d.titles_year[1:3]  AS top_3_movies_year,
  d.grade,
  d.count,
  d.count_principal
FROM persons_and_roles d

);
