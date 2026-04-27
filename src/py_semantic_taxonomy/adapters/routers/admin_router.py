from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, unquote, urlencode

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from py_semantic_taxonomy.adapters.routers import request_dto as req
from py_semantic_taxonomy.adapters.routers.web_router import (
    build_language_selector,
    concept_scheme_view_url,
    concept_view_url,
    format_languages,
    templates,
)
from py_semantic_taxonomy.cfg import Settings, get_settings
from py_semantic_taxonomy.dependencies import get_claim_store, get_graph_service
from py_semantic_taxonomy.domain import entities as de
from py_semantic_taxonomy.domain.constants import BIBO, DCTERMS, OWL, SKOS, XKOS, RDF_MAPPING
from py_semantic_taxonomy.domain.hash_utils import hash_fnv64
from py_semantic_taxonomy.domain.constants import RelationshipVerbs
from py_semantic_taxonomy.domain.url_utils import get_full_api_path

router = APIRouter(prefix="/web/admin", include_in_schema=False)

DATETIME_TYPE = "http://www.w3.org/2001/XMLSchema#dateTime"
CONVERSION_MULTIPLIER = "http://qudt.org/3.0.0/schema/qudt/conversionMultiplier"
STATUS_OPTIONS = [
    f"{BIBO}status/accepted",
    f"{BIBO}status/draft",
    f"{BIBO}status/rejected",
]
MAPPING_VERBS = [
    RelationshipVerbs.exact_match,
    RelationshipVerbs.close_match,
    RelationshipVerbs.broad_match,
    RelationshipVerbs.narrow_match,
    RelationshipVerbs.related_match,
]


def _admin_configured(settings: Settings) -> bool:
    return all(
        value and value != "missing"
        for value in (
            settings.gitlab_url,
            settings.gitlab_client_id,
            settings.gitlab_client_secret,
            settings.gitlab_admin_group,
        )
    )


def _default_language(language: str | None, settings: Settings) -> str:
    return language or settings.languages[0]


def _admin_redirect(request: Request, language: str) -> RedirectResponse:
    return RedirectResponse(
        str(request.url_for("admin_login")) + "?" + urlencode({"language": language}),
        status_code=303,
    )


def _ensure_admin(
    request: Request, language: str | None, settings: Settings
) -> dict[str, Any] | RedirectResponse:
    admin_user = request.session.get("admin_user")
    if admin_user:
        return admin_user
    return _admin_redirect(request, _default_language(language, settings))


def _ensure_csrf_token(request: Request) -> str:
    csrf_token = request.session.get("admin_csrf_token")
    if not csrf_token:
        csrf_token = quote(datetime.now(tz=timezone.utc).isoformat(), safe="")
        request.session["admin_csrf_token"] = csrf_token
    return csrf_token


def _validate_csrf(request: Request, csrf_token: str) -> None:
    if csrf_token != request.session.get("admin_csrf_token"):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


def _public_url_for(request: Request, route_name: str, settings: Settings) -> str:
    path = str(request.url_for(route_name).path)
    if settings.public_base_url:
        return f"{settings.public_base_url.rstrip('/')}{path}"
    return str(request.url_for(route_name))


def _language_selector(request: Request, language: str, settings: Settings) -> list[tuple[str, str]]:
    return build_language_selector(
        language,
        [
            (
                code,
                format_languages(settings.languages)[settings.languages.index(code)][1],
                str(request.url.include_query_params(language=code)),
            )
            for code in settings.languages
        ],
    )


def _base_context(
    request: Request,
    language: str,
    settings: Settings,
    **kwargs: Any,
) -> dict[str, Any]:
    return {
        "request": request,
        "language": language,
        "language_selector": _language_selector(request, language, settings),
        "suggest_api_url": get_full_api_path("suggest"),
        "query": "",
        **kwargs,
    }


def _split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _parse_multilingual(text: str, *, unique_per_language: bool) -> list[dict[str, str]]:
    result = []
    seen_languages = set()
    for line in _split_lines(text):
        separator = "|" if "|" in line else ":"
        if separator not in line:
            raise ValueError(
                f"Expected multilingual values in the form `language|text`, got `{line}`"
            )
        language, value = [part.strip() for part in line.split(separator, 1)]
        if not language or not value:
            raise ValueError(
                f"Expected multilingual values in the form `language|text`, got `{line}`"
            )
        if unique_per_language and language in seen_languages:
            raise ValueError(f"Language `{language}` was given more than once")
        seen_languages.add(language)
        result.append({"@language": language, "@value": value})
    return result


def _serialize_multilingual(values: list[dict[str, str]]) -> str:
    return "\n".join(
        f"{obj.get('@language', '')}|{obj.get('@value', '')}"
        for obj in values
        if obj.get("@value")
    )


def _value_for_language(values: list[dict[str, str]], language: str) -> str:
    for obj in values:
        if obj.get("@language") == language:
            return obj.get("@value", "")
    return ""


def _replace_language_value(
    values: list[dict[str, str]],
    *,
    language: str,
    text: str,
) -> list[dict[str, str]]:
    remaining = [obj for obj in values if obj.get("@language") != language]
    if text.strip():
        remaining.append({"@language": language, "@value": text.strip()})
    return remaining


def _parse_nodes(text: str) -> list[dict[str, str]]:
    return [{"@id": iri} for iri in _split_lines(text)]


def _serialize_nodes(values: list[dict[str, str]]) -> str:
    return "\n".join(obj.get("@id", "") for obj in values if obj.get("@id"))


def _parse_notations(text: str) -> list[dict[str, str]]:
    return [
        {
            "@value": value,
            "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral",
        }
        for value in _split_lines(text)
    ]


def _serialize_notations(values: list[dict[str, str]]) -> str:
    return "\n".join(obj.get("@value", "") for obj in values if obj.get("@value"))


def _modified_extra(existing_extra: dict[str, Any] | None = None) -> dict[str, Any]:
    extra = dict(existing_extra or {})
    extra[f"{DCTERMS}modified"] = [
        {"@type": DATETIME_TYPE, "@value": datetime.now(tz=timezone.utc).isoformat()}
    ]
    return extra


def _concept_scheme_form_data(concept_scheme: de.ConceptScheme | None = None) -> dict[str, Any]:
    if not concept_scheme:
        return {
            "id_": "",
            "pref_labels": "",
            "definitions": "",
            "notations": "",
            "status": STATUS_OPTIONS[0],
            "created": datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat(),
            "creators": "",
            "version": "",
        }
    return {
        "id_": concept_scheme.id_,
        "pref_labels": _serialize_multilingual(concept_scheme.pref_labels),
        "definitions": _serialize_multilingual(concept_scheme.definitions),
        "notations": _serialize_notations(concept_scheme.notations),
        "status": (
            concept_scheme.status[0].get("@id", STATUS_OPTIONS[0])
            if concept_scheme.status
            else STATUS_OPTIONS[0]
        ),
        "created": (
            concept_scheme.created[0].get("@value", "") if concept_scheme.created else ""
        ),
        "creators": _serialize_nodes(concept_scheme.creators),
        "version": concept_scheme.version[0].get("@value", "") if concept_scheme.version else "",
    }


