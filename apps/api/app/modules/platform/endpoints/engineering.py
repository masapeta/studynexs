"""Platform engineering dashboard API — internal visibility for admins."""

from fastapi import APIRouter, Depends

from app.core.api_route import CommitOnSuccessRoute
from app.core.dependencies import get_current_user, require_roles
from app.modules.platform.schemas.engineering import EngineeringStatusOut
from app.modules.platform.services.engineering_status import get_engineering_status
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)


@router.get(
    "/engineering-status",
    response_model=APIResponse[EngineeringStatusOut],
    summary="Engineering dashboard snapshot (admin only)",
)
async def engineering_status(
    _user=Depends(require_roles("super_admin", "admin")),
):
    """Return the machine-readable platform status used by the in-app Engineering Dashboard."""
    payload = get_engineering_status()
    return APIResponse(data=EngineeringStatusOut.model_validate(payload))
