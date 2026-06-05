"""User module: /api/users/me, wallet, transactions."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import CurrentUserDep, DBDep
from app.models.common import utc_now
from app.models.user import (
    AcceptTermsRequest,
    UpdateLocaleRequest,
    UserPublic,
    UserWithWallet,
    WalletPublic,
)
from app.models.wallet import WalletTransactionList, WalletTransactionPublic

router = APIRouter(tags=["user"])


@router.get("/users/me", response_model=UserWithWallet)
async def get_me(user: CurrentUserDep, db: DBDep) -> UserWithWallet:
    wallet = await db.user_wallets.find_one({"user_id": user["_id"]})
    return UserWithWallet(
        user=UserPublic.model_validate(user),
        wallet=WalletPublic(balance_credits=wallet["balance_credits"], updated_at=wallet["updated_at"]),
    )


@router.patch("/users/me/locale")
async def update_locale(req: UpdateLocaleRequest, user: CurrentUserDep, db: DBDep):
    locale = req.locale.lower()[:2]
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"locale": locale}})
    return {"ok": True, "locale": locale}


@router.post("/users/me/accept-terms")
async def accept_terms(req: AcceptTermsRequest, user: CurrentUserDep, db: DBDep):
    if not (req.terms and req.privacy):
        from app.core.errors import err_bad_request
        raise err_bad_request("terms.required", "Devi accettare entrambi: T&C e Privacy")
    now = utc_now()
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"terms_accepted_at": now, "privacy_accepted_at": now}},
    )
    return {"ok": True, "accepted_at": now.isoformat()}


@router.get("/wallet/balance", response_model=WalletPublic)
async def get_balance(user: CurrentUserDep, db: DBDep) -> WalletPublic:
    wallet = await db.user_wallets.find_one({"user_id": user["_id"]})
    return WalletPublic(balance_credits=wallet["balance_credits"], updated_at=wallet["updated_at"])


@router.get("/wallet/transactions", response_model=WalletTransactionList)
async def get_transactions(
    user: CurrentUserDep,
    db: DBDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> WalletTransactionList:
    skip = (page - 1) * page_size
    total = await db.wallet_transactions.count_documents({"user_id": user["_id"]})
    cursor = db.wallet_transactions.find({"user_id": user["_id"]}).sort("created_at", -1).skip(skip).limit(page_size)
    items_raw = await cursor.to_list(length=page_size)
    items = [WalletTransactionPublic.model_validate(tx) for tx in items_raw]
    return WalletTransactionList(items=items, total=total, page=page, page_size=page_size)