def _concept_scheme_form_data_for_language(
    concept_scheme: de.ConceptScheme | None,
    *,
    language: str,
) -> dict[str, Any]:
    data = _concept_scheme_form_data(concept_scheme)
    data["pref_label_text"] = (
        _value_for_language(concept_scheme.pref_labels, language) if concept_scheme else ""
    )
    data["definition_text"] = (
        _value_for_language(concept_scheme.definitions, language) if concept_scheme else ""
    )
    return data


def _concept_form_data(
    concept: de.Concept | None = None,
    *,
    scheme_hint: str = "",
    broader_iris: list[str] | None = None,
) -> dict[str, Any]:
    if not concept:
        return {
            "id_": "",
            "pref_labels": "",
            "definitions": "",
            "notations": "",
            "status": STATUS_OPTIONS[0],
            "schemes": scheme_hint,
            "alt_labels": "",
            "hidden_labels": "",
            "broader_iris": "",
            "top_concept": True,
        }
    return {
        "id_": concept.id_,
        "pref_labels": _serialize_multilingual(concept.pref_labels),
        "definitions": _serialize_multilingual(concept.definitions),
        "notations": _serialize_notations(concept.notations),
        "status": concept.status[0].get("@id", STATUS_OPTIONS[0]) if concept.status else STATUS_OPTIONS[0],
        "schemes": scheme_hint or (concept.schemes[0].get("@id", "") if concept.schemes else ""),
        "alt_labels": _serialize_multilingual(concept.alt_labels),
        "hidden_labels": _serialize_multilingual(concept.hidden_labels),
        "broader_iris": "\n".join(broader_iris or []),
        "top_concept": bool(concept.top_concept_of),
    }


def _concept_form_data_for_language(
    concept: de.Concept | None,
    *,
    language: str,
    scheme_hint: str = "",
    broader_iris: list[str] | None = None,
) -> dict[str, Any]:
    data = _concept_form_data(concept, scheme_hint=scheme_hint, broader_iris=broader_iris)
    data["pref_label_text"] = (
        _value_for_language(concept.pref_labels, language) if concept else ""
    )
    data["definition_text"] = (
        _value_for_language(concept.definitions, language) if concept else ""
    )
    return data


def _association_form_data(
    association: de.Association | None = None,
    *,
    source_concept_iri: str = "",
) -> dict[str, Any]:
    if not association:
        return {
            "id_": "",
            "source_concept_iri": source_concept_iri,
            "target_concept_iri": "",
        }
    target = association.target_concepts[0] if association.target_concepts else {}
    return {
        "id_": association.id_,
        "source_concept_iri": (
            association.source_concepts[0].get("@id", "") if association.source_concepts else source_concept_iri
        ),
        "target_concept_iri": target.get("@id", ""),
    }


def _mapping_form_data(
    *,
    link_type: str = str(RelationshipVerbs.exact_match),
    target_iri: str = "",
    association_id: str = "",
    ) -> dict[str, Any]:
    return {
        "link_type": link_type,
        "target_iri": target_iri,
        "association_id": association_id,
        "original_link_type": link_type,
        "original_target_iri": target_iri,
    }


def _concept_scheme_payload(form_data: dict[str, Any], *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        RDF_MAPPING["id_"]: form_data["id_"],
        RDF_MAPPING["types"]: [f"{SKOS}ConceptScheme"],
        RDF_MAPPING["pref_labels"]: _parse_multilingual(
            form_data["pref_labels"], unique_per_language=True
        ),
        RDF_MAPPING["definitions"]: _parse_multilingual(
            form_data["definitions"], unique_per_language=True
        ),
        RDF_MAPPING["notations"]: _parse_notations(form_data["notations"]),
        RDF_MAPPING["status"]: [{"@id": form_data["status"]}],
        f"{DCTERMS}created": [{"@type": DATETIME_TYPE, "@value": form_data["created"]}],
        f"{DCTERMS}creator": _parse_nodes(form_data["creators"]),
        f"{OWL}versionInfo": [{"@value": form_data["version"]}],
    }
    payload.update(extra or {})
    return payload


def _concept_payload(form_data: dict[str, Any], *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    schemes = _parse_nodes(form_data["schemes"])
    top_concept_of = schemes[:1] if form_data["top_concept"] else []
    payload = {
        RDF_MAPPING["id_"]: form_data["id_"],
        RDF_MAPPING["types"]: [f"{SKOS}Concept"],
        RDF_MAPPING["pref_labels"]: _parse_multilingual(
            form_data["pref_labels"], unique_per_language=True
        ),
        RDF_MAPPING["definitions"]: _parse_multilingual(
            form_data["definitions"], unique_per_language=True
        ),
        RDF_MAPPING["notations"]: _parse_notations(form_data["notations"]),
        RDF_MAPPING["status"]: [{"@id": form_data["status"]}],
        RDF_MAPPING["schemes"]: schemes,
        RDF_MAPPING["alt_labels"]: _parse_multilingual(
            form_data["alt_labels"], unique_per_language=False
        ),
        RDF_MAPPING["hidden_labels"]: _parse_multilingual(
            form_data["hidden_labels"], unique_per_language=False
        ),
        RDF_MAPPING["top_concept_of"]: top_concept_of,
    }
    payload.update(extra or {})
    return payload


def _association_payload(
    form_data: dict[str, Any],
    *,
    existing_association: de.Association | None = None,
) -> dict[str, Any]:
    target_node: dict[str, Any] = {"@id": form_data["target_concept_iri"]}
    if existing_association and existing_association.target_concepts:
        current_target = existing_association.target_concepts[0]
        if current_target.get("@id") == form_data["target_concept_iri"]:
            if CONVERSION_MULTIPLIER in current_target:
                target_node[CONVERSION_MULTIPLIER] = current_target[CONVERSION_MULTIPLIER]
    return {
        RDF_MAPPING["id_"]: form_data["id_"],
        RDF_MAPPING["types"]: [f"{XKOS}ConceptAssociation"],
        RDF_MAPPING["source_concepts"]: [{"@id": form_data["source_concept_iri"]}],
        RDF_MAPPING["target_concepts"]: [target_node],
    }


def _generate_association_iri(source_concept_iri: str, target_concept_iri: str) -> str:
    base = source_concept_iri.rstrip("/")
    return f"{base}/association/{hash_fnv64(source_concept_iri + '|' + target_concept_iri)}"


def _build_concept_scheme_form_data(
    *,
    language: str,
    id_: str,
    pref_label_text: str,
    definition_text: str,
    notations: str,
    status: str,
    created: str,
    creators: str,
    version: str,
    existing: de.ConceptScheme | None = None,
) -> dict[str, Any]:
    pref_labels = _replace_language_value(
        existing.pref_labels if existing else [],
        language=language,
        text=pref_label_text,
    )
    definitions = _replace_language_value(
        existing.definitions if existing else [],
        language=language,
        text=definition_text,
    )
    return {
        "id_": id_,
        "pref_labels": _serialize_multilingual(pref_labels),
        "definitions": _serialize_multilingual(definitions),
        "pref_label_text": pref_label_text,
        "definition_text": definition_text,
        "notations": notations,
        "status": status,
        "created": created,
        "creators": creators,
        "version": version,
    }


def _build_concept_form_data(
    *,
    language: str,
    id_: str,
    pref_label_text: str,
    definition_text: str,
    notations: str,
    status: str,
    schemes: str,
    alt_labels: str,
    hidden_labels: str,
    broader_iris: str,
    top_concept: bool,
    existing: de.Concept | None = None,
) -> dict[str, Any]:
    pref_labels = _replace_language_value(
        existing.pref_labels if existing else [],
        language=language,
        text=pref_label_text,
    )
    definitions = _replace_language_value(
        existing.definitions if existing else [],
        language=language,
        text=definition_text,
    )
    return {
        "id_": id_,
        "pref_labels": _serialize_multilingual(pref_labels),
        "definitions": _serialize_multilingual(definitions),
        "pref_label_text": pref_label_text,
        "definition_text": definition_text,
        "notations": notations,
        "status": status,
        "schemes": schemes,
        "alt_labels": alt_labels,
        "hidden_labels": hidden_labels,
        "broader_iris": broader_iris,
        "top_concept": top_concept,
    }


async def _exchange_code_for_token(code: str, redirect_uri: str, settings: Settings) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.gitlab_url.rstrip('/')}/oauth/token",
            data={
                "client_id": settings.gitlab_client_id,
                "client_secret": settings.gitlab_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = response.text.strip()
        raise HTTPException(
            status_code=502,
            detail=(
                "GitLab OAuth token exchange failed. "
                "Check that the configured callback URL exactly matches the GitLab application "
                f"redirect URI and that the authorization code was not reused. GitLab said: {detail}"
            ),
        ) from exc
    return response.json()


async def _gitlab_user(access_token: str, settings: Settings) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.gitlab_url.rstrip('/')}/api/v4/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    response.raise_for_status()
    return response.json()


