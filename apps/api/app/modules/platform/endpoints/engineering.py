"""Platform engineering dashboard API — internal tiers only (development / internal)."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.api_route import CommitOnSuccessRoute
from app.core.config import get_settings
from app.core.dependencies import require_roles
from app.modules.platform.schemas.engineering import EngineeringStatusOut
from app.modules.platform.services.engineering_status import get_engineering_status
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)


def require_internal_tier() -> None:
    """Defence in depth: the router is not mounted outside internal tiers, and this refuses too."""
    if not get_settings().is_internal_tier:
        raise HTTPException(status_code=404, detail="Not found")


@router.get(
    "/engineering-status",
    response_model=APIResponse[EngineeringStatusOut],
    summary="Engineering dashboard snapshot (internal tiers only)",
    dependencies=[Depends(require_internal_tier)],
)
async def engineering_status(
    _user=Depends(require_roles("super_admin", "admin")),
):
    """Return the machine-readable platform status used by the in-app Engineering Dashboard."""
    payload = get_engineering_status()
    return APIResponse(data=EngineeringStatusOut.model_validate(payload))
