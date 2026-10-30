-- Directors whose first movie the user watched within each period. A movie added as watched long ago
-- (include_in_recent false) has no real watch date: its directors count as known from the start
WITH first_seen AS (
  SELECT
    c.person_id,
    min(CASE WHEN r.include_in_recent THEN r.date ELSE '-infinity'::DATE END) AS date
  FROM journal.records r
  INNER JOIN journal.credits c
    ON r.tmdb_id = c.tmdb_id
    AND c.role = 'director'
  WHERE r.user_id = {user_id}
  GROUP BY 1
)
SELECT
  date_part('year', f.date)::INT AS year,
  count(*) AS count
FROM first_seen f
WHERE date_part('year', f.date) IN ({previous_year}, {year})
GROUP BY 1
;