async def _gitlab_group_member(user_id: int, access_token: str, settings: Settings) -> bool:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.gitlab_url.rstrip('/')}/api/v4/groups/"
            f"{quote(settings.gitlab_admin_group, safe='')}/members/all/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if response.status_code == 404:
        return False
    response.raise_for_status()
    member = response.json()
    return member.get("access_level", 0) >= settings.gitlab_admin_min_access_level


async def _concept_association_rows(
    request: Request,
    *,
    concept_iri: str,
    language: str,
    concept_scheme: str,
    service,
) -> list[dict[str, Any]]:
    associations = await service.association_get_all(source_concept_iri=concept_iri)
    rows = []
    for association in sorted(associations, key=lambda obj: obj.id_):
        if association.kind != de.AssociationKind.simple:
            continue
        target = association.target_concepts[0] if association.target_concepts else {}
        target_iri = target.get("@id", "")
        target_label = target_iri
        target_url = target_iri
        try:
            target_concept = await service.concept_get(target_iri)
            target_label = next(
                (
                    obj.get("@value", "")
                    for obj in target_concept.pref_labels
                    if obj.get("@language") == language
                ),
                target_iri,
            )
            target_url = concept_view_url(
                request,
                target_concept.id_,
                target_concept.schemes[0]["@id"],
                language,
            )
        except de.ConceptNotFoundError:
            pass
        rows.append(
            {
                "id_": association.id_,
                "target_iri": target_iri,
                "target_label": target_label,
                "target_url": target_url,
                "edit_url": (
                    str(request.url_for("admin_edit_concept", iri=quote(concept_iri)))
                    + "?"
                    + urlencode(
                        {
                            "language": language,
                            "concept_scheme": concept_scheme,
                            "link_type": "association",
                            "association_id": association.id_,
                            "target_iri": target_iri,
                        }
                    )
                ),
            }
        )
    return rows


async def _concept_mapping_rows(
    request: Request,
    *,
    concept_iri: str,
    language: str,
    concept_scheme: str,
    service,
) -> list[dict[str, Any]]:
    relationships = await service.relationships_get(iri=concept_iri, source=True, target=False)
    rows = []
    for rel in sorted(
        [rel for rel in relationships if rel.source == concept_iri and rel.predicate in MAPPING_VERBS],
        key=lambda obj: (obj.predicate, obj.target),
    ):
        target_label = rel.target
        target_url = rel.target
        try:
            target_concept = await service.concept_get(rel.target)
            target_label = next(
                (
                    obj.get("@value", "")
                    for obj in target_concept.pref_labels
                    if obj.get("@language") == language
                ),
                rel.target,
            )
            target_url = concept_view_url(
                request,
                target_concept.id_,
                target_concept.schemes[0]["@id"],
                language,
            )
        except de.ConceptNotFoundError:
            pass
        rows.append(
            {
                "predicate": str(rel.predicate),
                "predicate_label": str(rel.predicate).split("#")[-1],
                "target_iri": rel.target,
                "target_label": target_label,
                "target_url": target_url,
                "edit_url": (
                    str(request.url_for("admin_edit_concept", iri=quote(concept_iri)))
                    + "?"
                    + urlencode(
                        {
                            "language": language,
                            "concept_scheme": concept_scheme,
                            "link_type": str(rel.predicate),
                            "target_iri": rel.target,
                        }
                    )
                ),
            }
        )
    return rows


async def _concept_relationship_rows(
    request: Request,
    *,
    concept_iri: str,
    language: str,
    concept_scheme: str,
    service,
) -> list[dict[str, Any]]:
    relationships = await service.relationships_get(iri=concept_iri, source=True, target=True)
    rows = []
    seen = set()
    for rel in relationships:
        key = (rel.source, rel.target, str(rel.predicate))
        if key in seen or rel.predicate in MAPPING_VERBS:
            continue
        seen.add(key)

        related_iri = rel.target if rel.source == concept_iri else rel.source
        related_label = related_iri
        related_url = related_iri
        try:
            related_concept = await service.concept_get(related_iri)
            related_label = next(
                (
                    obj.get("@value", "")
                    for obj in related_concept.pref_labels
                    if obj.get("@language") == language
                ),
                related_iri,
            )
            related_url = concept_view_url(
                request,
                related_concept.id_,
                related_concept.schemes[0]["@id"],
                language,
            )
        except de.ConceptNotFoundError:
            pass

        predicate_label = str(rel.predicate).split("#")[-1]
        if rel.source != concept_iri and rel.predicate == RelationshipVerbs.broader:
            predicate_label = "narrower"
        elif rel.source != concept_iri:
            predicate_label = f"incoming {predicate_label}"

        rows.append(
            {
                "source_iri": rel.source,
                "target_iri": rel.target,
                "predicate": str(rel.predicate),
                "predicate_label": predicate_label,
                "related_iri": related_iri,
                "related_label": related_label,
                "related_url": related_url,
                "edit_url": (
                    str(request.url_for("admin_edit_concept", iri=quote(concept_iri)))
                    + "?"
                    + urlencode({"language": language, "concept_scheme": concept_scheme})
                ),
            }
        )
    return sorted(rows, key=lambda row: (row["predicate_label"], row["related_iri"]))


async def _delete_concept_dependencies(*, concept_iri: str, service) -> None:
    relationships = await service.relationships_get(iri=concept_iri, source=True, target=True)
    unique_relationships = {
        (rel.source, rel.target, rel.predicate): rel for rel in relationships
    }
    if unique_relationships:
        await service.relationships_delete(list(unique_relationships.values()))

    associations = [
        *(await service.association_get_all(source_concept_iri=concept_iri)),
        *(await service.association_get_all(target_concept_iri=concept_iri)),
    ]
    for association_id in {association.id_ for association in associations}:
        await service.association_delete(association_id)


