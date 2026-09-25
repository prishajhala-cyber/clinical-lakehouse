-- Silver: HL7 v2 lab results mapped to the same shape as the FHIR model.
select
    raw:message_control_id::varchar                                    as source_record_id,
    raw:patient_id::varchar                                            as patient_id,
    raw:loinc_code::varchar                                            as loinc_code,
    raw:loinc_display::varchar                                         as loinc_display,
    try_to_double(raw:value::varchar)                                  as result_value,
    nullif(raw:unit::varchar, '')                                      as result_unit,
    try_to_timestamp_ntz(raw:observed_at::varchar, 'YYYYMMDDHH24MISS') as observed_at_utc,
    -- HL7 result status codes (OBX-11) mapped to FHIR's vocabulary
    case raw:result_status::varchar
        when 'F' then 'final'
        when 'C' then 'corrected'
        when 'P' then 'preliminary'
        when 'X' then 'cancelled'
        else 'unknown'
    end                                                                as result_status,
    'hl7v2'                                                            as source_system,
    source_file,
    loaded_at
from {{ source('bronze', 'hl7_observations') }}