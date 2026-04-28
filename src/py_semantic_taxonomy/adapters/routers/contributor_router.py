import csv
import io
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, urlencode

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from py_semantic_taxonomy.adapters.routers.admin_router import (
    _base_context,
    _build_concept_form_data,
    _build_concept_scheme_form_data,
    _concept_association_rows,
    _concept_form_data_for_language,
    _concept_mapping_rows,
    _concept_payload,
    _concept_relationship_rows,
    _concept_scheme_form_data_for_language,
    _concept_scheme_payload,
    _default_language,
    _exchange_code_for_token,
    _gitlab_user,
    _mapping_form_data,
    _modified_extra,
    _parse_nodes,
    _language_selector,
    _public_url_for,
    STATUS_OPTIONS,
)
from py_semantic_taxonomy.adapters.routers import request_dto as req
from py_semantic_taxonomy.adapters.routers.web_router import templates
from py_semantic_taxonomy.cfg import Settings, get_settings
from py_semantic_taxonomy.dependencies import get_claim_store, get_graph_service
from py_semantic_taxonomy.domain import entities as de
from py_semantic_taxonomy.domain.constants import RelationshipVerbs
from py_semantic_taxonomy.domain.url_utils import get_full_api_path
from pydantic import ValidationError

router = APIRouter(prefix="/web/contributor", include_in_schema=False)

CLAIM_KINDS = [
    ("add_concept_scheme", "Add concept scheme"),
    ("add_concept", "Add concept"),
    ("edit_concept", "Edit concept"),
    ("add_relationship", "Add relationship"),
    ("edit_concept_scheme", "Edit concept scheme"),
    ("deprecate_concept", "Deprecate concept"),
    ("bulk_tree_import", "Bulk tree import"),
    ("bulk_concordance_import", "Bulk concordance import"),
    ("other", "Other"),
]

RELATIONSHIP_PREDICATE_OPTIONS = [
    (RelationshipVerbs.broader, "broader"),
    (RelationshipVerbs.narrower, "narrower"),
    (RelationshipVerbs.exact_match, "exactMatch"),
    (RelationshipVerbs.close_match, "closeMatch"),
    (RelationshipVerbs.broad_match, "broadMatch"),
    (RelationshipVerbs.narrow_match, "narrowMatch"),
    (RelationshipVerbs.related_match, "relatedMatch"),
]

CSV_IMPORT_EXAMPLES = {
    "bulk_tree_import": "code,parent_code,name,level\nROOT,,Root node,0\nCHILD,ROOT,Child node,1",
    "bulk_concordance_import": (
        "activitytype_from,activitytype_to,classification_from,classification_to,comment,skos_uri\n"
        "A_IRON,ai_0710,bonsut,bonsai,ambiguous one-to-many correspondence,"
        "http://www.w3.org/2004/02/skos/core#narrowMatch"
    ),
}


def _blank_claim_form_data(target_iri: str = "") -> dict[str, Any]:
    return {
        "kind": CLAIM_KINDS[0][0],
        "title": "",
        "target_iri": target_iri,
        "rationale": "",
        "payload": "",
        "concept_iri": target_iri,
        "scheme_iri": "",
        "concept_label": "",
        "concept_language": "en",
        "concept_notation": "",
        "concept_definition": "",
        "broader_iri": "",
        "relationship_source_iri": target_iri,
        "relationship_target_iri": "",
        "relationship_predicate": str(RelationshipVerbs.broader),
        "scheme_label": "",
        "scheme_notation": "",
        "scheme_definition": "",
        "scheme_version": "",
        "replacement_iri": "",
        "deprecation_note": "",
        "csv_text": "",
        "csv_import_name": "",
        "csv_file_name": "",
    }


def _normalize_claim_form_data(form_data: dict[str, Any]) -> dict[str, Any]:
    normalized = _blank_claim_form_data(form_data.get("target_iri", ""))
    normalized.update(form_data)
    return normalized


def _read_csv_upload(upload: UploadFile | None) -> tuple[str, str]:
    if not upload or not upload.filename:
        return "", ""
    raw = upload.file.read()
    try:
        return raw.decode("utf-8-sig"), upload.filename
    except UnicodeDecodeError as exc:
        raise ValueError("CSV files must use UTF-8 encoding") from exc


