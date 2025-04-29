WITH RECURSIVE concept_hierarchy (
    id_,
    types,
    pref_labels,
    status,
    notations,
    definitions,
    change_notes,
    history_notes,
    editorial_notes,
    schemes,
    alt_labels,
    hidden_labels,
    top_concept_of,
    extra
) AS (
    SELECT tc.*, 1::INT AS depth
    FROM relationship AS rt
    INNER JOIN concept AS tc
        ON tc.id_ = rt.target
    INNER JOIN concept AS sc
        ON sc.id_ = rt.source
    WHERE sc.id_ = :source_concept
        AND rt.predicate = :broader
        -- Equivalent to
        -- AND tc.schemes @@ '$."@id" == :concept_scheme'
        -- But this won't work with parameterized query inputs
        -- so we take the long way around
        AND jsonb_path_match(
            tc.schemes,
            '$."@id" == $var',
            jsonb_build_object('var', :concept_scheme :: text)
        )
        -- TBD: Profile if new approach is actually faster
        -- AND EXISTS (
        --     SELECT *
        --     FROM jsonb_array_elements(tc.schemes) AS elements
        --     WHERE elements.value ->> '@id' = :concept_scheme
        -- )
    UNION
    SELECT tc.*, ch.depth + 1 AS depth
    FROM relationship AS rt
    INNER JOIN concept_hierarchy AS ch
        ON ch.id_ = rt.source
    INNER JOIN concept AS tc
        ON tc.id_ = rt.target
    WHERE rt.predicate = :broader
        AND jsonb_path_match(
            tc.schemes,
            '$."@id" == $var',
            jsonb_build_object('var', :concept_scheme :: text)
        )
)
SELECT DISTINCT * FROM concept_hierarchy;
