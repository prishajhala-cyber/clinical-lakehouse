-- Silver: flatten FHIR Patient JSON into typed columns, one row per patient.
select
    raw:id::varchar                       as patient_id,
    raw:name[0]:given[0]::varchar         as given_name,
    raw:name[0]:family::varchar           as family_name,
    raw:gender::varchar                   as gender,
    raw:birthDate::date                   as birth_date,
    raw:deceasedDateTime::timestamp_tz    as deceased_at,
    raw:address[0]:city::varchar          as city,
    raw:address[0]:state::varchar         as state,
    source_file,
    loaded_at
from {{ source('bronze', 'fhir_patients') }}
-- If the same patient was ever loaded more than once, keep the latest load
qualify row_number() over (partition by raw:id::varchar order by loaded_at desc) = 1