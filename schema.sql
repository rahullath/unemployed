-- Azure SQL schema for the job board, counted. Load out/clean_listings.csv into stg_listing
-- (Azure Data Studio import wizard), then run the inserts below.

CREATE TABLE stg_listing (
  listing_id      INT IDENTITY PRIMARY KEY,
  date_found      DATE,
  source          NVARCHAR(40),
  title_family    NVARCHAR(30),
  location_band   NVARCHAR(20),          -- central / nearby / far / remote / unknown
  contract        NVARCHAR(20),          -- permanent / fixed-term / temp / part-time / unknown
  pay_annual      DECIMAL(10,0) NULL,
  posted_date     DATE NULL,
  closes_date     DATE NULL,
  has_closing     BIT,                   -- notes mention a closing date, even if it would not parse
  vet_state       NVARCHAR(12),          -- passed / failed / unread
  vet_fail_reason NVARCHAR(40) NULL,
  status          NVARCHAR(20),
  date_applied    DATE NULL
);

CREATE TABLE dim_source (
  source               NVARCHAR(40) PRIMARY KEY,
  readable_by_routine  NVARCHAR(3) NOT NULL    -- yes / no
);

INSERT INTO dim_source VALUES
  ('reed','yes'),('adzuna','yes'),('indeed','yes'),('linkedin','no'),('nhs','yes'),
  ('charityjob','yes'),('civil service','no'),('wmjobs','no'),('portals','no');

-- dim_date is Power BI's CALENDAR(DATE(2026,9,1), DATE(2026,12,31)); no table needed here.

CREATE TABLE fact_listing (
  listing_id INT PRIMARY KEY,
  source NVARCHAR(40) REFERENCES dim_source(source),
  date_found DATE, title_family NVARCHAR(30), location_band NVARCHAR(20), contract NVARCHAR(20),
  pay_annual DECIMAL(10,0) NULL, posted_date DATE NULL, closes_date DATE NULL, has_closing BIT,
  vet_state NVARCHAR(12), vet_fail_reason NVARCHAR(40) NULL, status NVARCHAR(20), date_applied DATE NULL
);

INSERT INTO fact_listing
SELECT listing_id, source, date_found, title_family, location_band, contract, pay_annual,
       posted_date, closes_date, has_closing, vet_state, vet_fail_reason, status, date_applied
FROM stg_listing;

-- Summaries behind the counted page (should match summaries/*.csv)
SELECT status, COUNT(*) AS n FROM fact_listing GROUP BY status;
SELECT s.source, s.readable_by_routine, COUNT(*) AS listings,
       SUM(CASE WHEN f.vet_state <> 'unread' THEN 1 ELSE 0 END) AS [read],
       SUM(CAST(f.has_closing AS INT)) AS has_closing_date
FROM fact_listing f JOIN dim_source s ON s.source = f.source
GROUP BY s.source, s.readable_by_routine ORDER BY listings DESC;
