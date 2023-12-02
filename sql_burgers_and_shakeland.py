import sqlite3

# Just exploring data, so not going to be committing anything in this file.

conn = sqlite3.connect("burgers_and_shakeland.db") 
cursor = conn.cursor()

cursor.execute("""PRAGMA table_info(Sales);
               """)
cursor.fetchall()

# question 1 (getting basic metrics of how busy each location is)
cursor.execute("""SELECT Location, COUNT(*) FROM Sales GROUP BY Location""")
cursor.fetchall()

# question 1 (evaluating by times in the day)
cursor.execute("""SELECT strftime('%H:%M:%S', datetime), Location, COUNT(*) 
               FROM Sales 
               GROUP BY Location, strftime('%H:%M:%S', datetime)""")
cursor.fetchall()

cursor.execute("""
               WITH ss AS (
                SELECT strftime('%H:%M:%S', datetime) AS Time, COUNT(*) AS SalesCount_SS
                FROM Sales 
                WHERE Location = "State Street"
                GROUP BY strftime('%H:%M:%S', datetime)
               ), uh AS (
                SELECT strftime('%H:%M:%S', datetime) AS Time, COUNT(*) AS SalesCount_UH
                FROM Sales 
                WHERE Location = "Union Heights"
                GROUP BY strftime('%H:%M:%S', datetime)
               ) SELECT Time, SalesCount_SS - SalesCount_UH FROM ss LEFT JOIN uh USING(time)""")
cursor.fetchall()

# question 2 (employee month comparison)

cursor.execute("""
               WITH march_sales AS (
                SELECT transaction_employeeid, strftime('%m', datetime) AS month, SUM(price) AS total_sales_amount_m
                FROM Sales 
                WHERE strftime('%m', datetime) = '03'
                GROUP BY strftime('%m', datetime), transaction_employeeid
               ), april_sales AS (
                SELECT employee_name, transaction_employeeid, strftime('%m', datetime) AS month, SUM(price) AS total_sales_amount_a
                FROM Sales 
                WHERE strftime('%m', datetime) = '04'
                GROUP BY strftime('%m', datetime), transaction_employeeid
               ) 
               SELECT transaction_employeeid, employee_name, total_sales_amount_a/total_sales_amount_m 
               FROM april_sales as
               LEFT JOIN march_sales ms USING(transaction_employeeid)
               ORDER BY total_sales_amount_a/total_sales_amount_m  DESC""")
cursor.fetchall()

# question 3 (combo meals)

cursor.execute("""
               -- icsu = item_counts_set_up
               WITH icsu AS (
                SELECT transaction_employeeid,
                datetime,
                CASE WHEN itemid = 1 THEN 1 ELSE 0 END AS item1,
                CASE WHEN itemid = 2 THEN 1 ELSE 0 END AS item2,
                CASE WHEN itemid = 3 THEN 1 WHEN itemid = 4 THEN 1 ELSE 0 END AS item3_or_4
                FROM Sales
                WHERE Location = 'State Street'
                AND strftime('%m', datetime) = '04'
               ),
               -- ic = item_counts
               ic AS (
               SELECT transaction_employeeid,
                datetime,
                SUM(item1) AS item1_count,
                SUM(item2) AS item2_count,
                SUM(item3_or_4) AS item3_or_4_count
               FROM icsu
               GROUP BY transaction_employeeid, datetime
               ),
               possible_combo_meals AS (
               SELECT transaction_employeeid,
                datetime,
                Case When item1_count <= item2_count And item1_count <= item3_or_4_count Then item1_count
                 When item2_count <= item1_count And item2_count <= item3_or_4_count Then item2_count 
                 Else item3_or_4_count
                 END AS possible_combo_meals
               FROM ic
               )
               SELECT SUM(possible_combo_meals)
               FROM possible_combo_meals
               """ 
                )
               
cursor.fetchall()

# 431
cursor.execute("""SELECT *, MONTH(datetime)
               FROM Sales""")
cursor.fetchall()



cursor.execute("""
               WITH drinks_combined_state_street AS (SELECT transaction_employeeid,
                datetime,
                CASE WHEN itemid = 4 THEN 3 else itemid END AS itemid
                FROM Sales
                WHERE location = 'State Street'
                AND strftime('%m', datetime) = '04'
               ),
               item_counts AS (
                SELECT transaction_employeeid,
                datetime,
                itemid,
                count() AS item_count
                FROM drinks_combined_state_street
                GROUP BY transaction_employeeid, datetime, itemid
               ),
               possible_combo_meals AS (
                SELECT MIN(ic0.item_count) AS possible_combo_meals
                FROM item_counts ic0
                INNER JOIN item_counts ic1 ON ic0.transaction_employeeid = ic1.transaction_employeeid
                        AND ic0.datetime = ic1.datetime
                INNER JOIN item_counts ic2 ON ic0.transaction_employeeid = ic2.transaction_employeeid
                        AND ic0.datetime = ic2.datetime
                INNER JOIN item_counts ic3 ON ic0.transaction_employeeid = ic3.transaction_employeeid
                        AND ic0.datetime = ic3.datetime
                WHERE ic1.itemid = 1
                AND ic2.itemid = 2
                AND ic3.itemid = 3
                GROUP BY ic0.transaction_employeeid, ic0.datetime
               )
               SELECT SUM(possible_combo_meals)
               FROM possible_combo_meals  
               
               """ 
                )
