import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, urlencode

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from py_semantic_taxonomy.adapters.routers.admin_router import (
    _base_context,
    _default_language,
    _exchange_code_for_token,
    _gitlab_user,
    _language_selector,
    _public_url_for,
)
from py_semantic_taxonomy.adapters.routers.web_router import templates
from py_semantic_taxonomy.cfg import Settings, get_settings
from py_semantic_taxonomy.dependencies import get_claim_store
from py_semantic_taxonomy.domain.url_utils import get_full_api_path

router = APIRouter(prefix="/web/contributor", include_in_schema=False)

CLAIM_KINDS = [
    ("add_concept", "Add concept"),
    ("edit_concept", "Edit concept"),
    ("add_relationship", "Add relationship"),
    ("edit_concept_scheme", "Edit concept scheme"),
    ("deprecate_concept", "Deprecate concept"),
    ("other", "Other"),
]


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


def _render_claim_form(
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
            claim_kinds=CLAIM_KINDS,
            form_data=form_data,
            error=error,
        ),
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
    target_iri: str = "",
    settings: Settings = Depends(get_settings),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user

    language = _default_language(language, settings)
    return _render_claim_form(
        request,
        language=language,
        settings=settings,
        contributor_user=contributor_user,
        form_data={
            "kind": CLAIM_KINDS[0][0],
            "title": "",
            "target_iri": target_iri,
            "rationale": "",
            "payload": "{\n  \n}",
        },
    )


@router.post("/claims/new", response_class=HTMLResponse)
async def contributor_create_claim(
    request: Request,
    csrf_token: str = Form(...),
    kind: str = Form(...),
    title: str = Form(...),
    target_iri: str = Form(""),
    rationale: str = Form(""),
    payload: str = Form("{}"),
    language: str = Form("en"),
    settings: Settings = Depends(get_settings),
    claim_store=Depends(get_claim_store),
):
    contributor_user = _ensure_contributor(request, language, settings)
    if isinstance(contributor_user, RedirectResponse):
        return contributor_user
    _validate_contributor_csrf(request, csrf_token)

    form_data = {
        "kind": kind,
        "title": title,
        "target_iri": target_iri,
        "rationale": rationale,
        "payload": payload,
    }
    if kind not in {value for value, _label in CLAIM_KINDS}:
        return _render_claim_form(
            request,
            language=language,
            settings=settings,
            contributor_user=contributor_user,
            form_data=form_data,
            error="Unknown claim type",
        )
    if not title.strip():
        return _render_claim_form(
            request,
            language=language,
            settings=settings,
            contributor_user=contributor_user,
            form_data=form_data,
            error="Title is required",
        )
    try:
        parsed_payload = json.loads(payload or "{}")
    except json.JSONDecodeError as exc:
        return _render_claim_form(
            request,
            language=language,
            settings=settings,
            contributor_user=contributor_user,
            form_data=form_data,
            error=f"Payload must be valid JSON: {exc}",
        )
    if not isinstance(parsed_payload, dict):
        return _render_claim_form(
            request,
            language=language,
            settings=settings,
            contributor_user=contributor_user,
            form_data=form_data,
            error="Payload must be a JSON object",
        )

    await claim_store.create(
        kind=kind,
        title=title.strip(),
        target_iri=target_iri.strip(),
        payload={"rationale": rationale.strip(), "change": parsed_payload},
        submitted_by=contributor_user,
    )
    return RedirectResponse(
        str(request.url_for("contributor_dashboard"))
        + "?"
        + urlencode({"language": language, "message": "Claim submitted for admin review"}),
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
        context={
            "request": request,
            "language": language,
            "language_selector": _language_selector(request, language, settings),
            "suggest_api_url": get_full_api_path("suggest"),
            "query": "",
            "contributor_user": contributor_user,
            "claim": claim,
        },
    )