def _parse_csv_rows(csv_text: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError("CSV data must include a header row")

    columns = [col.strip() for col in reader.fieldnames if col and col.strip()]
    if not columns:
        raise ValueError("CSV header row is empty")

    rows: list[dict[str, str]] = []
    for idx, row in enumerate(reader, start=2):
        cleaned = {str(key).strip(): (value or "").strip() for key, value in row.items() if key}
        if not any(cleaned.values()):
            continue
        rows.append(cleaned)

    if not rows:
        raise ValueError("CSV data must include at least one data row")
    return columns, rows


def _guided_change_from_form(kind: str, form_data: dict[str, Any]) -> dict[str, Any]:
    if kind in {"add_concept", "edit_concept"}:
        return {
            "entity_type": "concept",
            "operation": "create" if kind == "add_concept" else "update",
            "concept": {
                "iri": form_data["concept_iri"].strip(),
                "scheme_iri": form_data["scheme_iri"].strip(),
                "pref_label": {
                    "language": form_data["concept_language"].strip() or "en",
                    "value": form_data["concept_label"].strip(),
                },
                "notation": form_data["concept_notation"].strip(),
                "definition": form_data["concept_definition"].strip(),
            },
            "broader_iri": form_data["broader_iri"].strip(),
        }
    if kind == "add_relationship":
        return {
            "entity_type": "relationship",
            "operation": "create",
            "relationship": {
                "source_iri": form_data["relationship_source_iri"].strip(),
                "target_iri": form_data["relationship_target_iri"].strip(),
                "predicate": form_data["relationship_predicate"].strip(),
            },
        }
    if kind == "edit_concept_scheme":
        return {
            "entity_type": "concept_scheme",
            "operation": "update",
            "concept_scheme": {
                "iri": form_data["target_iri"].strip() or form_data["scheme_iri"].strip(),
                "pref_label": form_data["scheme_label"].strip(),
                "notation": form_data["scheme_notation"].strip(),
                "definition": form_data["scheme_definition"].strip(),
                "version": form_data["scheme_version"].strip(),
            },
        }
    if kind == "deprecate_concept":
        return {
            "entity_type": "concept",
            "operation": "deprecate",
            "concept": {
                "iri": form_data["target_iri"].strip() or form_data["concept_iri"].strip(),
                "replacement_iri": form_data["replacement_iri"].strip(),
                "note": form_data["deprecation_note"].strip(),
            },
        }
    return {}


def _csv_change_from_form(
    kind: str,
    *,
    csv_text: str,
    csv_file_name: str,
    import_name: str,
) -> dict[str, Any]:
    columns, rows = _parse_csv_rows(csv_text)
    return {
        "entity_type": "csv_import",
        "import_kind": "tree" if kind == "bulk_tree_import" else "concordance",
        "import_name": import_name.strip(),
        "file_name": csv_file_name,
        "columns": columns,
        "rows": rows,
    }


def _build_claim_payload(
    kind: str,
    *,
    rationale: str,
    form_data: dict[str, Any],
    payload_text: str,
    csv_text: str,
    csv_file_name: str,
    csv_import_name: str,
) -> tuple[dict[str, Any], str]:
    rationale = rationale.strip()
    payload_text = payload_text.strip()

    if kind in {"bulk_tree_import", "bulk_concordance_import"}:
        change = _csv_change_from_form(
            kind,
            csv_text=csv_text,
            csv_file_name=csv_file_name,
            import_name=csv_import_name,
        )
        mode = "csv"
    elif payload_text:
        raise ValueError("Raw JSON claim submission is no longer supported; use the shared forms")
    else:
        change = _guided_change_from_form(kind, form_data)
        if not change:
            raise ValueError("Provide structured claim details or advanced JSON")
        mode = "guided"

    return (
        {
            "rationale": rationale,
            "submission": {
                "mode": mode,
                "kind": kind,
            },
            "change": change,
        },
        mode,
    )


def _claim_payload_preview(payload: dict[str, Any]) -> dict[str, Any]:
    submission = payload.get("submission", {}) if isinstance(payload, dict) else {}
    change = payload.get("change", {}) if isinstance(payload, dict) else {}
    rows = change.get("rows", []) if isinstance(change, dict) else []
    columns = change.get("columns", []) if isinstance(change, dict) else []
    return {
        "rationale": payload.get("rationale", "") if isinstance(payload, dict) else "",
        "submission": submission if isinstance(submission, dict) else {},
        "change": change if isinstance(change, dict) else {},
        "change_json": json.dumps(change if isinstance(change, dict) else {}, indent=2),
        "csv_columns": columns if isinstance(columns, list) else [],
        "csv_rows_preview": rows[:5] if isinstance(rows, list) else [],
        "csv_row_count": len(rows) if isinstance(rows, list) else 0,
    }


def _contributor_configured(settings: Settings) -> bool:
    return all(
        value and value != "missing"
        for value in (
            settings.gitlab_url,
            settings.gitlab_client_id,
            settings.gitlab_client_secret,
            settings.gitlab_contributor_group,
        )
    )


def _backend_configured(settings: Settings) -> bool:
    return bool(
        settings.contributor_backend_base_url
        and settings.contributor_backend_base_url != "missing"
    )


def _backend_url(settings: Settings, path: str) -> str:
    return settings.contributor_backend_base_url.rstrip("/") + path


def _contributor_redirect(request: Request, language: str) -> RedirectResponse:
    return RedirectResponse(
        str(request.url_for("contributor_login")) + "?" + urlencode({"language": language}),
        status_code=303,
    )


def _ensure_contributor(
    request: Request, language: str | None, settings: Settings
) -> dict[str, Any] | RedirectResponse:
    contributor_user = request.session.get("contributor_user")
    if contributor_user:
        return contributor_user
    return _contributor_redirect(request, _default_language(language, settings))


def _ensure_contributor_csrf_token(request: Request) -> str:
    csrf_token = request.session.get("contributor_csrf_token")
    if not csrf_token:
        csrf_token = quote(datetime.now(tz=timezone.utc).isoformat(), safe="")
        request.session["contributor_csrf_token"] = csrf_token
    return csrf_token


def _validate_contributor_csrf(request: Request, csrf_token: str) -> None:
    if csrf_token != request.session.get("contributor_csrf_token"):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


async def _gitlab_group_member(
    *,
    group: str,
    min_access_level: int,
    user_id: int,
    access_token: str,
    settings: Settings,
) -> bool:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.gitlab_url.rstrip('/')}/api/v4/groups/"
            f"{quote(group, safe='')}/members/all/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if response.status_code == 404:
        return False
    response.raise_for_status()
    member = response.json()
    return member.get("access_level", 0) >= min_access_level


