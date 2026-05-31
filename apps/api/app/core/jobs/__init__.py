"""Async job infrastructure (Arq).

`queue` exposes the enqueue helper used by request handlers; `worker` defines the
Arq worker process that runs jobs and drives each Job row through its lifecycle.
"""