def _render_admin_dashboard(
    request: Request,
    *,
    language: str,
    settings: Settings,
    admin_user: dict[str, Any],
    concept_schemes: list[de.ConceptScheme],
    pending_claim_count: int = 0,
    message: str | None = None,
    error: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "admin_dashboard.html",
        context=_base_context(
            request,
            language,
            settings,
            admin_user=admin_user,
            concept_schemes=concept_schemes,
            pending_claim_count=pending_claim_count,
            csrf_token=_ensure_csrf_token(request),
            message=message,
            error=error,
            gitlab_admin_group=settings.gitlab_admin_group,
        ),
    )


def _render_concept_scheme_form(
    request: Request,
    *,
    language: str,
    settings: Settings,
    admin_user: dict[str, Any],
    form_data: dict[str, Any],
    form_mode: str,
    error: str | None = None,
    message: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "admin_concept_scheme_form.html",
        context=_base_context(
            request,
            language,
            settings,
            admin_user=admin_user,
            csrf_token=_ensure_csrf_token(request),
            form_data=form_data,
            form_mode=form_mode,
            status_options=STATUS_OPTIONS,
            error=error,
            message=message,
        ),
    )


def _render_concept_form(
    request: Request,
    *,
    language: str,
    settings: Settings,
    admin_user: dict[str, Any],
    form_data: dict[str, Any],
    concept_schemes: list[de.ConceptScheme],
    relationship_rows: list[dict[str, Any]] | None = None,
    mappings: list[dict[str, Any]] | None = None,
    mapping_form_data: dict[str, Any] | None = None,
    associations: list[dict[str, Any]] | None = None,
    association_form_data: dict[str, Any] | None = None,
    concept_form_action: str | None = None,
    mapping_form_action: str | None = None,
    association_form_action: str | None = None,
    form_mode: str,
    error: str | None = None,
    message: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "admin_concept_form.html",
        context=_base_context(
            request,
            language,
            settings,
            admin_user=admin_user,
            csrf_token=_ensure_csrf_token(request),
            form_data=form_data,
            concept_schemes=concept_schemes,
            relationship_rows=relationship_rows or [],
            mappings=mappings or [],
            mapping_form_data=mapping_form_data,
            associations=associations or [],
            association_form_data=association_form_data,
            concept_form_action=concept_form_action,
            mapping_form_action=mapping_form_action,
            association_form_action=association_form_action,
            form_mode=form_mode,
            status_options=STATUS_OPTIONS,
            mapping_verbs=MAPPING_VERBS,
            error=error,
            message=message,
        ),
    )


@router.get("/login", name="admin_login")
async def admin_login(
    request: Request,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
):
    language = _default_language(language, settings)
    if request.session.get("admin_user"):
        return RedirectResponse(
            str(request.url_for("admin_dashboard")) + "?" + urlencode({"language": language}),
            status_code=303,
        )
    if not _admin_configured(settings):
        raise HTTPException(status_code=503, detail="GitLab admin authentication is not configured")

    state = quote(datetime.now(tz=timezone.utc).isoformat(), safe="")
    request.session["gitlab_oauth_state"] = state
    redirect_uri = _public_url_for(request, "admin_gitlab_callback", settings)
    authorization_url = (
        f"{settings.gitlab_url.rstrip('/')}/oauth/authorize?"
        + urlencode(
            {
                "client_id": settings.gitlab_client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": settings.gitlab_oauth_scope,
                "state": state,
            }
        )
    )
    return RedirectResponse(authorization_url, status_code=303)


@router.get("/callback", name="admin_gitlab_callback")
async def admin_gitlab_callback(
    request: Request,
    code: str,
    state: str,
    settings: Settings = Depends(get_settings),
):
    if not _admin_configured(settings):
        raise HTTPException(status_code=503, detail="GitLab admin authentication is not configured")
    if state != request.session.get("gitlab_oauth_state"):
        raise HTTPException(status_code=400, detail="Invalid GitLab OAuth state")

    redirect_uri = _public_url_for(request, "admin_gitlab_callback", settings)
    token = await _exchange_code_for_token(code, redirect_uri, settings)
    access_token = token["access_token"]
    user = await _gitlab_user(access_token, settings)
    is_group_member = await _gitlab_group_member(user["id"], access_token, settings)
    if not is_group_member:
        raise HTTPException(
            status_code=403,
            detail=(
                "GitLab user is not in the configured admin group with the required "
                "access level"
            ),
        )

    request.session.pop("gitlab_oauth_state", None)
    request.session["admin_user"] = {
        "id": user["id"],
        "username": user.get("username"),
        "name": user.get("name") or user.get("username") or "Admin",
    }
    return RedirectResponse(str(request.url_for("admin_dashboard")), status_code=303)


@router.post("/logout")
async def admin_logout(
    request: Request,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
):
    request.session.clear()
    return RedirectResponse(
        str(request.url_for("web_concept_schemes"))
        + "?"
        + urlencode({"language": _default_language(language, settings)}),
        status_code=303,
    )