def _backend_user_from_payload(
    payload: dict[str, Any],
    *,
    fallback_email: str | None = None,
) -> dict[str, Any]:
    user = payload.get("user") if isinstance(payload.get("user"), dict) else payload
    email = user.get("email") or fallback_email
    username = user.get("username") or user.get("name") or email or str(user.get("id", "backend-user"))
    return {
        "provider": "backend",
        "id": str(user.get("id") or user.get("sub") or email or username),
        "username": username,
        "name": user.get("name") or username or "Contributor",
        "email": email,
    }


def _render_contributor_dashboard(
    request: Request,
    *,
    language: str,
    settings: Settings,
    contributor_user: dict[str, Any],
    claims: list[dict[str, Any]],
    message: str | None = None,
    error: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "contributor_dashboard.html",
        context=_base_context(
            request,
            language,
            settings,
            contributor_user=contributor_user,
            claims=claims,
            csrf_token=_ensure_contributor_csrf_token(request),
            message=message,
            error=error,
            gitlab_contributor_group=settings.gitlab_contributor_group,
        ),
    )


def _render_shared_concept_scheme_form(
    request: Request,
    *,
    language: str,
    settings: Settings,
    contributor_user: dict[str, Any],
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
            contributor_user=contributor_user,
            csrf_token=_ensure_contributor_csrf_token(request),
            form_data=form_data,
            form_mode=form_mode,
            status_options=STATUS_OPTIONS,
            actor_label="Contributor",
            actor_home_url=f"/web/contributor/?language={language}",
            actor_home_name="Contributor",
            submit_label=(
                "Submit Scheme Claim" if form_mode == "create" else "Submit Change Claim"
            ),
            show_delete_actions=False,
            collect_rationale=True,
            form_helper_text=(
                "This is the same editing form used by admins, but submitting it creates a claim for review."
            ),
            message=message,
            error=error,
        ),
    )


def _render_shared_concept_form(
    request: Request,
    *,
    language: str,
    settings: Settings,
    contributor_user: dict[str, Any],
    form_data: dict[str, Any],
    concept_schemes: list[de.ConceptScheme],
    form_mode: str,
    relationship_rows: list[dict[str, Any]] | None = None,
    mappings: list[dict[str, Any]] | None = None,
    mapping_form_data: dict[str, Any] | None = None,
    associations: list[dict[str, Any]] | None = None,
    mapping_form_action: str | None = None,
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
            contributor_user=contributor_user,
            csrf_token=_ensure_contributor_csrf_token(request),
            form_data=form_data,
            concept_schemes=concept_schemes,
            relationship_rows=relationship_rows or [],
            mappings=mappings or [],
            mapping_form_data=mapping_form_data,
            associations=associations or [],
            association_form_data=None,
            concept_form_action=request.url.path,
            mapping_form_action=mapping_form_action,
            association_form_action=None,
            form_mode=form_mode,
            status_options=STATUS_OPTIONS,
            mapping_verbs=[verb for verb, _label in RELATIONSHIP_PREDICATE_OPTIONS if verb in {
                RelationshipVerbs.exact_match,
                RelationshipVerbs.close_match,
                RelationshipVerbs.broad_match,
                RelationshipVerbs.narrow_match,
                RelationshipVerbs.related_match,
            }],
            actor_label="Contributor",
            actor_home_url=f"/web/contributor/?language={language}",
            actor_home_name="Contributor",
            submit_label=(
                "Submit Concept Claim" if form_mode == "create" else "Submit Change Claim"
            ),
            show_delete_actions=False,
            show_direct_link_actions=False,
            show_mapping_form=form_mode == "edit",
            collect_rationale=True,
            form_helper_text=(
                "This is the same editing form used by admins, but submitting it creates a claim for review."
            ),
            message=message,
            error=error,
        ),
    )


