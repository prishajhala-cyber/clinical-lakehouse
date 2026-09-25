"""Load raw files from the landing stage into Bronze tables with COPY INTO.

COPY INTO remembers which files it has already loaded, so re-running this
script skips old files and never duplicates rows (idempotent).
"""
from sf import connect

# Bronze table -> stage folder it loads from
TABLES = {
    "fhir_patients": "fhir/Patient/",
    "fhir_observations": "fhir/Observation/",
    "hl7_observations": "hl7_parsed/",
}

def load_table(table):
    """COPY new files from this table's stage folder into the Bronze table."""
    sql = f"""
        copy into {table} (raw, source_file, loaded_at)
        from (
            select
                $1,
                metadata$filename,
                metadata$start_scan_time::timestamp_ntz
            from @landing/{TABLES[table]}
        )
        file_format = (format_name = 'json_fmt')
        on_error = 'continue'
    """
    conn = connect()
    try:
        results = conn.cursor().execute(sql).fetchall()
    finally:
        conn.close()

    # When there's nothing new, Snowflake returns one message row instead of file rows
    files = [row for row in results if len(row) > 1]
    rows_loaded = sum(row[3] for row in files)
    errors = sum(row[5] for row in files)
    print(f"  {table}: {len(files)} new file(s), {rows_loaded} row(s) loaded, {errors} error(s)")

    for row in files:
        if row[5]:
            print(f"    first error in {row[0]}: {row[6]}")

def main():
    print("Loading Bronze tables:")
    for table in TABLES:
        load_table(table)


if __name__ == "__main__":
    main()