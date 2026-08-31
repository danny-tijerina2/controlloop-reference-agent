"""In-process stand-ins for the services this agent's artifacts name.

Nothing here opens a socket, starts a process, or reads a credential.
`openapi/orders-api.yaml` describes a service at
`https://internal-orders-api.widgetworks.example/v1`; that host is
fictional and is never contacted. The stubs are called as ordinary
Python functions so the whole scenario runs offline.
"""