def _render_csv_import_form(
    request: Request,
    *,
    language: str,
    settings: Settings,
    contributor_user: dict[str, Any],
    form_data: dict[str, Any],
    error: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "contributor_claim_form.html",
        context=_base_context(
            request,
            language,
            settings,
            contributor_user=contributor_user,
            csrf_token=_ensure_contributor_csrf_token(request),
            claim_kinds=[("bulk_tree_import", "Bulk tree import"), ("bulk_concordance_import", "Bulk concordance import")],
            form_data=_normalize_claim_form_data(form_data),
            relationship_predicates=RELATIONSHIP_PREDICATE_OPTIONS,
            csv_import_examples=CSV_IMPORT_EXAMPLES,
            error=error,
        ),
    )


async def _submit_claim(
    *,
    claim_store,
    kind: str,
    title: str,
    target_iri: str,
    rationale: str,
    contributor_user: dict[str, Any],
    change: dict[str, Any],
) -> None:
    await claim_store.create(
        kind=kind,
        title=title.strip(),
        target_iri=target_iri.strip(),
        payload={
            "rationale": rationale.strip(),
            "submission": {"mode": "shared_ui", "kind": kind},
            "change": change,
        },
        submitted_by=contributor_user,
    )


@router.get("/login", name="contributor_login")
async def contributor_login(
    request: Request,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
):
    language = _default_language(language, settings)
    if request.session.get("contributor_user"):
        return RedirectResponse(
            str(request.url_for("contributor_dashboard")) + "?" + urlencode({"language": language}),
            status_code=303,
        )
    if not _contributor_configured(settings) and not _backend_configured(settings):
        raise HTTPException(
            status_code=503, detail="Contributor authentication is not configured"
        )

    return templates.TemplateResponse(
        request,
        "contributor_login.html",
        context=_base_context(
            request,
            language,
            settings,
            csrf_token=_ensure_contributor_csrf_token(request),
            gitlab_configured=_contributor_configured(settings),
            backend_configured=_backend_configured(settings),
            backend_name=settings.contributor_backend_name,
            error=request.query_params.get("error"),
        ),
    )


@router.get("/gitlab/login", name="contributor_gitlab_login")
async def contributor_gitlab_login(
    request: Request,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
):
    language = _default_language(language, settings)
    if not _contributor_configured(settings):
        raise HTTPException(
            status_code=503, detail="GitLab contributor authentication is not configured"
        )

    state = quote(datetime.now(tz=timezone.utc).isoformat(), safe="")
    request.session["gitlab_contributor_oauth_state"] = state
    redirect_uri = _public_url_for(request, "contributor_gitlab_callback", settings)
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


@router.get("/backend/login", name="contributor_backend_login")
async def contributor_backend_login(
    request: Request,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
):
    if not _backend_configured(settings):
        raise HTTPException(status_code=503, detail="Contributor backend is not configured")

    next_url = _public_url_for(request, "contributor_backend_callback", settings)
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            _backend_url(settings, "/api/user/auth/gitlab/login/"),
            json={"next": next_url},
        )
    response.raise_for_status()
    payload = response.json()
    authorization_url = payload.get("authorization_url") or payload.get("next")
    if not authorization_url:
        raise HTTPException(
            status_code=502,
            detail="Contributor backend did not return an authorization URL",
        )
    return RedirectResponse(authorization_url, status_code=303)


@router.get("/backend/callback", name="contributor_backend_callback")
async def contributor_backend_callback(
    request: Request,
    code: str | None = None,
    handoff_code: str | None = None,
    error: str | None = None,
    settings: Settings = Depends(get_settings),
):
    if error:
        raise HTTPException(status_code=403, detail=error)
    if not _backend_configured(settings):
        raise HTTPException(status_code=503, detail="Contributor backend is not configured")

    exchange_code = code or handoff_code or request.query_params.get("handoff")
    if not exchange_code:
        raise HTTPException(status_code=400, detail="Missing backend handoff code")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            _backend_url(settings, "/api/user/auth/exchange/"),
            json={"code": exchange_code},
        )
    response.raise_for_status()
    request.session["contributor_user"] = _backend_user_from_payload(response.json())
    return RedirectResponse(str(request.url_for("contributor_dashboard")), status_code=303)