cursor.fetchall()

# 99

# bonus question

cursor.execute("""
               WITH datetime_as_datetime AS (
                SELECT transaction_employeeid,
                JulianDay(datetime) AS datetime_dt,
                date(datetime) AS date
                FROM Sales
               ), time_between_transactions AS (
                SELECT transaction_employeeid, datetime_dt, date, CAST((
                            JulianDay(datetime_dt) - JulianDay(LAG(datetime_dt) OVER (
                        PARTITION BY transaction_employeeid, date
                        ORDER BY datetime_dt
                        ))
                        ) * 24 * 60 AS Integer) AS time_between_transactions
                FROM datetime_as_datetime
               ), possible_shifts AS (
                SELECT CAST((MAX(datetime_dt) - MIN(datetime_dt)) * 24 AS Integer) AS possible_shift,
                    MIN(datetime_dt) AS shift_start,
                    MAX(datetime_dt) AS shift_end,
                    MAX(time_between_transactions) AS longest_possible_break_in_possible_shift,
                    transaction_employeeid
                FROM time_between_transactions
               
                GROUP BY transaction_employeeid, date
               )
                SELECT ps.transaction_employeeid,
                 ps.possible_shift, 
                 ps.longest_possible_break_in_possible_shift,  
                 s.datetime, 
                 s2.datetime
                FROM possible_shifts ps
                LEFT JOIN Sales s
                    ON JulianDay(s.datetime) = ps.shift_start
                    AND s.transaction_employeeid = ps.transaction_employeeid
                LEFT JOIN Sales s2
                    ON JulianDay(s2.datetime) = ps.shift_end
                    AND s2.transaction_employeeid = ps.transaction_employeeid
                WHERE possible_shift > 8
                ORDER BY possible_shift, longest_possible_break_in_possible_shift
               """ 
                )
cursor.fetchall()

cursor.execute("""
               WITH datetime_as_datetime AS (
                SELECT transaction_employeeid,
                JulianDay(datetime) AS datetime_dt,
                date(datetime) AS date
                FROM Sales
               ), time_between_transactions AS (
                SELECT transaction_employeeid, datetime_dt, date, CAST((
                            JulianDay(datetime_dt) - JulianDay(LAG(datetime_dt) OVER (
                        PARTITION BY transaction_employeeid, date
                        ORDER BY datetime_dt
                        ))
                        ) * 24 * 60 AS Integer) AS time_between_transactions
                FROM datetime_as_datetime
               ), possible_shifts AS (
                SELECT CAST((MAX(datetime_dt) - MIN(datetime_dt)) * 24 AS Integer) AS possible_shift,
                    MIN(datetime_dt) AS shift_start,
                    MAX(datetime_dt) AS shift_end,
                    MAX(time_between_transactions) AS longest_possible_break_in_possible_shift,
                    transaction_employeeid
                FROM time_between_transactions
               
                GROUP BY transaction_employeeid, date
               )
                SELECT COUNT()
                FROM possible_shifts ps
                LEFT JOIN Sales s
                    ON JulianDay(s.datetime) = ps.shift_start
                    AND s.transaction_employeeid = ps.transaction_employeeid
                LEFT JOIN Sales s2
                    ON JulianDay(s2.datetime) = ps.shift_end
                    AND s2.transaction_employeeid = ps.transaction_employeeid
                WHERE possible_shift > 8
               """ 
                )
cursor.fetchall()


cursor.execute("""
               WITH datetime_as_datetime AS (
                SELECT transaction_employeeid,
                JulianDay(datetime) AS datetime_dt,
                date(datetime) AS date
                FROM Sales
               ), time_between_transactions AS (
                SELECT transaction_employeeid, datetime_dt, date, CAST((
                            JulianDay(datetime_dt) - JulianDay(LAG(datetime_dt) OVER (
                        PARTITION BY transaction_employeeid, date
                        ORDER BY datetime_dt
                        ))
                        ) * 24 * 60 AS Integer) AS time_between_transactions
                FROM datetime_as_datetime
               ), possible_shifts AS (
                SELECT CAST((MAX(datetime_dt) - MIN(datetime_dt)) * 24 AS Integer) AS possible_shift,
                    MIN(datetime_dt) AS shift_start,
                    MAX(datetime_dt) AS shift_end,
                    MAX(time_between_transactions) AS longest_possible_break_in_possible_shift,
                    transaction_employeeid
                FROM time_between_transactions
               
                GROUP BY transaction_employeeid, date
               )
                SELECT COUNT()
                FROM possible_shifts ps
                LEFT JOIN Sales s
                    ON JulianDay(s.datetime) = ps.shift_start
                    AND s.transaction_employeeid = ps.transaction_employeeid
                LEFT JOIN Sales s2
                    ON JulianDay(s2.datetime) = ps.shift_end
                    AND s2.transaction_employeeid = ps.transaction_employeeid
                WHERE possible_shift <= 8
               """ 
                )
cursor.fetchall()


# highest 239 minute break possibility
