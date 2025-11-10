
CREATE MATERIALIZED VIEW journal.top_persons AS (

WITH credits AS (

  SELECT
    c.person_id,
    c.tmdb_id,
    c.role,
    c.cast_rank,
    row_number() OVER (PARTITION BY c.person_id, c.tmdb_id, c.role ORDER BY update_datetime_utc DESC) AS row_nb
  FROM journal.credits c

),

credits_enriched AS (

  SELECT
    c.*,
    t.id,
    t.title,
    t.original_title,
    t.original_language,
    date_part('year', t.release_date)::INT AS year,
    CASE
      WHEN c.role NOT IN ('actress', 'actor') THEN NULL
      WHEN 'Animation' = ANY(t.genres) THEN FALSE
      WHEN c.cast_rank <= 5 THEN TRUE
      WHEN ntile(10) OVER (PARTITION BY c.tmdb_id ORDER BY c.cast_rank) = 1 AND c.cast_rank <= 12 THEN TRUE
    ELSE FALSE END AS principal
  FROM (
    SELECT * FROM credits WHERE row_nb = 1
  ) c
  INNER JOIN journal.titles t
    ON c.tmdb_id = t.id

),

persons_and_roles AS (

  SELECT
    r.user_id,
    c.role,
    c.person_id,
    p.name,
    array_agg(
      CASE WHEN u.language = 'fr' AND t.original_language = 'fr' THEN t.original_title ELSE t.title END
      ORDER BY r.grade DESC, r.date DESC
    )                                                                                   AS title_names,
    array_agg(c.year ORDER BY r.grade DESC, r.date DESC)                                AS title_years,
    array_agg(t.id ORDER BY r.grade DESC, r.date DESC)                                  AS title_ids,
    max(r.date)                                                                         AS last_added,
    count(*)                                                                            AS count,
    sum(c.principal::INTEGER)                                                           AS count_principal,
    sum(CASE WHEN coalesce(c.principal, TRUE) THEN 1 ELSE 0.5 END * r.grade)
      / sum(CASE WHEN coalesce(c.principal, TRUE) THEN 1 ELSE 0.5 END)                  AS grade
  FROM journal.records r
  INNER JOIN journal.titles t
    ON r.tmdb_id = t.id
  INNER JOIN journal.users u
    ON r.user_id = u.id
  INNER JOIN credits_enriched c
    ON r.tmdb_id = c.tmdb_id
  INNER JOIN journal.persons p
    ON c.person_id = p.id
  WHERE r.include_in_top_persons IS TRUE
  GROUP BY 1,2,3,4

)

SELECT
  d.user_id,
  d.role,
  d.person_id,
  d.name,
  d.title_names[1:3]    AS top_3_movie_names,
  d.title_years[1:3]    AS top_3_movie_years,
  d.title_ids[1:3]      AS top_3_movie_ids,
  d.grade,
  d.count,
  d.count_principal
FROM persons_and_roles d

);
