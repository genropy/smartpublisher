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

    def _tagged_openapi(
        self, openapi: dict, ignore_prefixes=None, single_segment_tag: str = "default"
    ) -> dict:
        """
        Add tags to OpenAPI operations based on their path.

        Rule:
            /xx/yy/zz/resource -> tag: "xx.yy.zz"

        Args:
            openapi: OpenAPI spec as dict
            ignore_prefixes: list of prefixes to strip, e.g. [["api", "v1"], ["internal"]]
            single_segment_tag: tag to use when the path has a single segment
                (after prefix stripping); defaults to "default".

        Returns:
            Modified OpenAPI dict
        """
        if ignore_prefixes is None:
            ignore_prefixes = []

        def generate_tag(path: str) -> str:
            parts = [p for p in path.split("/") if p]
            # strip configured prefixes
            for prefix in ignore_prefixes:
                if parts[: len(prefix)] == prefix:
                    parts = parts[len(prefix) :]
            # drop path params
            parts = [p for p in parts if not p.startswith("{")]
            if len(parts) >= 2:
                return ".".join(parts[:-1])
            if len(parts) == 1:
                return single_segment_tag or parts[0]
            return "default"

        for path, methods in openapi.get("paths", {}).items():
            for _http_method, operation in methods.items():
                if isinstance(operation, dict) and not operation.get("tags"):
                    operation["tags"] = [generate_tag(path)]

        return openapi

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
            "handlers": len(self.list_handlers()),
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

        # Root methods
        def _http_method_for(name: str) -> str:
            return "get" if name in ["list", "get", "describe", "getapp", "members"] else "post"

        root_methods = {
            name: info
            for name, info in self.publisher.api.describe().get("methods", {}).items()
            if name.startswith("/")
        }
        for method_name, method_info in root_methods.items():
            safe_root = method_name.lstrip("/") or method_name
            http_method = _http_method_for(safe_root)
            raw_params = method_info.get("parameters", {})
            if isinstance(raw_params, dict):
                param_iter = [
                    {"name": pname, **(pdata or {})} if isinstance(pdata, dict) else {"name": pname}
                    for pname, pdata in raw_params.items()
                ]
            else:
                param_iter = raw_params or []

            openapi_spec["paths"][f"/{safe_root}"] = {
                http_method: {
                    "summary": method_info.get("description", safe_root),
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

        # Children handlers
        for handler_name, handler in self.get_handlers().items():
            if not hasattr(handler, "api"):
                continue

            handler_schema = handler.api.describe()
            safe_handler = handler_name.lstrip("/") or handler_name
            for method_name, method_info in handler_schema.get("methods", {}).items():
                path = f"/{safe_handler}/{method_name}"

                http_method = _http_method_for(method_name)
                raw_params = method_info.get("parameters", {})
                if isinstance(raw_params, dict):
                    param_iter = [
                        {"name": pname, **(pdata or {})} if isinstance(pdata, dict) else {"name": pname}
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

        return self._tagged_openapi(openapi_spec, ignore_prefixes=[["_http"]], single_segment_tag="root")

    @route("http_api")
    def metrics(self) -> dict:
        """
        Get metrics.

        This is an HTTP utility command, not business logic.

        Returns:
            dict: Metrics data
        """
        return {
            "total_handlers": len(self.list_handlers()),
            "handlers": self.list_handlers(),
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
            from fastapi import FastAPI, Request
        except ImportError:
            raise ImportError(
                "FastAPI not installed. Install with: pip install smartpublisher[http]"
            )

        app = FastAPI(
            title=f"{self.publisher.__class__.__name__} API",
            description=f"Auto-generated API from {self.publisher.__class__.__name__}",
            docs_url=None,
            redoc_url=None,
        )

        # Register HTTP utility endpoints at /_http/
        @app.get("/_http/health", name="health", summary="Health check")
        async def health_endpoint():
            return self.http_api["health"]()

        @app.get("/_http/openapi", name="openapi", summary="OpenAPI spec")
        async def openapi_endpoint():
            return self.http_api["openapi_schema"]()

        @app.get("/_http/metrics", name="metrics", summary="Metrics")
        async def metrics_endpoint():
            return self.http_api["metrics"]()

        # Scalar UI served at /_http/scalar
        @app.get("/_http/scalar", name="scalar", summary="Scalar UI")
        async def scalar_ui():
            html = """
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="UTF-8" />
              <title>SmartPublisher API</title>
            </head>
            <body>
              <script
                id="api-reference"
                data-url="/_http/openapi">
              </script>
              <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
            </body>
            </html>
            """
            from fastapi.responses import HTMLResponse

            return HTMLResponse(content=html)

        @app.get("/_http/members", name="members", summary="API members tree")
        async def members_endpoint():
            def _prune(node: dict) -> dict:
                handlers = node.get("handlers", {}) or {}
                children = node.get("children", {}) or {}
                return {
                    "name": node.get("name"),
                    "handlers": {name: {} for name in handlers.keys()},
                    "children": {child_name: _prune(child) for child_name, child in children.items()},
                }

            tree = self.publisher.api.members(channel=self.CHANNEL_CODE)
            return _prune(tree)

        @app.get("/_http/ui", name="ui", summary="Simple members viewer", response_class=None)
        async def members_ui():
            html = """
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="UTF-8" />
              <title>SmartPublisher API</title>
              <style>
                body { font-family: sans-serif; margin: 16px; }
                ul { list-style: none; padding-left: 16px; }
                .handler { font-weight: 600; }
                code { background: #f5f5f5; padding: 2px 4px; border-radius: 3px; }
              </style>
            </head>
            <body>
              <h1>SmartPublisher API</h1>
              <div id="tree">Loading...</div>
              <script>
              fetch('/_http/members').then(r => r.json()).then(data => {
                const container = document.getElementById('tree');
                const renderHandlers = (handlers) => {
                  const ul = document.createElement('ul');
                  Object.keys(handlers || {}).forEach(name => {
                    const li = document.createElement('li');
                    li.innerHTML = '<span class="handler">' + name + '</span>';
                    ul.appendChild(li);
                  });
                  return ul;
                };
                const renderNode = (node) => {
                  const root = document.createElement('ul');
                  const rootLi = document.createElement('li');
                  rootLi.innerHTML = '<span class="handler">' + (node.name || 'root') + '</span>';
                  const handlers = renderHandlers(node.handlers);
                  rootLi.appendChild(handlers);
                  const childrenUl = document.createElement('ul');
                  Object.entries(node.children || {}).forEach(([childName, child]) => {
                    const li = document.createElement('li');
                    li.innerHTML = '<span class="handler">' + childName + '</span>';
                    li.appendChild(renderHandlers(child.handlers));
                    childrenUl.appendChild(li);
                  });
                  rootLi.appendChild(childrenUl);
                  root.appendChild(rootLi);
                  return root;
                };
                container.innerHTML = '';
                container.appendChild(renderNode(data));
              }).catch(err => {
                document.getElementById('tree').innerText = 'Error loading tree: ' + err;
              });
              </script>
            </body>
            </html>
            """
            from fastapi.responses import HTMLResponse

            return HTMLResponse(content=html)

        # Build endpoints from members filtered by channel
        tree = self.publisher.api.members(channel=self.CHANNEL_CODE)

        def _http_method_for(name: str) -> str:
            return "get" if name in ["list", "get", "describe", "getapp", "members"] else "post"

        # Root-level methods
        for method_name in tree.get("handlers", {}).keys():
            safe_root = method_name.lstrip("/") or method_name
            path = f"/{safe_root}"
            http_method_type = _http_method_for(safe_root)

            async def root_endpoint(request: Request, method=method_name):
                method_callable = self.publisher.api.get(method, use_smartasync=True)
                kwargs = {}
                try:
                    kwargs = await request.json()
                except Exception:
                    kwargs = {}
                result = method_callable(**kwargs)
                if hasattr(result, "__await__"):
                    result = await result
                return {"result": result}

            root_endpoint.__name__ = f"root_{safe_root}_{http_method_type}"
            root_endpoint.__doc__ = safe_root

            if http_method_type == "get":
                app.get(path, name=safe_root, summary=root_endpoint.__doc__)(root_endpoint)
            else:
                app.post(path, name=safe_root, summary=root_endpoint.__doc__)(root_endpoint)

        # Children (business handlers)
        for handler_name, meta in tree.get("children", {}).items():
            instance = meta.get("instance")
            if instance is None or not hasattr(instance, "api"):
                continue
            safe_handler = handler_name.lstrip("/") or handler_name
            for method_name in meta.get("handlers", {}).keys():
                path = f"/{safe_handler}/{method_name}"
                http_method_type = _http_method_for(method_name)

                def make_endpoint(handler_inst, method_nm):
                    async def endpoint(request: Request):
                        method_callable = handler_inst.api.get(method_nm, use_smartasync=True)
                        kwargs = {}
                        try:
                            kwargs = await request.json()
                        except Exception:
                            kwargs = {}
                        result = method_callable(**kwargs)
                        if hasattr(result, "__await__"):
                            result = await result
                        return {"result": result}

                    endpoint.__name__ = f"{safe_handler}_{method_nm}_{http_method_type}"
                    endpoint.__doc__ = method_nm
                    return endpoint

                endpoint_func = make_endpoint(instance, method_name)

                if http_method_type == "get":
                    app.get(path, name=f"{safe_handler}.{method_name}", summary=endpoint_func.__doc__)(endpoint_func)
                else:
                    app.post(path, name=f"{safe_handler}.{method_name}", summary=endpoint_func.__doc__)(endpoint_func)

        return app

    def run(self, port: int = 8000, **kwargs):
        """
        Run HTTP server.

        Args:
            port: Port to listen on
            **kwargs: Additional options (ignored)
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
