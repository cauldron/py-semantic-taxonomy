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
        -- See discussion here:
        -- https://github.com/cauldron/py-semantic-taxonomy/issues/51
        AND tc.schemes @> :concept_scheme_dict
    UNION
    SELECT tc.*, ch.depth + 1 AS depth
    FROM relationship AS rt
    INNER JOIN concept_hierarchy AS ch
        ON ch.id_ = rt.source
    INNER JOIN concept AS tc
        ON tc.id_ = rt.target
    WHERE rt.predicate = :broader
        AND tc.schemes @> :concept_scheme_dict
)
SELECT DISTINCT * FROM concept_hierarchy;
