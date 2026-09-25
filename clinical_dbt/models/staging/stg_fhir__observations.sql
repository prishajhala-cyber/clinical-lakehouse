-- Silver: FHIR lab results mapped to the shared lab-result shape.
select
    raw:id::varchar                                                             as source_record_id,
    regexp_replace(raw:subject:reference::varchar, '^(Patient/|urn:uuid:)', '') as patient_id,
    raw:code:coding[0]:code::varchar                                            as loinc_code,
    raw:code:coding[0]:display::varchar                                         as loinc_display,
    raw:valueQuantity:value::float                                              as result_value,
    raw:valueQuantity:unit::varchar                                             as result_unit,
    convert_timezone('UTC', raw:effectiveDateTime::timestamp_tz)::timestamp_ntz as observed_at_utc,
    raw:status::varchar                                                         as result_status,
    'fhir_r4'                                                                   as source_system,
    source_file,
    loaded_at
from {{ source('bronze', 'fhir_observations') }}
where raw:category[0]:coding[0]:code::varchar = 'laboratory'
  and raw:valueQuantity is not null