-- Silver: combine both lab sources and remove cross-system duplicates.
-- The same result can arrive from the EHR (FHIR) and the lab system (HL7 v2).
-- Rule: keep every FHIR record (FHIR IDs already identify distinct results).
--       Keep an HL7 record only if no FHIR record shares its business key
--       (patient + LOINC test + observation time).
-- Why not dedup on the business key alone: FHIR contains distinct results that
-- share a timestamp (e.g., two lipid panels), and merging them would lose data.

{% set columns %}
    source_record_id, patient_id, loinc_code, loinc_display, result_value,
    result_unit, observed_at_utc, result_status, source_system, source_file, loaded_at
{% endset %}

with unioned as (

    select {{ columns }} from {{ ref('stg_fhir__observations') }}
    union all
    select {{ columns }} from {{ ref('stg_hl7__observations') }}

),

flagged as (

    select
        {{ columns }},
        max(iff(source_system = 'fhir_r4', 1, 0))
            over (partition by patient_id, loinc_code, observed_at_utc) as has_fhir_record,
        max(iff(source_system = 'hl7v2', 1, 0))
            over (partition by patient_id, loinc_code, observed_at_utc) as has_hl7_record
    from unioned

)

select
    {{ dbt_utils.generate_surrogate_key(['source_system', 'source_record_id']) }} as lab_result_id,
    {{ columns }},
    has_fhir_record + has_hl7_record as source_count
from flagged
where source_system = 'fhir_r4'
   or has_fhir_record = 0