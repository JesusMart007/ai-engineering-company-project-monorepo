from __future__ import annotations

import logging
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from jose import jwt

import email_service
import security
import user_service
from config import ALGORITHM, SECRET_KEY
from conftest import PASSWORD, login, register

EMAIL = "reset@nexova.example"
NEW_PASSWORD = "brand-new-pass-2"


@pytest.fixture()
def outbox(monkeypatch):
    """Captures reset emails instead of calling Resend."""
    sent: list[dict] = []
    monkeypatch.setattr(
        user_service,
        "send_password_reset_email",
        lambda to, link, minutes: sent.append({"to": to, "link": link, "minutes": minutes}) or True,
    )
    return sent


def forgot(client, email=EMAIL):
    return client.post("/auth/forgot-password", json={"email": email})


def token_from(link: str) -> str:
    return parse_qs(urlparse(link).query)["token"][0]


def request_token(client, outbox, email=EMAIL) -> str:
    assert forgot(client, email).status_code == 200
    return token_from(outbox[-1]["link"])


def reset(client, token, new_password=NEW_PASSWORD):
    return client.post("/auth/reset-password", json={"token": token, "new_password": new_password})


def can_login(client, password, email=EMAIL) -> bool:
    return client.post("/auth/login", data={"username": email, "password": password}).status_code == 200


def test_forgot_password_answers_the_same_for_known_and_unknown_emails(anon_client, outbox):
    register(anon_client, EMAIL)
    known, unknown = forgot(anon_client, EMAIL.upper()), forgot(anon_client, "nobody@nexova.example")
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()
    assert [mail["to"] for mail in outbox] == [EMAIL]


def test_reset_email_links_to_the_frontend_with_a_reset_token(anon_client, outbox):
    user = register(anon_client, EMAIL)
    forgot(anon_client)
    (mail,) = outbox
    assert mail["link"].startswith(f"{user_service.FRONTEND_URL}/reset-password?token=")
    assert mail["minutes"] == user_service.RESET_TOKEN_EXPIRE_MINUTES
    claims = jwt.decode(token_from(mail["link"]), SECRET_KEY, algorithms=[ALGORITHM])
    assert claims["sub"] == user["id"] and claims["type"] == "password_reset" and claims["jti"]


def test_inactive_user_gets_no_email(anon_client, outbox):
    user = register(anon_client, EMAIL)
    anon_client.app.state.user_repository.update_user(user["id"], {"is_active": False})
    assert forgot(anon_client).status_code == 200
    assert outbox == []


def test_forgot_password_still_answers_200_when_sending_fails(anon_client, monkeypatch):
    register(anon_client, EMAIL)
    monkeypatch.setattr(email_service, "RESEND_API_KEY", "")  # _send logs and gives up
    assert forgot(anon_client).status_code == 200

    def broken(*_):
        raise RuntimeError("Resend is down")

    monkeypatch.setattr(user_service, "send_password_reset_email", broken)
    assert forgot(anon_client).status_code == 200


def test_reset_changes_the_password_once(anon_client, outbox):
    register(anon_client, EMAIL)
    token = request_token(anon_client, outbox)
    assert reset(anon_client, token).status_code == 200
    assert can_login(anon_client, NEW_PASSWORD)
    assert not can_login(anon_client, PASSWORD)

    reused = reset(anon_client, token, "yet-another-pass-3")
    assert reused.status_code == 400
    assert can_login(anon_client, NEW_PASSWORD)


def test_expired_reset_token_is_rejected(anon_client, outbox, monkeypatch):
    register(anon_client, EMAIL)
    monkeypatch.setattr(
        user_service, "create_reset_token", lambda user_id: security.create_reset_token(user_id, timedelta(seconds=-1))
    )
    assert reset(anon_client, request_token(anon_client, outbox)).status_code == 400
    assert can_login(anon_client, PASSWORD)


def test_new_reset_link_invalidates_the_previous_one(anon_client, outbox):
    register(anon_client, EMAIL)
    first = request_token(anon_client, outbox)
    second = request_token(anon_client, outbox)
    assert reset(anon_client, first).status_code == 400
    assert reset(anon_client, second).status_code == 200


def test_changing_the_password_invalidates_pending_reset_links(anon_client, outbox):
    register(anon_client, EMAIL)
    token = request_token(anon_client, outbox)
    headers = login(anon_client, EMAIL)
    changed = anon_client.post(
        "/auth/change-password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD}, headers=headers
    )
    assert changed.status_code == 200
    assert reset(anon_client, token, "yet-another-pass-3").status_code == 400


@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        jwt.encode({"sub": "x", "jti": "y", "type": "password_reset"}, "another-secret", algorithm="HS256"),
    ],
)
def test_malformed_or_forged_reset_token_is_rejected(anon_client, token):
    assert reset(anon_client, token).status_code == 400


