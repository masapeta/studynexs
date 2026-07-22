/** Customer-safe error copy — never expose hosts, ports, or stack traces in the UI. */

export const CUSTOMER_NETWORK_ERROR =
  "We couldn't load this information. Check your connection and try again, or contact your school administrator if this continues.";

export const CUSTOMER_SERVER_ERROR =
  "Something went wrong on our side. Please try again in a moment.";

export const CUSTOMER_UNAUTHORIZED =
  "Your session has expired. Please sign in again.";

const TECHNICAL_PATTERN =
  /localhost|127\.0\.0\.1|0\.0\.0\.0|:8000|api server|running on port|uvicorn|traceback|exception|sqlalchemy|fastapi|docker\/wsl/i;

export function sanitizeCustomerErrorMessage(
  message: string,
  status: number,
  fallback = CUSTOMER_NETWORK_ERROR
): string {
  const trimmed = (message || "").trim();
  if (!trimmed) return fallback;

  if (status === 0) return CUSTOMER_NETWORK_ERROR;
  if (status === 401) return CUSTOMER_UNAUTHORIZED;
  if (status >= 500) return CUSTOMER_SERVER_ERROR;

  if (TECHNICAL_PATTERN.test(trimmed)) return fallback;
  if (trimmed.length > 220) return fallback;

  return trimmed;
}
