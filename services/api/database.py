"""TinyDB data access for suppliers, users, profiles and password reset tokens.

Routes only talk to SupplierRepository, so moving to Postgres later means
rewriting this module without touching the API layer. Documents are stored as
JSON (dates and datetimes in ISO 8601) and turned back into models on read.
"""

from __future__ import annotations

import os
import threading
from datetime import UTC, datetime
from pathlib import Path

from tinydb import Query, TinyDB
from tinydb.table import Document

from models import Category, Country, Supplier, SupplierCreate, SupplierStatus
from user_models import PasswordResetToken, Profile, User

API_ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = API_ROOT / "data" / "suppliers.json"
DB_PATH_ENV = "SUPPLIERS_DB_PATH"
DEFAULT_USERS_DB_PATH = API_ROOT / "data" / "users.json"
USERS_DB_PATH_ENV = "USERS_DB_PATH"


def db_path_from_env() -> Path:
    return Path(os.environ.get(DB_PATH_ENV) or DEFAULT_DB_PATH)


def users_db_path_from_env() -> Path:
    return Path(os.environ.get(USERS_DB_PATH_ENV) or DEFAULT_USERS_DB_PATH)


def _now() -> str:
    return datetime.now(UTC).isoformat()


class SupplierRepository:
    def __init__(self, path: Path | str) -> None:
        self._db = TinyDB(path, create_dirs=True, encoding="utf-8", ensure_ascii=False, indent=2)
        self._table = self._db.table("suppliers")
        # TinyDB is not thread-safe and FastAPI runs sync routes in a thread pool.
        self._lock = threading.Lock()

    def close(self) -> None:
        self._db.close()

    @staticmethod
    def _to_model(doc: Document) -> Supplier:
        return Supplier.model_validate({**doc, "id": doc.doc_id})

    def count(self) -> int:
        with self._lock:
            return len(self._table)

    def exists_name(self, name: str) -> bool:
        with self._lock:
            return self._table.contains(Query().name == name)

    def list(self, country: Country | None = None, category: Category | None = None) -> list[Supplier]:
        supplier = Query()
        conditions = []
        if country is not None:
            conditions.append(supplier.country == country.value)
        if category is not None:
            conditions.append(supplier.categories.any([category.value]))
        with self._lock:
            if not conditions:
                docs = self._table.all()
            else:
                condition = conditions[0]
                for extra in conditions[1:]:
                    condition &= extra
                docs = self._table.search(condition)
        return [self._to_model(doc) for doc in docs]

    def get(self, supplier_id: int) -> Supplier | None:
        with self._lock:
            doc = self._table.get(doc_id=supplier_id)
        return self._to_model(doc) if doc else None

    def create(self, data: SupplierCreate) -> Supplier:
        record = {**data.model_dump(mode="json"), "updated_at": _now()}
        with self._lock:
            doc_id = self._table.insert(record)
            doc = self._table.get(doc_id=doc_id)
        return self._to_model(doc)

    def _update(self, supplier_id: int, fields: dict) -> Supplier | None:
        with self._lock:
            if not self._table.contains(doc_id=supplier_id):
                return None
            self._table.update(fields, doc_ids=[supplier_id])
            doc = self._table.get(doc_id=supplier_id)
        return self._to_model(doc)

    def update_rate(self, supplier_id: int, monthly_rate: float) -> Supplier | None:
        return self._update(supplier_id, {"monthly_rate": monthly_rate, "updated_at": _now()})

    def update_status(self, supplier_id: int, status: SupplierStatus) -> Supplier | None:
        return self._update(supplier_id, {"status": status.value})

    def delete(self, supplier_id: int) -> bool:
        with self._lock:
            # TinyDB raises KeyError when removing an unknown doc_id.
            if not self._table.contains(doc_id=supplier_id):
                return False
            self._table.remove(doc_ids=[supplier_id])
            return True


class EmailAlreadyRegistered(Exception):
    pass


