# API v1 stability policy

## Scope

Version **v1** is defined by the URL prefix `/api/v1` and the OpenAPI file `openapi-v1.json`.

## Stable (no breaking change without notice)

- Existing paths and HTTP methods
- Required request fields and types
- Response field names and types for documented endpoints
- HTTP status codes for documented success/error cases
- Authentication: Bearer access token + HttpOnly refresh cookie at `/api/v1/auth/refresh`

## Allowed without a new major version

- Adding **optional** request fields
- Adding **new** response fields (clients should ignore unknown fields)
- Adding new endpoints under `/api/v1`
- Adding new enum values only if clients tolerate unknown values

## Breaking (requires v2 or explicit client agreement)

- Removing or renaming response fields
- Changing field types
- Removing endpoints
- Changing authentication scheme
- Changing error body shape for existing clients

## Deprecation process

1. Document in [CHANGELOG.md](./CHANGELOG.md)
2. Add response headers: `Deprecation: true`, `Sunset: <RFC date>`
3. Minimum **90 days** before removal (mobile apps)
4. Ship `/api/v2` in parallel when breaking changes are required

## Tenant

Production clients should use school subdomain or header `X-Tenant-Slug`. JWT `school_id` must match resolved tenant.
