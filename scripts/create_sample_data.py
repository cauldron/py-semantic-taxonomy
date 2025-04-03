#!/usr/bin/env python3
from datetime import datetime
from typing import List

import pyst_client
from pyst_client.models import (
    ConceptCreate,
    ConceptSchemeInput,
    DateTime,
    DateTimeType,
    MultilingualString,
    Node,
    Status,
    VersionString,
)

# Configuration
API_URL = "http://localhost:8000"
API_TOKEN = "missing"
LANGUAGES = ["en", "de", "es", "da", "fr", "pt", "it"]

def create_multilingual_string(text_base: str, index: int) -> List[MultilingualString]:
    """Create multilingual strings for each supported language."""
    translations = {
        "en": f"{text_base} {index}",
        "de": f"{text_base} {index} (DE)",
        "es": f"{text_base} {index} (ES)",
        "da": f"{text_base} {index} (DA)",
        "fr": f"{text_base} {index} (FR)",
        "pt": f"{text_base} {index} (PT)",
        "it": f"{text_base} {index} (IT)",
    }
    return [
        MultilingualString(language=lang, value=translations[lang])
        for lang in LANGUAGES
    ]

def create_concept_scheme(index: int) -> ConceptSchemeInput:
    """Create a concept scheme with the given index."""
    return ConceptSchemeInput(
        id=f"http://example.com/taxonomy/2024/scheme{index}",
        type=["http://www.w3.org/2004/02/skos/core#ConceptScheme"],
        http___www_w3_org_2004_02_skos_corepref_label=create_multilingual_string(
            "Example Taxonomy", index
        ),
        http___purl_org_ontology_bibo_status=[
            Status(id="http://purl.org/ontology/bibo/status/accepted")
        ],
        http___purl_org_dc_terms_created=[DateTime(
            type=DateTimeType.HTTP_COLON_SLASH_SLASH_WWW_DOT_W3_DOT_ORG_SLASH_2001_SLASH_XML_SCHEMA_HASH_DATE_TIME,
            value=datetime.now()
        )],
        http___purl_org_dc_terms_creator=[
            Node(id="http://example.com/organization")
        ],
        http___www_w3_org_2002_07_owlversion_info=[
            VersionString(value=f"1.0.{index}")
        ],
        http___www_w3_org_2004_02_skos_coredefinition=create_multilingual_string(
            "A comprehensive taxonomy for organizing and classifying various concepts and categories, version",
            index
        ),
        http___www_w3_org_2004_02_skos_corenotation=[{
            "@value": f"TAX-2024-{index:03d}",
            "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral"
        }]
    )

def create_concept(scheme_id: str, index: int) -> ConceptCreate:
    """Create a concept with the given index for a specific scheme."""
    concept_id = f"{scheme_id}/concept{index}"
    broader = None
    if index > 1:
        broader = [Node(id=f"{scheme_id}/concept{index-1}")]

    return ConceptCreate(
        id=concept_id,
        type=["http://www.w3.org/2004/02/skos/core#Concept"],
        http___www_w3_org_2004_02_skos_corepref_label=create_multilingual_string(
            "Example Concept", index
        ),
        http___www_w3_org_2004_02_skos_corein_scheme=[Node(id=scheme_id)],
        http___purl_org_ontology_bibo_status=[
            Status(id="http://purl.org/ontology/bibo/status/accepted")
        ],
        http___purl_org_dc_terms_created=[DateTime(
            type=DateTimeType.HTTP_COLON_SLASH_SLASH_WWW_DOT_W3_DOT_ORG_SLASH_2001_SLASH_XML_SCHEMA_HASH_DATE_TIME,
            value=datetime.now()
        )],
        http___purl_org_dc_terms_creator=[
            Node(id="http://example.com/organization")
        ],
        http___www_w3_org_2004_02_skos_coredefinition=create_multilingual_string(
            "A concept that represents a specific category or idea, version",
            index
        ),
        http___www_w3_org_2004_02_skos_corenotation=[{
            "@value": f"CON-{index:03d}",
            "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral"
        }],
        http___www_w3_org_2004_02_skos_corebroader=broader
    )