class UserRepository:
    """Users, their 1:1 profiles and password reset tokens, in tables of the same TinyDB file.

    All tables share one lock, so creating or deleting a user together with its
    profile happens as a single step no other request can interleave with.
    Records are keyed by their own `id` (uuid4 string), not by TinyDB's doc_id.
    """

    def __init__(self, path: Path | str) -> None:
        self._db = TinyDB(path, create_dirs=True, encoding="utf-8", ensure_ascii=False, indent=2)
        self._users = self._db.table("users")
        self._profiles = self._db.table("profiles")
        self._reset_tokens = self._db.table("password_reset_tokens")
        self._lock = threading.Lock()

    def close(self) -> None:
        self._db.close()

    def get_user(self, user_id: str) -> User | None:
        with self._lock:
            doc = self._users.get(Query().id == user_id)
        return User.model_validate(doc) if doc else None

    def get_user_by_email(self, email: str) -> User | None:
        with self._lock:
            doc = self._users.get(Query().email == email)
        return User.model_validate(doc) if doc else None

    def list_users(self) -> list[User]:
        with self._lock:
            docs = self._users.all()
        return [User.model_validate(doc) for doc in docs]

    def create_user_with_profile(self, user: User, profile: Profile) -> User:
        with self._lock:
            if self._users.contains(Query().email == user.email):
                raise EmailAlreadyRegistered(user.email)
            self._users.insert(user.model_dump(mode="json"))
            try:
                self._profiles.insert(profile.model_dump(mode="json"))
            except Exception:
                self._users.remove(Query().id == user.id)
                raise
        return user

    def update_user(self, user_id: str, fields: dict) -> User | None:
        record = Query()
        with self._lock:
            if "email" in fields and self._users.contains((record.email == fields["email"]) & (record.id != user_id)):
                raise EmailAlreadyRegistered(fields["email"])
            if not self._users.update(fields, record.id == user_id):
                return None
            doc = self._users.get(record.id == user_id)
        return User.model_validate(doc)

    def delete_user_with_profile(self, user_id: str) -> bool:
        with self._lock:
            removed = self._users.remove(Query().id == user_id)
            self._profiles.remove(Query().user_id == user_id)
        return bool(removed)

    def get_profile(self, user_id: str) -> Profile | None:
        with self._lock:
            doc = self._profiles.get(Query().user_id == user_id)
        return Profile.model_validate(doc) if doc else None

    def upsert_profile(self, profile: Profile) -> Profile:
        """Write the profile of `profile.user_id`, keeping at most one per user."""
        with self._lock:
            self._profiles.upsert(profile.model_dump(mode="json"), Query().user_id == profile.user_id)
        return profile

    def _invalidate_reset_tokens(self, user_id: str, now: str) -> int:
        record = Query()
        return len(self._reset_tokens.update({"used_at": now}, (record.user_id == user_id) & (record.used_at == None)))  # noqa: E711

    def add_reset_token(self, token: PasswordResetToken) -> None:
        """Store a new reset token, invalidating any the user still had pending."""
        with self._lock:
            self._invalidate_reset_tokens(token.user_id, _now())
            self._reset_tokens.insert(token.model_dump(mode="json"))

    def consume_reset_token(self, jti: str, user_id: str) -> bool:
        """Mark the token used if it exists, belongs to the user, is unused and unexpired.

        Check and update happen under one lock, so two requests can never spend the same token.
        """
        record = Query()
        with self._lock:
            doc = self._reset_tokens.get(record.jti == jti)
            if doc is None:
                return False
            token = PasswordResetToken.model_validate(doc)
            now = datetime.now(UTC)
            if token.user_id != user_id or token.used_at is not None or token.expires_at <= now:
                return False
            self._reset_tokens.update({"used_at": now.isoformat()}, record.jti == jti)
        return True

    def invalidate_reset_tokens(self, user_id: str) -> int:
        """Spend every pending reset token of the user. Returns how many there were."""
        with self._lock:
            return self._invalidate_reset_tokens(user_id, _now())

    def get_reset_token(self, jti: str) -> PasswordResetToken | None:
        with self._lock:
            doc = self._reset_tokens.get(Query().jti == jti)
        return PasswordResetToken.model_validate(doc) if doc else None
