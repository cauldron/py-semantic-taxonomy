from py_semantic_taxonomy.domain.entities import SearchResult

WITH_HIGHLIGHTS = {
    "facet_counts": [],
    "found": 1,
    "hits": [
        {
            "document": {
                "all_languages_pref_labels": [
                    "0101 Pferde, Esel, Maultiere und Maulesel, lebend",
                    "0101 Caballos, asnos, mulos y burdéganos, vivos",
                ],
                "alt_labels": [],
                "definition": "",
                "hidden_labels": [],
                "id": "http%3A//data.europa.eu/xsp/cn2023/010100000080",
                "notation": "0101",
                "pref_label": "0101 Pferde, Esel, Maultiere und Maulesel, lebend",
            },
            "highlight": {
                "all_languages_pref_labels": [
                    {
                        "matched_tokens": ["Ese"],
                        "snippet": "0101 "
                        "Pferde, "
                        "<mark>Ese</mark>l, "
                        "Maultiere "
                        "und "
                        "Maulesel, "
                        "lebend",
                    },
                    {
                        "matched_tokens": [],
                        "snippet": "0101 Caballos, asnos, mulos y burdéganos, vivos",
                    },
                ],
                "pref_label": {
                    "matched_tokens": ["Ese"],
                    "snippet": "0101 Pferde, "
                    "<mark>Ese</mark>l, "
                    "Maultiere und Maulesel, "
                    "lebend",
                },
            },
            "highlights": [
                {
                    "field": "pref_label",
                    "matched_tokens": ["Ese"],
                    "snippet": "0101 Pferde, <mark>Ese</mark>l, Maultiere und Maulesel, lebend",
                },
                {
                    "field": "all_languages_pref_labels",
                    "indices": [0],
                    "matched_tokens": [["Ese"]],
                    "snippets": ["0101 Pferde, <mark>Ese</mark>l, Maultiere und Maulesel, lebend"],
                },
            ],
            "text_match": 578730089005449338,
            "text_match_info": {
                "best_field_score": "1108074561536",
                "best_field_weight": 15,
                "fields_matched": 2,
                "num_tokens_dropped": 0,
                "score": "578730089005449338",
                "tokens_matched": 1,
                "typo_prefix_score": 1,
            },
        }
    ],
    "out_of": 2,
    "page": 1,
    "request_params": {
        "collection_name": "pyst-concepts-de",
        "first_q": "Ese",
        "per_page": 50,
        "q": "Ese",
    },
    "search_cutoff": False,
    "search_time_ms": 0,
}
WITHOUT_HIGHLIGHTS = {
    "facet_counts": [],
    "found": 2,
    "hits": [
        {
            "document": {
                "all_languages_pref_labels": [
                    "0101 Pferde, Esel, Maultiere und Maulesel, lebend",
                    "0101 Caballos, asnos, mulos y burdéganos, vivos",
                ],
                "alt_labels": [],
                "definition": "",
                "hidden_labels": [],
                "id": "http%3A//data.europa.eu/xsp/cn2023/010100000080",
                "notation": "0101",
                "pref_label": "0101 Pferde, Esel, Maultiere und Maulesel, lebend",
            },
            "highlight": {},
            "highlights": [],
            "hybrid_search_info": {"rank_fusion_score": 0.30000001192092896},
            "text_match": 0,
            "text_match_info": {
                "best_field_score": "0",
                "best_field_weight": 0,
                "fields_matched": 0,
                "num_tokens_dropped": 1,
                "score": "0",
                "tokens_matched": 0,
                "typo_prefix_score": 255,
            },
            "vector_distance": 0.815794050693512,
        },
        {
            "document": {
                "all_languages_pref_labels": [
                    "ABSCHNITT I - LEBENDE TIERE UND WAREN TIERISCHEN URSPRUNGS",
                    "SECCIÓN I - ANIMALES VIVOS Y PRODUCTOS DEL REINO ANIMAL",
                ],
                "alt_labels": [],
                "definition": "",
                "hidden_labels": [],
                "id": "http%3A//data.europa.eu/xsp/cn2023/010011000090",
                "notation": "I",
                "pref_label": "ABSCHNITT I - LEBENDE TIERE UND WAREN TIERISCHEN URSPRUNGS",
            },
            "highlight": {},
            "highlights": [],
            "hybrid_search_info": {"rank_fusion_score": 0.15000000596046448},
            "text_match": 0,
            "text_match_info": {
                "best_field_score": "0",
                "best_field_weight": 0,
                "fields_matched": 0,
                "num_tokens_dropped": 1,
                "score": "0",
                "tokens_matched": 0,
                "typo_prefix_score": 255,
            },
            "vector_distance": 0.9725939631462097,
        },
    ],
    "out_of": 2,
    "page": 1,
    "request_params": {
        "collection_name": "pyst-concepts-de",
        "first_q": "Zaum",
        "per_page": 50,
        "q": "Zaum",
    },
    "search_cutoff": False,
    "search_time_ms": 8,
}


def test_from_results_with_highlight():
    expected = [
        SearchResult(
            id_="http://data.europa.eu/xsp/cn2023/010100000080",
            label="0101 Pferde, Esel, Maultiere und Maulesel, lebend",
            highlight="0101 Pferde, <mark>Ese</mark>l, Maultiere und Maulesel, lebend",
        ),
    ]
    assert SearchResult.from_typesense_results(WITH_HIGHLIGHTS) == expected


def test_from_results_without_highlight():
    expected = [
        SearchResult(
            id_="http://data.europa.eu/xsp/cn2023/010100000080",
            label="0101 Pferde, Esel, Maultiere und Maulesel, lebend",
            highlight=None,
        ),
        SearchResult(
            id_="http://data.europa.eu/xsp/cn2023/010011000090",
            label="ABSCHNITT I - LEBENDE TIERE UND WAREN TIERISCHEN URSPRUNGS",
            highlight=None,
        ),
    ]
    assert SearchResult.from_typesense_results(WITHOUT_HIGHLIGHTS) == expected


def test_search_result_to_json_with_highlight():
    expected = {
        "id_": "http://data.europa.eu/xsp/cn2023/010100000080",
        "label": "0101 Pferde, Esel, Maultiere und Maulesel, lebend",
        "highlight": "0101 Pferde, <mark>Ese</mark>l, Maultiere und Maulesel, lebend",
    }
    SearchResult.from_typesense_results(WITH_HIGHLIGHTS)[0].to_json() == expected


def test_search_result_to_json_without_highlight():
    expected = {
        "id_": "http://data.europa.eu/xsp/cn2023/010100000080",
        "label": "0101 Pferde, Esel, Maultiere und Maulesel, lebend",
        "highlight": None,
    }
    SearchResult.from_typesense_results(WITHOUT_HIGHLIGHTS)[0].to_json() == expected
