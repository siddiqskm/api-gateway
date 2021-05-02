class ExecSql:
    """
    Class to store all the sql statements to be executed
    in rgate
    """
    CreateRgateTable = """CREATE TABLE IF NOT EXISTS "rgate" (
        "reqid"	INTEGER,
        "status_code"	INTEGER,
        "time_elapsed"	INTEGER,
        PRIMARY KEY("reqid" AUTOINCREMENT)
        );"""

    InsertRequestStats = """INSERT INTO rgate(status_code, time_elapsed) VALUES(?, ?);"""

    NthPercentileQuery = """WITH p AS (SELECT time_elapsed, NTILE(?) OVER (ORDER BY time_elapsed) AS percentile
        FROM rgate
        WHERE status_code = 200)
    SELECT percentile, max(time_elapsed) as lat FROM p;"""

    StatsQuery = """SELECT Count(*) AS total_queries, Count(CASE WHEN status_code = 200 THEN 1 ELSE NULL END) AS success_rate, Avg(time_elapsed) as avg_time FROM rgate;"""