def test_signed_reset_token_without_stored_state_is_rejected(anon_client):
    user = register(anon_client, EMAIL)
    # Correct signature and type, but never issued by /forgot-password: no jti in TinyDB.
    assert reset(anon_client, security.create_reset_token(user["id"]).token).status_code == 400


def test_session_token_cannot_be_used_as_reset_token(anon_client):
    register(anon_client, EMAIL)
    access_token = login(anon_client, EMAIL)["Authorization"].removeprefix("Bearer ")
    assert reset(anon_client, access_token).status_code == 400


def test_reset_token_cannot_be_used_as_a_session_token(anon_client, outbox):
    register(anon_client, EMAIL)
    token = request_token(anon_client, outbox)
    for path in ("/auth/me", "/suppliers", "/profiles/me"):
        assert anon_client.get(path, headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_without_type_is_not_a_session_token(anon_client):
    user = register(anon_client, EMAIL)
    legacy = jwt.encode({"sub": user["id"], "exp": 4102444800}, SECRET_KEY, algorithm=ALGORITHM)
    assert anon_client.get("/auth/me", headers={"Authorization": f"Bearer {legacy}"}).status_code == 401


def test_reset_applies_the_sign_up_password_rules(anon_client, outbox):
    register(anon_client, EMAIL)
    token = request_token(anon_client, outbox)
    assert reset(anon_client, token, "short").status_code == 422
    assert reset(anon_client, token, "x" * 73).status_code == 422
    assert reset(anon_client, token).status_code == 200  # a rejected attempt does not spend the link


def test_change_password_checks_the_current_one(auth_client):
    wrong = auth_client.post(
        "/auth/change-password", json={"current_password": "wrong-password", "new_password": NEW_PASSWORD}
    )
    assert wrong.status_code == 400
    assert can_login(auth_client, PASSWORD, "tester@nexova.example")

    ok = auth_client.post("/auth/change-password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD})
    assert ok.status_code == 200
    assert can_login(auth_client, NEW_PASSWORD, "tester@nexova.example")
    assert not can_login(auth_client, PASSWORD, "tester@nexova.example")


def test_change_password_validates_the_new_one(auth_client):
    response = auth_client.post("/auth/change-password", json={"current_password": PASSWORD, "new_password": "short"})
    assert response.status_code == 422


def test_change_password_requires_a_session(anon_client):
    response = anon_client.post(
        "/auth/change-password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD}
    )
    assert response.status_code == 401


def test_reset_email_is_mobile_friendly_and_has_a_text_version():
    link = "http://localhost:3000/reset-password?token=abc&x=1"
    subject, html_body, text_body = email_service.password_reset_email(link, 30)
    assert "contraseña" in subject.lower()
    assert 'name="viewport"' in html_body and "max-width:480px" in html_body
    assert "Restablecer contraseña" in html_body and "30 minutos" in html_body and "ignora este correo" in html_body
    assert "token=abc&amp;x=1" in html_body  # escaped inside the HTML
    assert link in text_body and "30 minutos" in text_body


@pytest.mark.parametrize(
    ("code", "error_type"),
    [(403, "invalid_api_key"), (500, "HttpClientError"), (429, "rate_limit_exceeded")],
)
def test_resend_failure_is_logged_without_personal_data_and_still_200(anon_client, monkeypatch, caplog, code, error_type):
    import resend
    from resend.exceptions import ResendError

    register(anon_client, "resend-fails@nexova.example")
    monkeypatch.setattr(email_service, "RESEND_API_KEY", "re_test_key_not_real")

    def fail(_params):
        raise ResendError(code=code, error_type=error_type, message="boom", suggested_action="retry")

    monkeypatch.setattr(resend.Emails, "send", fail)
    with caplog.at_level(logging.ERROR, logger="email_service"):
        response = anon_client.post("/auth/forgot-password", json={"email": "resend-fails@nexova.example"})
    assert response.status_code == 200
    assert f"{error_type} (code {code})" in caplog.text
    assert "resend-fails@nexova.example" not in caplog.text
    assert "re_test_key_not_real" not in caplog.text
    assert "token=" not in caplog.text


def test_resend_client_has_an_explicit_timeout():
    import resend

    assert resend.default_http_client._timeout == email_service.RESEND_TIMEOUT_SECONDS == 10


# --- service level: request_password_reset / reset_password with a repository and no HTTP -----------

from datetime import UTC, datetime  # noqa: E402

from freezegun import freeze_time  # noqa: E402

import email_service  # noqa: E402
from security import create_access_token  # noqa: E402


def issue(repo, email):
    user_service.request_password_reset(repo, email)
    return repo._reset_tokens.all()


def test_request_for_a_registered_email_stores_a_token_and_sends_one_email(repo, user, resend_mock):
    tokens = issue(repo, user.email.upper())
    assert len(tokens) == 1 and tokens[0]["user_id"] == user.id and tokens[0]["used_at"] is None
    assert [mail["to"] for mail in resend_mock] == [[user.email]]


@freeze_time(datetime(2030, 1, 1, tzinfo=UTC))
def test_reset_token_expires_after_the_configured_minutes(repo, user):
    issue(repo, user.email)
    stored = repo.get_reset_token(repo._reset_tokens.all()[0]["jti"])
    assert stored.expires_at == datetime.now(UTC) + timedelta(minutes=user_service.RESET_TOKEN_EXPIRE_MINUTES)


def test_request_for_an_unknown_email_stores_nothing_and_sends_nothing(repo, user, resend_mock):
    assert issue(repo, "nobody@nexova.example") == []
    assert resend_mock == []


def test_request_survives_a_resend_failure_without_leaking_it(repo, user, monkeypatch, resend_mock):
    from resend.exceptions import ResendError  # noqa: PLC0415

    def boom(params):
        raise ResendError(code=500, error_type="application_error", message="down", suggested_action="retry")

    monkeypatch.setattr(email_service.resend.Emails, "send", staticmethod(boom))
    user_service.request_password_reset(repo, user.email)  # does not raise
    assert len(repo._reset_tokens.all()) == 1


def test_request_without_api_key_sends_nothing_and_does_not_raise(repo, user, monkeypatch, resend_mock):
    monkeypatch.setattr(email_service, "RESEND_API_KEY", "")
    user_service.request_password_reset(repo, user.email)
    assert resend_mock == []


def _stored_reset(repo, user, **kwargs):
    from user_models import PasswordResetToken  # noqa: PLC0415

    token = security.create_reset_token(user.id, **kwargs)
    repo.add_reset_token(PasswordResetToken(jti=token.jti, user_id=user.id, expires_at=token.expires_at))
    return token


def test_reset_with_a_valid_token_sets_the_password_and_marks_the_token_used(repo, user):
    token = _stored_reset(repo, user)
    user_service.reset_password(repo, token.token, NEW_PASSWORD)
    assert security.verify_password(NEW_PASSWORD, repo.get_user(user.id).hashed_password)
    assert not security.verify_password(PASSWORD, repo.get_user(user.id).hashed_password)
    assert repo.get_reset_token(token.jti).used_at is not None


def test_reusing_a_reset_token_fails_and_keeps_the_second_password_out(repo, user):
    token = _stored_reset(repo, user)
    user_service.reset_password(repo, token.token, NEW_PASSWORD)
    with pytest.raises(user_service.InvalidResetToken):
        user_service.reset_password(repo, token.token, "attacker-pass-9")
    assert security.verify_password(NEW_PASSWORD, repo.get_user(user.id).hashed_password)


def test_expired_reset_token_raises_and_keeps_the_old_password(repo, user):
    token = _stored_reset(repo, user, expires_delta=timedelta(seconds=-1))
    with pytest.raises(user_service.InvalidResetToken):
        user_service.reset_password(repo, token.token, NEW_PASSWORD)
    assert security.verify_password(PASSWORD, repo.get_user(user.id).hashed_password)


def test_session_token_is_not_accepted_as_reset_token(repo, user):
    with pytest.raises(user_service.InvalidResetToken):
        user_service.reset_password(repo, create_access_token(user.id), NEW_PASSWORD)


def test_reset_for_deleted_or_inactive_user_is_rejected(repo, make_user):
    gone, inactive = make_user("gone@nexova.example"), make_user("off@nexova.example")
    tokens = [_stored_reset(repo, gone), _stored_reset(repo, inactive)]
    repo.delete_user_with_profile(gone.id)
    repo.update_user(inactive.id, {"is_active": False})
    for token in tokens:
        with pytest.raises(user_service.InvalidResetToken):
            user_service.reset_password(repo, token.token, NEW_PASSWORD)


def test_a_token_cannot_be_spent_by_another_user_and_only_once(repo, user, make_user):
    other = make_user("other@nexova.example")
    token = _stored_reset(repo, user)
    assert repo.consume_reset_token(token.jti, other.id) is False  # wrong owner
    assert repo.consume_reset_token(token.jti, user.id) is True
    assert repo.consume_reset_token(token.jti, user.id) is False  # already spent


def test_rejected_new_password_does_not_spend_the_token():
    from pydantic import ValidationError  # noqa: PLC0415

    from user_models import ResetPasswordRequest  # noqa: PLC0415

    for bad in ("", "short", " " * 10, "x" * 73):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token="t", new_password=bad)
