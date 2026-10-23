"""MCP Apps adapter — a bounded, read-only interoperability layer.

Exposes an explicitly allowlisted subset of existing StudyNexs assistant capabilities to
compatible external MCP hosts, over the stable MCP JSON-RPC protocol. It holds NO business logic,
NO identity, NO authorization and NO data of its own: every tool call runs the existing governed
capability under the authenticated CurrentUser, and authorization is re-enforced there. See
server.py for the allowlist and endpoints/mcp.py for the authenticated transport.
"""