@router.post("/backend/token-login", name="contributor_backend_token_login")
async def contributor_backend_token_login(
    request: Request,
    csrf_token: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    language: str = Form("en"),
    settings: Settings = Depends(get_settings),
):
    if not _backend_configured(settings):
        raise HTTPException(status_code=503, detail="Contributor backend is not configured")
    _validate_contributor_csrf(request, csrf_token)

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            _backend_url(settings, "/api/user/token/"),
            json={"email": email, "password": password},
        )
    if response.status_code >= 400:
        return RedirectResponse(
            str(request.url_for("contributor_login"))
            + "?"
            + urlencode({"language": language, "error": "Backend login failed"}),
            status_code=303,
        )

    request.session["contributor_user"] = _backend_user_from_payload(
        response.json(),
        fallback_email=email,
    )
    return RedirectResponse(
        str(request.url_for("contributor_dashboard")) + "?" + urlencode({"language": language}),
        status_code=303,
    )


@router.get("/callback", name="contributor_gitlab_callback")
async def contributor_gitlab_callback(
    request: Request,
    code: str,
    state: str,
    settings: Settings = Depends(get_settings),
):
    if not _contributor_configured(settings):
        raise HTTPException(
            status_code=503, detail="GitLab contributor authentication is not configured"
        )
    if state != request.session.get("gitlab_contributor_oauth_state"):
        raise HTTPException(status_code=400, detail="Invalid GitLab OAuth state")

    redirect_uri = _public_url_for(request, "contributor_gitlab_callback", settings)
    token = await _exchange_code_for_token(code, redirect_uri, settings)
    access_token = token["access_token"]
    user = await _gitlab_user(access_token, settings)
    is_group_member = await _gitlab_group_member(
        group=settings.gitlab_contributor_group,
        min_access_level=settings.gitlab_contributor_min_access_level,
        user_id=user["id"],
        access_token=access_token,
        settings=settings,
    )
    if not is_group_member:
        raise HTTPException(
            status_code=403,
            detail=(
                "GitLab user is not in the configured contributor group with the required "
                "access level"
            ),
        )

    request.session.pop("gitlab_contributor_oauth_state", None)
    request.session["contributor_user"] = {
        "id": user["id"],
        "username": user.get("username"),
        "name": user.get("name") or user.get("username") or "Contributor",
    }
    return RedirectResponse(str(request.url_for("contributor_dashboard")), status_code=303)


@router.post("/logout")
async def contributor_logout(
    request: Request,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
):
    for key in (
        "contributor_user",
        "contributor_csrf_token",
        "gitlab_contributor_oauth_state",
    ):
        request.session.pop(key, None)
    return RedirectResponse(
        str(request.url_for("web_concept_schemes"))
        + "?"
        + urlencode({"language": _default_language(language, settings)}),
        status_code=303,
    )


