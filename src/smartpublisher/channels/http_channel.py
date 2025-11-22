"""
PublisherHTTP - HTTP channel implementation.

This class has its own Switcher (http_api) for HTTP-specific utility commands.
These are NOT business logic - they are transport-specific utilities.

Examples: health, openapi_schema, metrics, etc.
These commands make sense in HTTP but not necessarily in CLI.
"""

from smartroute.core import Router, route
from ._base_channel import BaseChannel


class PublisherHTTP(BaseChannel):
    """
    HTTP channel for Publisher.

    Two-level command structure:
    1. Business commands: From publisher.api (channel-agnostic)
    2. Channel commands: From self.http_api (HTTP-specific utilities)

        Example:
            # Business command (works on all channels):
            result = publisher.api['shop']['list']()

            # HTTP utility command (HTTP-specific):
            health_status = http.http_api['health']()
            openapi_spec = http.http_api['openapi_schema']()
    """

    CHANNEL_CODE = "SYS_HTTP"

    def __init__(self, registry):
        """
        Initialize HTTP channel.

        Args:
            registry: ChanRegistry instance
        """
        super().__init__(registry)
        # Router name must match the @route target ("http_api")
        self.http_api = Router(self, name="http_api")

    @route("http_api")
    def health(self) -> dict:
        """
        Health check endpoint.

        This is an HTTP utility command, not business logic.

        Returns:
            dict: Health status
        """
        return {
            "status": "healthy",
            "app": self.publisher.__class__.__name__,
            "handlers": len(self.publisher.list_handlers()),
        }

    @route("http_api")
    def openapi_schema(self) -> dict:
        """
        Generate OpenAPI schema.

        This is an HTTP utility command, not business logic.

        Returns:
            dict: OpenAPI specification
        """
        # Generate from publisher.api
        self.publisher.api.describe()

        # Convert to OpenAPI format
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {"title": f"{self.publisher.__class__.__name__} API", "version": "0.1.0"},
            "paths": {},
        }

        # Build paths from handlers
        for handler_name, handler in self.publisher.get_handlers().items():
            if hasattr(handler, "api"):
                handler_schema = handler.api.describe()

                # Convert each method to OpenAPI path
                safe_handler = handler_name.lstrip("/") or handler_name
                for method_name, method_info in handler_schema.get("methods", {}).items():
                    path = f"/{safe_handler}/{method_name}"

                    # Determine HTTP method (GET for read, POST for write)
                    http_method = "get" if method_name in ["list", "get", "search"] else "post"
                    raw_params = method_info.get("parameters", {})
                    if isinstance(raw_params, dict):
                        param_iter = [
                            (
                                {"name": pname, **(pdata or {})}
                                if isinstance(pdata, dict)
                                else {"name": pname}
                            )
                            for pname, pdata in raw_params.items()
                        ]
                    else:
                        param_iter = raw_params or []

                    openapi_spec["paths"][path] = {
                        http_method: {
                            "summary": method_info.get("description", method_name),
                            "parameters": [
                                {
                                    "name": param.get("name"),
                                    "in": "query" if http_method == "get" else "body",
                                    "required": param.get("required", False),
                                    "schema": {"type": param.get("type", "string")},
                                }
                                for param in param_iter
                            ],
                            "responses": {
                                "200": {
                                    "description": "Successful response",
                                    "content": {"application/json": {"schema": {"type": "object"}}},
                                }
                            },
                        }
                    }

        return openapi_spec

    @route("http_api")
    def metrics(self) -> dict:
        """
        Get metrics.

        This is an HTTP utility command, not business logic.

        Returns:
            dict: Metrics data
        """
        return {
            "total_handlers": len(self.publisher.list_handlers()),
            "handlers": self.publisher.list_handlers(),
        }

    def create_fastapi_app(self):
        """
        Create FastAPI application.

        This wraps the business API (publisher.api) with FastAPI routes.
        It also exposes HTTP utility commands at /_http/ path.

        Returns:
            FastAPI app instance
        """
        try:
            from fastapi import FastAPI
        except ImportError:
            raise ImportError(
                "FastAPI not installed. Install with: pip install smartpublisher[http]"
            )

        app = FastAPI(
            title=f"{self.publisher.__class__.__name__} API",
            description=f"Auto-generated API from {self.publisher.__class__.__name__}",
        )

        # Register HTTP utility endpoints at /_http/
        @app.get("/_http/health")
        async def health_endpoint():
            return self.http_api["health"]()

        @app.get("/_http/openapi")
        async def openapi_endpoint():
            return self.http_api["openapi_schema"]()

        @app.get("/_http/metrics")
        async def metrics_endpoint():
            return self.http_api["metrics"]()

        # Register business endpoints from publisher.api
        for handler_name, handler in self.publisher.get_handlers().items():
            if not hasattr(handler, "api"):
                continue

            handler_api = handler.api

            safe_handler = handler_name.lstrip("/") or handler_name
            for method_name in handler_api.entries():
                path = f"/{safe_handler}/{method_name}"

                # Determine HTTP method
                http_method_type = "get" if method_name in ["list", "get", "search"] else "post"

                # Create endpoint
                def make_endpoint(handler_inst, method_nm):
                    async def endpoint(request=None):
                        method_callable = handler_inst.api.get(method_nm, use_smartasync=True)
                        kwargs = {}
                        if request is not None:
                            try:
                                kwargs = await request.json()
                            except Exception:
                                kwargs = {}
                        result = method_callable(**kwargs)
                        if hasattr(result, "__await__"):
                            result = await result
                        return {"result": result}

                    return endpoint

                endpoint_func = make_endpoint(handler, method_name)

                # Register with FastAPI
                if http_method_type == "get":
                    app.get(path)(endpoint_func)
                else:
                    app.post(path)(endpoint_func)

        return app

    def run(self, port: int = 8000):
        """
        Run HTTP server.

        Args:
            port: Port to listen on
        """
        try:
            import uvicorn
        except ImportError:
            raise ImportError(
                "Uvicorn not installed. Install with: pip install smartpublisher[http]"
            )

        app = self.create_fastapi_app()

        print(f"Starting HTTP server on http://0.0.0.0:{port}")
        print(f"Swagger UI: http://localhost:{port}/docs")
        print(f"Health: http://localhost:{port}/_http/health")

        uvicorn.run(app, host="0.0.0.0", port=port)