@router.get("/", response_class=HTMLResponse, name="admin_dashboard")
async def admin_dashboard(
    request: Request,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
    claim_store=Depends(get_claim_store),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user

    language = _default_language(language, settings)
    concept_schemes = await service.concept_scheme_get_all()
    pending_claims = await claim_store.get_all(status="pending")
    for scheme in concept_schemes:
        scheme.url = concept_scheme_view_url(request, scheme.id_, language)
        scheme.edit_url = (
            str(request.url_for("admin_edit_concept_scheme", iri=quote(scheme.id_)))
            + "?"
            + urlencode({"language": language})
        )
        scheme.delete_url = str(request.url_for("admin_delete_concept_scheme", iri=quote(scheme.id_)))
        scheme.new_concept_url = (
            str(request.url_for("admin_new_concept"))
            + "?"
            + urlencode({"language": language, "concept_scheme": scheme.id_})
        )

    return _render_admin_dashboard(
        request,
        language=language,
        settings=settings,
        admin_user=admin_user,
        concept_schemes=concept_schemes,
        pending_claim_count=len(pending_claims),
        message=request.query_params.get("message"),
        error=request.query_params.get("error"),
    )


@router.get("/claims", response_class=HTMLResponse, name="admin_claims")
async def admin_claims(
    request: Request,
    status: str | None = "pending",
    language: str | None = None,
    settings: Settings = Depends(get_settings),
    claim_store=Depends(get_claim_store),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user

    language = _default_language(language, settings)
    claims = await claim_store.get_all(status=status or None)
    return templates.TemplateResponse(
        request,
        "admin_claims.html",
        context=_base_context(
            request,
            language,
            settings,
            admin_user=admin_user,
            claims=claims,
            status=status or "",
            csrf_token=_ensure_csrf_token(request),
            message=request.query_params.get("message"),
            error=request.query_params.get("error"),
        ),
    )


@router.get("/claims/{claim_id}", response_class=HTMLResponse, name="admin_claim_detail")
async def admin_claim_detail(
    request: Request,
    claim_id: int,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
    claim_store=Depends(get_claim_store),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user

    claim = await claim_store.get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    language = _default_language(language, settings)
    return templates.TemplateResponse(
        request,
        "admin_claim_detail.html",
        context=_base_context(
            request,
            language,
            settings,
            admin_user=admin_user,
            claim=claim,
            csrf_token=_ensure_csrf_token(request),
        ),
    )


@router.post("/claims/{claim_id}/review", name="admin_review_claim")
async def admin_review_claim(
    request: Request,
    claim_id: int,
    csrf_token: str = Form(...),
    decision: str = Form(...),
    comment: str = Form(""),
    language: str = Form("en"),
    settings: Settings = Depends(get_settings),
    claim_store=Depends(get_claim_store),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)

    status = {"accept": "accepted", "reject": "rejected"}.get(decision)
    if not status:
        raise HTTPException(status_code=422, detail="Unknown review decision")

    claim = await claim_store.get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim["status"] != "pending":
        return RedirectResponse(
            str(request.url_for("admin_claim_detail", claim_id=claim_id))
            + "?"
            + urlencode({"language": language, "error": "Claim has already been reviewed"}),
            status_code=303,
        )

    await claim_store.review(
        claim_id=claim_id,
        status=status,
        reviewer=admin_user,
        comment=comment.strip(),
    )
    return RedirectResponse(
        str(request.url_for("admin_claims"))
        + "?"
        + urlencode({"language": language, "status": "pending", "message": f"Claim {status}"}),
        status_code=303,
    )


@router.get("/concept_schemes/new", response_class=HTMLResponse, name="admin_new_concept_scheme")
async def admin_new_concept_scheme(
    request: Request,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user

    language = _default_language(language, settings)
    return _render_concept_scheme_form(
        request,
        language=language,
        settings=settings,
        admin_user=admin_user,
        form_data=_concept_scheme_form_data_for_language(None, language=language),
        form_mode="create",
    )


@router.post("/concept_schemes/new", response_class=HTMLResponse)
async def admin_create_concept_scheme(
    request: Request,
    csrf_token: str = Form(...),
    id_: str = Form(...),
    pref_label_text: str = Form(...),
    definition_text: str = Form(""),
    notations: str = Form(""),
    status: str = Form(...),
    created: str = Form(...),
    creators: str = Form(""),
    version: str = Form(...),
    language: str = Form("en"),
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)

    form_data = _build_concept_scheme_form_data(
        language=language,
        id_=id_,
        pref_label_text=pref_label_text,
        definition_text=definition_text,
        notations=notations,
        status=status,
        created=created,
        creators=creators,
        version=version,
    )
    try:
        payload = _concept_scheme_payload(form_data)
        validated = req.ConceptScheme.model_validate(payload)
        concept_scheme = de.ConceptScheme.from_json_ld(validated.model_dump(by_alias=True))
        await service.concept_scheme_create(concept_scheme)
    except (ValidationError, ValueError, de.DuplicateIRI) as exc:
        return _render_concept_scheme_form(
            request,
            language=language,
            settings=settings,
            admin_user=admin_user,
            form_data=form_data,
            form_mode="create",
            error=str(exc),
        )

    return RedirectResponse(
        str(request.url_for("admin_edit_concept_scheme", iri=quote(id_)))
        + "?"
        + urlencode({"language": language, "message": "Concept scheme created"}),
        status_code=303,
    )


@router.get(
    "/concept_schemes/{iri:path}/edit",
    response_class=HTMLResponse,
    name="admin_edit_concept_scheme",
)
async def admin_edit_concept_scheme(
    request: Request,
    iri: str = Path(...),
    language: str | None = None,
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user

    language = _default_language(language, settings)
    concept_scheme = await service.concept_scheme_get(unquote(iri))
    return _render_concept_scheme_form(
        request,
        language=language,
        settings=settings,
        admin_user=admin_user,
        form_data=_concept_scheme_form_data_for_language(concept_scheme, language=language),
        form_mode="edit",
        message=request.query_params.get("message"),
    )


@router.post("/concept_schemes/{iri:path}/edit", response_class=HTMLResponse)
async def admin_update_concept_scheme(
    request: Request,
    iri: str = Path(...),
    csrf_token: str = Form(...),
    id_: str = Form(...),
    pref_label_text: str = Form(...),
    definition_text: str = Form(""),
    notations: str = Form(""),
    status: str = Form(...),
    created: str = Form(...),
    creators: str = Form(""),
    version: str = Form(...),
    language: str = Form("en"),
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)

    current = await service.concept_scheme_get(iri)
    form_data = _build_concept_scheme_form_data(
        language=language,
        id_=id_,
        pref_label_text=pref_label_text,
        definition_text=definition_text,
        notations=notations,
        status=status,
        created=created,
        creators=creators,
        version=version,
        existing=current,
    )
    try:
        payload = _concept_scheme_payload(form_data, extra=_modified_extra(current.extra))
        validated = req.ConceptScheme.model_validate(payload)
        concept_scheme = de.ConceptScheme.from_json_ld(validated.model_dump(by_alias=True))
        await service.concept_scheme_update(concept_scheme)
    except (ValidationError, ValueError, de.ConceptSchemeNotFoundError) as exc:
        return _render_concept_scheme_form(
            request,
            language=language,
            settings=settings,
            admin_user=admin_user,
            form_data=form_data,
            form_mode="edit",
            error=str(exc),
        )

    return RedirectResponse(
        str(request.url_for("admin_edit_concept_scheme", iri=quote(id_)))
        + "?"
        + urlencode({"language": language, "message": "Concept scheme updated"}),
        status_code=303,
    )


@router.post("/concept_schemes/{iri:path}/delete", name="admin_delete_concept_scheme")
async def admin_delete_concept_scheme(
    request: Request,
    iri: str = Path(...),
    csrf_token: str = Form(...),
    language: str = Form("en"),
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)

    concepts = await service.concept_get_all(concept_scheme_iri=iri)
    shared_concepts = [concept.id_ for concept in concepts if len(concept.schemes) > 1]
    if shared_concepts:
        preview = ", ".join(shared_concepts[:3])
        if len(shared_concepts) > 3:
            preview += ", ..."
        return RedirectResponse(
            str(request.url_for("admin_dashboard"))
            + "?"
            + urlencode(
                {
                    "language": language,
                    "error": (
                        "Concept scheme cannot be deleted while shared concepts still reference it: "
                        + preview
                    ),
                }
            ),
            status_code=303,
        )

    for concept in concepts:
        await _delete_concept_dependencies(concept_iri=concept.id_, service=service)
        await service.concept_delete(concept.id_)
    await service.concept_scheme_delete(iri)
    return RedirectResponse(
        str(request.url_for("admin_dashboard"))
        + "?"
        + urlencode({"language": language, "message": "Concept scheme deleted"}),
        status_code=303,
    )


@router.get("/concepts/new", response_class=HTMLResponse, name="admin_new_concept")
async def admin_new_concept(
    request: Request,
    concept_scheme: str | None = None,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user

    language = _default_language(language, settings)
    concept_schemes = await service.concept_scheme_get_all()
    return _render_concept_form(
        request,
        language=language,
        settings=settings,
        admin_user=admin_user,
        form_data=_concept_form_data_for_language(
            None, language=language, scheme_hint=concept_scheme or ""
        ),
        concept_schemes=concept_schemes,
        form_mode="create",
    )


@router.post("/concepts/new", response_class=HTMLResponse)
async def admin_create_concept(
    request: Request,
    csrf_token: str = Form(...),
    id_: str = Form(...),
    pref_label_text: str = Form(...),
    definition_text: str = Form(""),
    notations: str = Form(""),
    status: str = Form(...),
    schemes: str = Form(...),
    alt_labels: str = Form(""),
    hidden_labels: str = Form(""),
    broader_iris: str = Form(""),
    top_concept: bool = Form(False),
    language: str = Form("en"),
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)

    concept_schemes = await service.concept_scheme_get_all()
    form_data = _build_concept_form_data(
        language=language,
        id_=id_,
        pref_label_text=pref_label_text,
        definition_text=definition_text,
        notations=notations,
        status=status,
        schemes=schemes,
        alt_labels=alt_labels,
        hidden_labels=hidden_labels,
        broader_iris=broader_iris,
        top_concept=top_concept,
    )
    try:
        payload = _concept_payload(form_data)
        if top_concept and _split_lines(broader_iris):
            raise ValueError("A top concept cannot also have broader concepts")
        validated = req.ConceptCreate.model_validate(
            {
                **payload,
                str(RelationshipVerbs.broader): _parse_nodes(broader_iris),
            }
        )
        json_ld = validated.model_dump(by_alias=True)
        concept = de.Concept.from_json_ld(json_ld)
        relationships = de.Relationship.from_json_ld(json_ld)
        await service.concept_create(concept, relationships)
    except (ValidationError, ValueError, de.DuplicateIRI, de.ConceptSchemesNotInDatabase) as exc:
        return _render_concept_form(
            request,
            language=language,
            settings=settings,
            admin_user=admin_user,
            form_data=form_data,
            concept_schemes=concept_schemes,
            form_mode="create",
            error=str(exc),
        )

    primary_scheme = _parse_nodes(schemes)[0]["@id"]
    return RedirectResponse(
        str(request.url_for("admin_edit_concept", iri=quote(id_)))
        + "?"
        + urlencode(
            {
                "language": language,
                "concept_scheme": primary_scheme,
                "message": "Concept created",
            }
        ),
        status_code=303,
    )


@router.get("/concepts/{iri:path}/edit", response_class=HTMLResponse, name="admin_edit_concept")
async def admin_edit_concept(
    request: Request,
    iri: str = Path(...),
    concept_scheme: str | None = None,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user

    language = _default_language(language, settings)
    concept = await service.concept_get(iri)
    relationships = await service.relationships_get(iri=iri, source=True, target=True)
    broader_iris = [
        rel.target
        for rel in relationships
        if rel.source == concept.id_ and rel.predicate == RelationshipVerbs.broader
    ]
    concept_schemes = await service.concept_scheme_get_all()
    selected_scheme = concept_scheme or concept.schemes[0]["@id"]
    relationship_rows = await _concept_relationship_rows(
        request,
        concept_iri=concept.id_,
        language=language,
        concept_scheme=selected_scheme,
        service=service,
    )
    associations = await _concept_association_rows(
        request,
        concept_iri=concept.id_,
        language=language,
        concept_scheme=selected_scheme,
        service=service,
    )
    mappings = await _concept_mapping_rows(
        request,
        concept_iri=concept.id_,
        language=language,
        concept_scheme=selected_scheme,
        service=service,
    )
    mapping_form = _mapping_form_data(
        link_type=request.query_params.get("link_type", str(RelationshipVerbs.exact_match)),
        target_iri=request.query_params.get("target_iri", ""),
        association_id=request.query_params.get("association_id", ""),
    )
    response = _render_concept_form(
        request,
        language=language,
        settings=settings,
        admin_user=admin_user,
        form_data=_concept_form_data_for_language(
            concept, language=language, scheme_hint=selected_scheme, broader_iris=broader_iris
        ),
        concept_schemes=concept_schemes,
        relationship_rows=relationship_rows,
        mappings=mappings,
        mapping_form_data=mapping_form,
        associations=associations,
        association_form_data=_association_form_data(source_concept_iri=concept.id_),
        concept_form_action=str(request.url_for("admin_update_concept", iri=quote(concept.id_))),
        mapping_form_action=str(request.url_for("admin_upsert_link", iri=quote(concept.id_))),
        association_form_action=str(
            request.url_for("admin_create_association", iri=quote(concept.id_))
        ),
        form_mode="edit",
        message=request.query_params.get("message"),
    )
    return response


@router.post("/concepts/{iri:path}/edit", response_class=HTMLResponse)
async def admin_update_concept(
    request: Request,
    iri: str = Path(...),
    csrf_token: str = Form(...),
    id_: str = Form(...),
    pref_label_text: str = Form(...),
    definition_text: str = Form(""),
    notations: str = Form(""),
    status: str = Form(...),
    schemes: str = Form(...),
    alt_labels: str = Form(""),
    hidden_labels: str = Form(""),
    broader_iris: str = Form(""),
    top_concept: bool = Form(False),
    language: str = Form("en"),
    concept_scheme: str | None = Form(None),
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)

    current = await service.concept_get(iri)
    current_relationships = await service.relationships_get(iri=iri, source=True, target=True)
    concept_schemes = await service.concept_scheme_get_all()
    selected_scheme = concept_scheme or current.schemes[0]["@id"]
    relationship_rows = await _concept_relationship_rows(
        request,
        concept_iri=current.id_,
        language=language,
        concept_scheme=selected_scheme,
        service=service,
    )
    associations = await _concept_association_rows(
        request,
        concept_iri=current.id_,
        language=language,
        concept_scheme=selected_scheme,
        service=service,
    )
    mappings = await _concept_mapping_rows(
        request,
        concept_iri=current.id_,
        language=language,
        concept_scheme=selected_scheme,
        service=service,
    )
    form_data = _build_concept_form_data(
        language=language,
        id_=id_,
        pref_label_text=pref_label_text,
        definition_text=definition_text,
        notations=notations,
        status=status,
        schemes=schemes,
        alt_labels=alt_labels,
        hidden_labels=hidden_labels,
        broader_iris=broader_iris,
        top_concept=top_concept,
        existing=current,
    )
    try:
        payload = _concept_payload(form_data, extra=_modified_extra(current.extra))
        if top_concept and _split_lines(broader_iris):
            raise ValueError("A top concept cannot also have broader concepts")
        validated = req.ConceptUpdate.model_validate(payload)
        concept = de.Concept.from_json_ld(validated.model_dump(by_alias=True))
        await service.concept_update(concept)

        existing_broader = {
            rel.target
            for rel in current_relationships
            if rel.source == current.id_ and rel.predicate == RelationshipVerbs.broader
        }
        desired_broader = set(_split_lines(broader_iris))
        if desired_broader - existing_broader:
            await service.relationships_create(
                [
                    de.Relationship(
                        source=current.id_,
                        target=target,
                        predicate=RelationshipVerbs.broader,
                    )
                    for target in sorted(desired_broader - existing_broader)
                ]
            )
        if existing_broader - desired_broader:
            await service.relationships_delete(
                [
                    de.Relationship(
                        source=current.id_,
                        target=target,
                        predicate=RelationshipVerbs.broader,
                    )
                    for target in sorted(existing_broader - desired_broader)
                ]
            )
    except (
        ValidationError,
        ValueError,
        de.ConceptNotFoundError,
        de.RelationshipsInCurrentConceptScheme,
        de.ConceptSchemesNotInDatabase,
        de.HierarchyConflict,
        de.HierarchicRelationshipAcrossConceptScheme,
        de.DuplicateRelationship,
    ) as exc:
        return _render_concept_form(
            request,
            language=language,
            settings=settings,
            admin_user=admin_user,
            form_data=form_data,
            concept_schemes=concept_schemes,
            relationship_rows=relationship_rows,
            mappings=mappings,
            mapping_form_data=_mapping_form_data(),
            associations=associations,
            association_form_data=_association_form_data(source_concept_iri=current.id_),
            concept_form_action=str(request.url_for("admin_update_concept", iri=quote(current.id_))),
            mapping_form_action=str(request.url_for("admin_upsert_link", iri=quote(current.id_))),
            association_form_action=str(
                request.url_for("admin_create_association", iri=quote(current.id_))
            ),
            form_mode="edit",
            error=str(exc),
        )

    redirect_scheme = concept_scheme or _parse_nodes(schemes)[0]["@id"]
    return RedirectResponse(
        str(request.url_for("admin_edit_concept", iri=quote(id_)))
        + "?"
        + urlencode(
            {
                "language": language,
                "concept_scheme": redirect_scheme,
                "message": "Concept updated",
            }
        ),
        status_code=303,
    )


@router.post("/concepts/{iri:path}/delete", name="admin_delete_concept")
async def admin_delete_concept(
    request: Request,
    iri: str = Path(...),
    csrf_token: str = Form(...),
    language: str = Form("en"),
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)

    await _delete_concept_dependencies(concept_iri=iri, service=service)
    await service.concept_delete(iri)

    return RedirectResponse(
        str(request.url_for("admin_dashboard"))
        + "?"
        + urlencode({"language": language, "message": "Concept deleted"}),
        status_code=303,
    )


@router.post("/concepts/{iri:path}/links", name="admin_upsert_link")
async def admin_upsert_link(
    request: Request,
    iri: str = Path(...),
    csrf_token: str = Form(...),
    link_type: str = Form(str(RelationshipVerbs.exact_match)),
    target_iri: str = Form(...),
    association_id: str = Form(""),
    original_link_type: str = Form(""),
    original_target_iri: str = Form(""),
    language: str = Form("en"),
    concept_scheme: str | None = Form(None),
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)

    current = await service.concept_get(iri)
    target_scheme = concept_scheme or current.schemes[0]["@id"]
    try:
        if link_type == "association":
            if original_link_type and original_link_type != "association" and original_target_iri:
                await service.relationships_delete(
                    [
                        de.Relationship(
                            source=iri,
                            target=original_target_iri,
                            predicate=RelationshipVerbs(original_link_type),
                        )
                    ]
                )
            assoc_id = association_id.strip() or _generate_association_iri(iri, target_iri)
            existing_association = None
            if association_id.strip():
                existing_association = await service.association_get(association_id)
            validated = req.Association.model_validate(
                _association_payload(
                    {
                        "id_": assoc_id,
                        "source_concept_iri": iri,
                        "target_concept_iri": target_iri,
                    },
                    existing_association=existing_association,
                )
            )
            association = de.Association.from_json_ld(validated.model_dump(by_alias=True))
            if existing_association:
                if existing_association.id_ != association.id_:
                    await service.association_create(association)
                    await service.association_delete(existing_association.id_)
                else:
                    await service.association_delete(existing_association.id_)
                    await service.association_create(association)
            else:
                await service.association_create(association)
        else:
            if association_id.strip():
                await service.association_delete(association_id)
            new_relationship = req.Relationship.model_validate(
                {"@id": iri, link_type: [{"@id": target_iri}]}
            )
            desired = de.Relationship.from_json_ld(new_relationship.model_dump(by_alias=True))
            if original_link_type and original_link_type != "association" and original_target_iri:
                await service.relationships_delete(
                    [
                        de.Relationship(
                            source=iri,
                            target=original_target_iri,
                            predicate=RelationshipVerbs(original_link_type),
                        )
                    ]
                )
            await service.relationships_create(desired)
    except (
        ValidationError,
        ValueError,
        de.DuplicateRelationship,
        de.HierarchicRelationshipAcrossConceptScheme,
        de.DuplicateIRI,
        de.AssociationNotFoundError,
    ) as exc:
        return RedirectResponse(
            str(request.url_for("admin_edit_concept", iri=quote(iri)))
            + "?"
            + urlencode(
                {
                    "language": language,
                    "concept_scheme": target_scheme,
                    "link_type": link_type,
                    "target_iri": target_iri,
                    "association_id": association_id,
                    "error": str(exc),
                }
            ),
            status_code=303,
        )

    return RedirectResponse(
        str(request.url_for("admin_edit_concept", iri=quote(iri)))
        + "?"
        + urlencode(
            {
                "language": language,
                "concept_scheme": target_scheme,
                "message": "Link saved",
            }
        ),
        status_code=303,
    )


@router.post("/concepts/{iri:path}/mappings/delete")
async def admin_delete_mapping(
    request: Request,
    iri: str = Path(...),
    csrf_token: str = Form(...),
    predicate: str = Form(...),
    target_iri: str = Form(...),
    language: str = Form("en"),
    concept_scheme: str | None = Form(None),
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)
    await service.relationships_delete(
        [
            de.Relationship(
                source=iri,
                target=target_iri,
                predicate=RelationshipVerbs(predicate),
            )
        ]
    )
    concept = await service.concept_get(iri)
    return RedirectResponse(
        str(request.url_for("admin_edit_concept", iri=quote(iri)))
        + "?"
        + urlencode(
            {
                "language": language,
                "concept_scheme": concept_scheme or concept.schemes[0]["@id"],
                "message": "Mapping deleted",
            }
        ),
        status_code=303,
    )


@router.post("/concepts/{iri:path}/relationships/delete", name="admin_delete_relationship")
async def admin_delete_relationship(
    request: Request,
    iri: str = Path(...),
    csrf_token: str = Form(...),
    source_iri: str = Form(...),
    predicate: str = Form(...),
    target_iri: str = Form(...),
    language: str = Form("en"),
    concept_scheme: str | None = Form(None),
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)
    await service.relationships_delete(
        [
            de.Relationship(
                source=source_iri,
                target=target_iri,
                predicate=RelationshipVerbs(predicate),
            )
        ]
    )
    concept = await service.concept_get(iri)
    return RedirectResponse(
        str(request.url_for("admin_edit_concept", iri=quote(iri)))
        + "?"
        + urlencode(
            {
                "language": language,
                "concept_scheme": concept_scheme or concept.schemes[0]["@id"],
                "message": "Relationship deleted",
            }
        ),
        status_code=303,
    )


@router.post("/concepts/{iri:path}/associations/new", response_class=HTMLResponse)
async def admin_create_association(
    request: Request,
    iri: str = Path(...),
    csrf_token: str = Form(...),
    id_: str = Form(...),
    source_concept_iri: str = Form(...),
    target_concept_iri: str = Form(...),
    language: str = Form("en"),
    concept_scheme: str | None = Form(None),
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)

    concept = await service.concept_get(iri)
    concept_schemes = await service.concept_scheme_get_all()
    relationships = await service.relationships_get(iri=iri, source=True, target=True)
    broader_iris = [
        rel.target
        for rel in relationships
        if rel.source == concept.id_ and rel.predicate == RelationshipVerbs.broader
    ]
    associations = await _concept_association_rows(
        request,
        concept_iri=concept.id_,
        language=language,
        concept_scheme=concept_scheme or concept.schemes[0]["@id"],
        service=service,
    )
    relationship_rows = await _concept_relationship_rows(
        request,
        concept_iri=concept.id_,
        language=language,
        concept_scheme=concept_scheme or concept.schemes[0]["@id"],
        service=service,
    )
    if not id_.strip():
        id_ = _generate_association_iri(source_concept_iri, target_concept_iri)
    assoc_form = {
        "id_": id_,
        "source_concept_iri": source_concept_iri,
        "target_concept_iri": target_concept_iri,
    }
    try:
        validated = req.Association.model_validate(_association_payload(assoc_form))
        association = de.Association.from_json_ld(validated.model_dump(by_alias=True))
        await service.association_create(association)
    except (ValidationError, ValueError, de.DuplicateIRI) as exc:
        return _render_concept_form(
            request,
            language=language,
            settings=settings,
            admin_user=admin_user,
            form_data=_concept_form_data_for_language(
                concept,
                language=language,
                scheme_hint=concept_scheme or concept.schemes[0]["@id"],
                broader_iris=broader_iris,
            ),
            concept_schemes=concept_schemes,
            relationship_rows=relationship_rows,
            associations=associations,
            association_form_data=assoc_form,
            concept_form_action=str(request.url_for("admin_update_concept", iri=quote(concept.id_))),
            association_form_action=str(
                request.url_for("admin_create_association", iri=quote(concept.id_))
            ),
            form_mode="edit",
            error=str(exc),
        )

    return RedirectResponse(
        str(request.url_for("admin_edit_concept", iri=quote(iri)))
        + "?"
        + urlencode(
            {
                "language": language,
                "concept_scheme": concept_scheme or concept.schemes[0]["@id"],
                "message": "Association created",
            }
        ),
        status_code=303,
    )


@router.get("/associations/{iri:path}/edit", response_class=HTMLResponse, name="admin_edit_association")
async def admin_edit_association(
    request: Request,
    iri: str = Path(...),
    source_concept: str = "",
    language: str | None = None,
    concept_scheme: str | None = None,
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user

    language = _default_language(language, settings)
    concept = await service.concept_get(source_concept)
    association = await service.association_get(iri)
    concept_schemes = await service.concept_scheme_get_all()
    relationships = await service.relationships_get(iri=source_concept, source=True, target=True)
    broader_iris = [
        rel.target
        for rel in relationships
        if rel.source == concept.id_ and rel.predicate == RelationshipVerbs.broader
    ]
    associations = await _concept_association_rows(
        request,
        concept_iri=concept.id_,
        language=language,
        concept_scheme=concept_scheme or concept.schemes[0]["@id"],
        service=service,
    )
    relationship_rows = await _concept_relationship_rows(
        request,
        concept_iri=concept.id_,
        language=language,
        concept_scheme=concept_scheme or concept.schemes[0]["@id"],
        service=service,
    )
    return _render_concept_form(
        request,
        language=language,
        settings=settings,
        admin_user=admin_user,
        form_data=_concept_form_data_for_language(
            concept,
            language=language,
            scheme_hint=concept_scheme or concept.schemes[0]["@id"],
            broader_iris=broader_iris,
        ),
        concept_schemes=concept_schemes,
        relationship_rows=relationship_rows,
        associations=associations,
        association_form_data=_association_form_data(association, source_concept_iri=concept.id_),
        concept_form_action=str(request.url_for("admin_update_concept", iri=quote(concept.id_))),
        association_form_action=str(request.url_for("admin_update_association", iri=quote(association.id_))),
        form_mode="edit",
        message="Editing association",
    )


@router.post("/associations/{iri:path}/edit", response_class=HTMLResponse)
async def admin_update_association(
    request: Request,
    iri: str = Path(...),
    csrf_token: str = Form(...),
    id_: str = Form(...),
    source_concept_iri: str = Form(...),
    target_concept_iri: str = Form(...),
    language: str = Form("en"),
    concept_scheme: str | None = Form(None),
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)

    concept = await service.concept_get(source_concept_iri)
    current = await service.association_get(iri)
    concept_schemes = await service.concept_scheme_get_all()
    relationships = await service.relationships_get(iri=source_concept_iri, source=True, target=True)
    broader_iris = [
        rel.target
        for rel in relationships
        if rel.source == concept.id_ and rel.predicate == RelationshipVerbs.broader
    ]
    associations = await _concept_association_rows(
        request,
        concept_iri=concept.id_,
        language=language,
        concept_scheme=concept_scheme or concept.schemes[0]["@id"],
        service=service,
    )
    relationship_rows = await _concept_relationship_rows(
        request,
        concept_iri=concept.id_,
        language=language,
        concept_scheme=concept_scheme or concept.schemes[0]["@id"],
        service=service,
    )
    if not id_.strip():
        id_ = _generate_association_iri(source_concept_iri, target_concept_iri)
    assoc_form = {
        "id_": id_,
        "source_concept_iri": source_concept_iri,
        "target_concept_iri": target_concept_iri,
    }
    try:
        validated = req.Association.model_validate(
            _association_payload(assoc_form, existing_association=current)
        )
        association = de.Association.from_json_ld(validated.model_dump(by_alias=True))
        if current.id_ != association.id_:
            await service.association_create(association)
            await service.association_delete(current.id_)
        else:
            await service.association_delete(current.id_)
            await service.association_create(association)
    except (ValidationError, ValueError, de.DuplicateIRI, de.AssociationNotFoundError) as exc:
        return _render_concept_form(
            request,
            language=language,
            settings=settings,
            admin_user=admin_user,
            form_data=_concept_form_data_for_language(
                concept,
                language=language,
                scheme_hint=concept_scheme or concept.schemes[0]["@id"],
                broader_iris=broader_iris,
            ),
            concept_schemes=concept_schemes,
            relationship_rows=relationship_rows,
            associations=associations,
            association_form_data=assoc_form,
            concept_form_action=str(request.url_for("admin_update_concept", iri=quote(concept.id_))),
            association_form_action=str(request.url_for("admin_update_association", iri=quote(iri))),
            form_mode="edit",
            error=str(exc),
        )

    return RedirectResponse(
        str(request.url_for("admin_edit_concept", iri=quote(source_concept_iri)))
        + "?"
        + urlencode(
            {
                "language": language,
                "concept_scheme": concept_scheme or concept.schemes[0]["@id"],
                "message": "Association updated",
            }
        ),
        status_code=303,
    )


@router.post("/associations/{iri:path}/delete")
async def admin_delete_association(
    request: Request,
    iri: str = Path(...),
    csrf_token: str = Form(...),
    source_concept_iri: str = Form(...),
    language: str = Form("en"),
    concept_scheme: str | None = Form(None),
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    admin_user = _ensure_admin(request, language, settings)
    if isinstance(admin_user, RedirectResponse):
        return admin_user
    _validate_csrf(request, csrf_token)
    await service.association_delete(iri)
    concept = await service.concept_get(source_concept_iri)
    return RedirectResponse(
        str(request.url_for("admin_edit_concept", iri=quote(source_concept_iri)))
        + "?"
        + urlencode(
            {
                "language": language,
                "concept_scheme": concept_scheme or concept.schemes[0]["@id"],
                "message": "Association deleted",
            }
        ),
        status_code=303,
    )