async def create_schemes():
    """Create 10 concept schemes."""
    configuration = pyst_client.Configuration(
        host=API_URL,
        api_key={"X-PyST-Auth-Token": API_TOKEN}
    )

    async with pyst_client.ApiClient(configuration) as api_client:
        concept_scheme_api = pyst_client.ConceptSchemeApi(api_client)

        for i in range(1, 11):
            try:
                scheme = create_concept_scheme(i)
                response = await concept_scheme_api.concept_scheme_create_concept_scheme_post(
                    concept_scheme_input=scheme,
                    x_pyst_auth_token=API_TOKEN
                )
                print(f"Created concept scheme {i} successfully")
            except Exception as e:
                print(f"Failed to create concept scheme {i}: {str(e)}")

async def create_concepts_for_scheme(scheme_id: str):
    """Create 5 concepts for a specific scheme."""
    configuration = pyst_client.Configuration(
        host=API_URL,
        api_key={"X-PyST-Auth-Token": API_TOKEN}
    )

    async with pyst_client.ApiClient(configuration) as api_client:
        concept_api = pyst_client.ConceptApi(api_client)

        for j in range(1, 6):
            try:
                concept = create_concept(scheme_id, j)
                await concept_api.concept_create_concept_post(
                    concept_create=concept,
                    x_pyst_auth_token=API_TOKEN
                )
                print(f"Created concept {j} for scheme {scheme_id} successfully")
            except Exception as e:
                print(f"Failed to create concept {j} for scheme {scheme_id}: {str(e)}")

async def create_all_data():
    """Create all sample data - schemes and concepts for all schemes."""
    configuration = pyst_client.Configuration(
        host=API_URL,
        api_key={"X-PyST-Auth-Token": API_TOKEN}
    )

    async with pyst_client.ApiClient(configuration) as api_client:
        concept_scheme_api = pyst_client.ConceptSchemeApi(api_client)
        concept_api = pyst_client.ConceptApi(api_client)

        # Create schemes
        for i in range(1, 11):
            try:
                scheme = create_concept_scheme(i)
                response = await concept_scheme_api.concept_scheme_create_concept_scheme_post(
                    concept_scheme_input=scheme,
                    x_pyst_auth_token=API_TOKEN
                )
                print(f"Created concept scheme {i} successfully")

                # Create concepts for this scheme
                for j in range(1, 6):
                    try:
                        concept = create_concept(scheme.id, j)
                        await concept_api.concept_create_concept_post(
                            concept_create=concept,
                            x_pyst_auth_token=API_TOKEN
                        )
                        print(f"Created concept {j} for scheme {i} successfully")
                    except Exception as e:
                        print(f"Failed to create concept {j} for scheme {i}: {str(e)}")
            except Exception as e:
                print(f"Failed to create concept scheme {i}: {str(e)}")

async def main():
    """Create sample data - either schemes, concepts, or both."""
    import argparse

    parser = argparse.ArgumentParser(description='Create sample data for the semantic taxonomy')
    parser.add_argument('--schemes', action='store_true', help='Create concept schemes')
    parser.add_argument('--concepts', action='store_true', help='Create concepts')
    parser.add_argument('--scheme-id', type=str, help='Scheme ID to create concepts for (required if --concepts is used)')
    parser.add_argument('--all', action='store_true', help='Create all sample data (schemes and concepts)')
    args = parser.parse_args()

    if args.all:
        await create_all_data()
        return

    if args.schemes:
        await create_schemes()

    if args.concepts:
        if not args.scheme_id:
            print("Error: --scheme-id is required when creating concepts")
            return
        await create_concepts_for_scheme(args.scheme_id)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
