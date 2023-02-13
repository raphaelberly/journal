SELECT
  tmdb_id
FROM journal.records r
INNER JOIN journal.titles t
  ON r.tmdb_id = t.id
WHERE r.date >= (now() - INTERVAL '24' MONTH)::DATE
  AND r.tmdb_id NOT IN (
    SELECT tmdb_id FROM journal.records r
    WHERE r.user_id = '{user_id}'
    UNION ALL
    SELECT tmdb_id FROM journal.blacklist b
  )
GROUP BY 1
HAVING count(*) >= 3
ORDER BY count(*)*0.333 + avg(r.grade)*0.666 DESC
;