@router.get("/", response_class=HTMLResponse, name="contributor_dashboard")
async def contributor_dashboard(
    request: Request,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
    claim_store=Depends(get_claim_store),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user

    language = _default_language(language, settings)
    claims = await claim_store.get_all(submitted_by_id=contributor_user["id"])
    return _render_contributor_dashboard(
        request,
        language=language,
        settings=settings,
        contributor_user=contributor_user,
        claims=claims,
        message=request.query_params.get("message"),
        error=request.query_params.get("error"),
    )


@router.get("/claims/new", response_class=HTMLResponse, name="contributor_new_claim")
async def contributor_new_claim(
    request: Request,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    return RedirectResponse(
        str(request.url_for("contributor_dashboard"))
        + "?"
        + urlencode(
            {
                "language": _default_language(language, settings),
                "message": "Use the guided contributor forms instead of the old generic claim form",
            }
        ),
        status_code=303,
    )


@router.get("/concept_schemes/new", response_class=HTMLResponse, name="contributor_new_concept_scheme")
async def contributor_new_concept_scheme(
    request: Request,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    language = _default_language(language, settings)
    form_data = _concept_scheme_form_data_for_language(None, language=language)
    form_data["rationale"] = ""
    return _render_shared_concept_scheme_form(
        request,
        language=language,
        settings=settings,
        contributor_user=contributor_user,
        form_data=form_data,
        form_mode="create",
    )


@router.post("/concept_schemes/new", response_class=HTMLResponse)
async def contributor_create_concept_scheme_claim(
    request: Request,
    csrf_token: str = Form(...),
    rationale: str = Form(""),
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
    claim_store=Depends(get_claim_store),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    _validate_contributor_csrf(request, csrf_token)
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
    form_data["rationale"] = rationale
    try:
        payload = _concept_scheme_payload(form_data)
        validated = req.ConceptScheme.model_validate(payload)
        await _submit_claim(
            claim_store=claim_store,
            kind="add_concept_scheme",
            title=f"Create concept scheme: {pref_label_text.strip() or id_.strip()}",
            target_iri=id_,
            rationale=rationale,
            contributor_user=contributor_user,
            change={
                "entity_type": "concept_scheme",
                "operation": "create",
                "payload": validated.model_dump(by_alias=True),
            },
        )
    except (ValidationError, ValueError) as exc:
        return _render_shared_concept_scheme_form(
            request,
            language=language,
            settings=settings,
            contributor_user=contributor_user,
            form_data=form_data,
            form_mode="create",
            error=str(exc),
        )
    return RedirectResponse(
        str(request.url_for("contributor_dashboard"))
        + "?"
        + urlencode({"language": language, "message": "Concept scheme claim submitted for admin review"}),
        status_code=303,
    )


@router.get("/concept_schemes/{iri:path}/edit", response_class=HTMLResponse, name="contributor_edit_concept_scheme")
async def contributor_edit_concept_scheme(
    request: Request,
    iri: str,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    language = _default_language(language, settings)
    concept_scheme = await service.concept_scheme_get(iri)
    form_data = _concept_scheme_form_data_for_language(concept_scheme, language=language)
    form_data["rationale"] = ""
    return _render_shared_concept_scheme_form(
        request,
        language=language,
        settings=settings,
        contributor_user=contributor_user,
        form_data=form_data,
        form_mode="edit",
    )


@router.post("/concept_schemes/{iri:path}/edit", response_class=HTMLResponse)
async def contributor_update_concept_scheme_claim(
    request: Request,
    iri: str,
    csrf_token: str = Form(...),
    rationale: str = Form(""),
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
    claim_store=Depends(get_claim_store),
    service=Depends(get_graph_service),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    _validate_contributor_csrf(request, csrf_token)
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
    form_data["rationale"] = rationale
    try:
        payload = _concept_scheme_payload(form_data, extra=_modified_extra(current.extra))
        validated = req.ConceptScheme.model_validate(payload)
        await _submit_claim(
            claim_store=claim_store,
            kind="edit_concept_scheme",
            title=f"Edit concept scheme: {pref_label_text.strip() or id_.strip()}",
            target_iri=id_,
            rationale=rationale,
            contributor_user=contributor_user,
            change={
                "entity_type": "concept_scheme",
                "operation": "update",
                "payload": validated.model_dump(by_alias=True),
            },
        )
    except (ValidationError, ValueError) as exc:
        return _render_shared_concept_scheme_form(
            request,
            language=language,
            settings=settings,
            contributor_user=contributor_user,
            form_data=form_data,
            form_mode="edit",
            error=str(exc),
        )
    return RedirectResponse(
        str(request.url_for("contributor_dashboard"))
        + "?"
        + urlencode({"language": language, "message": "Concept scheme change claim submitted"}),
        status_code=303,
    )


@router.get("/concepts/new", response_class=HTMLResponse, name="contributor_new_concept")
async def contributor_new_concept(
    request: Request,
    concept_scheme: str | None = None,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    language = _default_language(language, settings)
    concept_schemes = await service.concept_scheme_get_all()
    form_data = _concept_form_data_for_language(None, language=language, scheme_hint=concept_scheme or "")
    form_data["rationale"] = ""
    return _render_shared_concept_form(
        request,
        language=language,
        settings=settings,
        contributor_user=contributor_user,
        form_data=form_data,
        concept_schemes=concept_schemes,
        form_mode="create",
    )


@router.post("/concepts/new", response_class=HTMLResponse)
async def contributor_create_concept_claim(
    request: Request,
    csrf_token: str = Form(...),
    rationale: str = Form(""),
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
    claim_store=Depends(get_claim_store),
    service=Depends(get_graph_service),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    _validate_contributor_csrf(request, csrf_token)
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
    form_data["rationale"] = rationale
    try:
        payload = _concept_payload(form_data)
        if top_concept and _parse_nodes(broader_iris):
            raise ValueError("A top concept cannot also have broader concepts")
        validated = req.ConceptCreate.model_validate(
            {**payload, str(RelationshipVerbs.broader): _parse_nodes(broader_iris)}
        )
        await _submit_claim(
            claim_store=claim_store,
            kind="add_concept",
            title=f"Create concept: {pref_label_text.strip() or id_.strip()}",
            target_iri=id_,
            rationale=rationale,
            contributor_user=contributor_user,
            change={
                "entity_type": "concept",
                "operation": "create",
                "payload": validated.model_dump(by_alias=True),
            },
        )
    except (ValidationError, ValueError, de.ConceptSchemesNotInDatabase) as exc:
        return _render_shared_concept_form(
            request,
            language=language,
            settings=settings,
            contributor_user=contributor_user,
            form_data=form_data,
            concept_schemes=concept_schemes,
            form_mode="create",
            error=str(exc),
        )
    return RedirectResponse(
        str(request.url_for("contributor_dashboard"))
        + "?"
        + urlencode({"language": language, "message": "Concept claim submitted for admin review"}),
        status_code=303,
    )


@router.get("/concepts/{iri:path}/edit", response_class=HTMLResponse, name="contributor_edit_concept")
async def contributor_edit_concept(
    request: Request,
    iri: str,
    concept_scheme: str | None = None,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
    service=Depends(get_graph_service),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    language = _default_language(language, settings)
    concept = await service.concept_get(iri)
    relationships = await service.relationships_get(iri=iri, source=True, target=True)
    broader_iris = [
        rel.target for rel in relationships
        if rel.source == concept.id_ and rel.predicate == RelationshipVerbs.broader
    ]
    concept_schemes = await service.concept_scheme_get_all()
    selected_scheme = concept_scheme or concept.schemes[0]["@id"]
    relationship_rows = await _concept_relationship_rows(
        request, concept_iri=concept.id_, language=language, concept_scheme=selected_scheme, service=service
    )
    associations = await _concept_association_rows(
        request, concept_iri=concept.id_, language=language, concept_scheme=selected_scheme, service=service
    )
    mappings = await _concept_mapping_rows(
        request, concept_iri=concept.id_, language=language, concept_scheme=selected_scheme, service=service
    )
    form_data = _concept_form_data_for_language(
        concept, language=language, scheme_hint=selected_scheme, broader_iris=broader_iris
    )
    form_data["rationale"] = ""
    return _render_shared_concept_form(
        request,
        language=language,
        settings=settings,
        contributor_user=contributor_user,
        form_data=form_data,
        concept_schemes=concept_schemes,
        form_mode="edit",
        relationship_rows=relationship_rows,
        mappings=mappings,
        associations=associations,
        mapping_form_data=_mapping_form_data(
            link_type=request.query_params.get("link_type", str(RelationshipVerbs.exact_match)),
            target_iri=request.query_params.get("target_iri", ""),
            association_id=request.query_params.get("association_id", ""),
        ),
        mapping_form_action=str(request.url_for("contributor_create_link_claim", iri=quote(concept.id_))),
    )


@router.post("/concepts/{iri:path}/edit", response_class=HTMLResponse)
async def contributor_update_concept_claim(
    request: Request,
    iri: str,
    csrf_token: str = Form(...),
    rationale: str = Form(""),
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
    claim_store=Depends(get_claim_store),
    service=Depends(get_graph_service),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    _validate_contributor_csrf(request, csrf_token)
    current = await service.concept_get(iri)
    concept_schemes = await service.concept_scheme_get_all()
    selected_scheme = concept_scheme or current.schemes[0]["@id"]
    relationship_rows = await _concept_relationship_rows(
        request, concept_iri=current.id_, language=language, concept_scheme=selected_scheme, service=service
    )
    associations = await _concept_association_rows(
        request, concept_iri=current.id_, language=language, concept_scheme=selected_scheme, service=service
    )
    mappings = await _concept_mapping_rows(
        request, concept_iri=current.id_, language=language, concept_scheme=selected_scheme, service=service
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
    form_data["rationale"] = rationale
    try:
        payload = _concept_payload(form_data, extra=_modified_extra(current.extra))
        if top_concept and _parse_nodes(broader_iris):
            raise ValueError("A top concept cannot also have broader concepts")
        validated = req.ConceptUpdate.model_validate(payload)
        await _submit_claim(
            claim_store=claim_store,
            kind="edit_concept",
            title=f"Edit concept: {pref_label_text.strip() or id_.strip()}",
            target_iri=id_,
            rationale=rationale,
            contributor_user=contributor_user,
            change={
                "entity_type": "concept",
                "operation": "update",
                "payload": validated.model_dump(by_alias=True),
                "broader_iris": [node["@id"] for node in _parse_nodes(broader_iris)],
            },
        )
    except (ValidationError, ValueError, de.ConceptNotFoundError) as exc:
        return _render_shared_concept_form(
            request,
            language=language,
            settings=settings,
            contributor_user=contributor_user,
            form_data=form_data,
            concept_schemes=concept_schemes,
            form_mode="edit",
            relationship_rows=relationship_rows,
            mappings=mappings,
            associations=associations,
            mapping_form_data=_mapping_form_data(),
            mapping_form_action=str(request.url_for("contributor_create_link_claim", iri=quote(current.id_))),
            error=str(exc),
        )
    return RedirectResponse(
        str(request.url_for("contributor_dashboard"))
        + "?"
        + urlencode({"language": language, "message": "Concept change claim submitted"}),
        status_code=303,
    )


@router.post("/concepts/{iri:path}/links/claim", name="contributor_create_link_claim")
async def contributor_create_link_claim(
    request: Request,
    iri: str,
    csrf_token: str = Form(...),
    language: str = Form("en"),
    link_type: str = Form(str(RelationshipVerbs.exact_match)),
    target_iri: str = Form(""),
    association_id: str = Form(""),
    original_link_type: str = Form(""),
    original_target_iri: str = Form(""),
    concept_scheme: str | None = Form(None),
    settings: Settings = Depends(get_settings),
    claim_store=Depends(get_claim_store),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    _validate_contributor_csrf(request, csrf_token)
    change = {
        "entity_type": "concept_link",
        "operation": "upsert",
        "source_iri": iri,
        "target_iri": target_iri.strip(),
        "link_type": link_type.strip(),
        "association_id": association_id.strip(),
        "original_link_type": original_link_type.strip(),
        "original_target_iri": original_target_iri.strip(),
    }
    await _submit_claim(
        claim_store=claim_store,
        kind="add_relationship",
        title=f"Update concept link for {iri}",
        target_iri=iri,
        rationale="",
        contributor_user=contributor_user,
        change=change,
    )
    return RedirectResponse(
        str(request.url_for("contributor_edit_concept", iri=quote(iri)))
        + "?"
        + urlencode(
            {
                "language": language,
                "concept_scheme": concept_scheme or "",
                "message": "Link claim submitted for admin review",
            }
        ),
        status_code=303,
    )


@router.get("/imports/csv", response_class=HTMLResponse, name="contributor_csv_import")
async def contributor_csv_import(
    request: Request,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    language = _default_language(language, settings)
    return _render_csv_import_form(
        request,
        language=language,
        settings=settings,
        contributor_user=contributor_user,
        form_data={"kind": "bulk_tree_import", "title": "", "rationale": "", "csv_text": "", "csv_import_name": ""},
    )


@router.post("/imports/csv", response_class=HTMLResponse)
async def contributor_csv_import_claim(
    request: Request,
    csrf_token: str = Form(...),
    kind: str = Form("bulk_tree_import"),
    title: str = Form(""),
    rationale: str = Form(""),
    csv_text: str = Form(""),
    csv_import_name: str = Form(""),
    csv_file: UploadFile | None = File(None),
    language: str = Form("en"),
    settings: Settings = Depends(get_settings),
    claim_store=Depends(get_claim_store),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    _validate_contributor_csrf(request, csrf_token)
    form_data = {"kind": kind, "title": title, "rationale": rationale, "csv_text": csv_text, "csv_import_name": csv_import_name}
    try:
        uploaded_csv_text, csv_file_name = _read_csv_upload(csv_file)
        if uploaded_csv_text:
            csv_text = uploaded_csv_text
            form_data["csv_text"] = csv_text
        change = _csv_change_from_form(kind, csv_text=csv_text, csv_file_name=csv_file_name, import_name=csv_import_name)
        await _submit_claim(
            claim_store=claim_store,
            kind=kind,
            title=title.strip() or f"CSV import: {csv_import_name.strip() or kind}",
            target_iri="",
            rationale=rationale,
            contributor_user=contributor_user,
            change=change,
        )
    except ValueError as exc:
        return _render_csv_import_form(
            request,
            language=language,
            settings=settings,
            contributor_user=contributor_user,
            form_data=form_data,
            error=str(exc),
        )
    return RedirectResponse(
        str(request.url_for("contributor_dashboard"))
        + "?"
        + urlencode({"language": language, "message": "CSV import claim submitted for admin review"}),
        status_code=303,
    )


@router.get("/claims/{claim_id}", response_class=HTMLResponse, name="contributor_claim_detail")
async def contributor_claim_detail(
    request: Request,
    claim_id: int,
    language: str | None = None,
    settings: Settings = Depends(get_settings),
    claim_store=Depends(get_claim_store),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user

    claim = await claim_store.get(claim_id)
    if not claim or claim["submitted_by"].get("id") != contributor_user["id"]:
        raise HTTPException(status_code=404, detail="Claim not found")

    language = _default_language(language, settings)
    return templates.TemplateResponse(
        request,
        "contributor_claim_detail.html",
        context=_base_context(
            request,
            language,
            settings,
            contributor_user=contributor_user,
            claim=claim,
            claim_preview=_claim_payload_preview(claim.get("payload", {})),
        ),
    )
