"""
FastAPI integration for Publisher HTTP mode.
"""

import inspect
from enum import Enum
from typing import Any

try:
    from fastapi import FastAPI, HTTPException, Depends
    from pydantic import ValidationError
except ImportError:
    FastAPI = None


def create_fastapi_app(
    publisher,
    title: str = "SmartPublisher API",
    description: str = "Auto-generated API from Publisher",
    version: str = "0.1.0",
) -> Any:
    """
    Create a FastAPI app from a Publisher instance.

    Args:
        publisher: Publisher instance
        title: API title
        description: API description
        version: API version

    Returns:
        FastAPI app instance
    """
    if FastAPI is None:
        raise ImportError("FastAPI is not installed. Install with: pip install smpub[http]")

    app = FastAPI(
        title=title,
        description=description,
        version=version,
    )

    # Collect all models and endpoints first
    endpoints = []

    # Register routes for each handler
    for http_path, handler_info in publisher._openapi_handlers.items():
        handler = handler_info["handler"]
        handler_name = handler_info["name"]
        switcher_name = handler_info["switcher_name"]

        # Get handler's Switcher
        if not hasattr(handler.__class__, switcher_name):
            continue

        switcher = getattr(handler.__class__, switcher_name)

        # Get prefix if any
        prefix = getattr(switcher, "prefix", None) or ""

        # Get only registered methods from switcher (not all public methods)
        entries = switcher.entries() if hasattr(switcher, "entries") else []

        for method_key in entries:
            # method_key is the display name (without prefix)
            # Build full method name with prefix
            full_method_name = f"{prefix}{method_key}" if prefix else method_key
            api_method_name = method_key

            # Check if method exists on handler
            if not hasattr(handler, full_method_name):
                continue

            # Get method
            method = getattr(handler, full_method_name)

            # Get Pydantic model from func._plugin_meta['pydantic']
            # This is prepared by PydanticPlugin during decoration via on_decorate() hook
            RequestModel = None
            if hasattr(method, "_plugin_meta") and "pydantic" in method._plugin_meta:
                pydantic_meta = method._plugin_meta["pydantic"]
                RequestModel = pydantic_meta.get("model")

            # Determine if this is a read-only method (use GET) or write method (use POST)
            read_only_methods = {"list", "get", "search", "find", "statistics", "count", "exists"}
            is_read_only = api_method_name in read_only_methods

            # Store endpoint info
            route_path = f"{http_path}/{api_method_name}"
            endpoints.append(
                {
                    "route_path": route_path,
                    "handler_name": handler_name,
                    "api_method_name": api_method_name,
                    "method": method,
                    "RequestModel": RequestModel,
                    "is_read_only": is_read_only,
                }
            )

    # Store models in globals so FastAPI can find them
    import sys

    this_module = sys.modules[__name__]

    # Now register all routes with pre-created models
    for endpoint_info in endpoints:
        route_path = endpoint_info["route_path"]
        handler_name = endpoint_info["handler_name"]
        api_method_name = endpoint_info["api_method_name"]
        method = endpoint_info["method"]
        RequestModel = endpoint_info["RequestModel"]
        is_read_only = endpoint_info["is_read_only"]

        if RequestModel:
            # Store model in module globals so FastAPI can find it
            model_name = RequestModel.__name__
            setattr(this_module, model_name, RequestModel)

            if is_read_only:
                # For read-only methods, use GET with query parameters
                # FastAPI with Depends() automatically converts Pydantic model fields to query params
                def make_get_endpoint(method_ref, model_cls):
                    async def endpoint_func(params: model_cls = Depends()):
                        f"""Auto-generated GET endpoint for {handler_name}.{api_method_name}"""
                        try:
                            params_dict = params.model_dump()

                            # Convert enum values back to strings
                            for key, value in params_dict.items():
                                if isinstance(value, Enum):
                                    params_dict[key] = value.value

                            # Handle markdown_html format: convert to markdown for the method call
                            original_format = params_dict.get("format")
                            if original_format == "markdown_html":
                                params_dict["format"] = "markdown"

                            # Call method - smartasync handles async/sync automatically
                            result = method_ref(**params_dict)
                            if inspect.iscoroutine(result):
                                result = await result

                            # For read methods, return result directly without wrapper if it's a string
                            # (formatted output like markdown/html/table)
                            if isinstance(result, str):
                                format_type = original_format if original_format else "json"
                                if format_type == "html":
                                    from fastapi.responses import HTMLResponse

                                    return HTMLResponse(content=result)
                                elif format_type == "markdown_html":
                                    from fastapi.responses import HTMLResponse

                                    # Wrap markdown in HTML with client-side rendering libraries
                                    html_wrapper = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Markdown View</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true }});
    </script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            padding: 20px;
            max-width: 900px;
            margin: 0 auto;
            line-height: 1.6;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f5f5f5;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f9f9f9;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
    </style>
</head>
<body>
    <div id="content"></div>
    <script>
        const markdown = {repr(result)};
        document.getElementById('content').innerHTML = marked.parse(markdown);
    </script>
</body>
</html>"""
                                    return HTMLResponse(content=html_wrapper)
                                else:
                                    from fastapi.responses import PlainTextResponse

                                    return PlainTextResponse(content=result)

                            return {"result": result}
                        except ValidationError as e:
                            raise HTTPException(status_code=422, detail=str(e))
                        except Exception as e:
                            raise HTTPException(status_code=500, detail=str(e))

                    # Set proper name for FastAPI introspection
                    endpoint_func.__name__ = f"{handler_name}_{api_method_name}"

                    return endpoint_func

                endpoint_func = make_get_endpoint(method, RequestModel)

                # Register with FastAPI as GET
                app.get(route_path, summary=f"{handler_name}.{api_method_name}")(endpoint_func)
            else:
                # For write methods, use POST with request body
                def make_post_endpoint(method_ref, model_cls):
                    async def endpoint_func(body: model_cls):
                        f"""Auto-generated POST endpoint for {handler_name}.{api_method_name}"""
                        try:
                            params_dict = body.model_dump()
                            # Convert enum values back to strings
                            for key, value in params_dict.items():
                                if isinstance(value, Enum):
                                    params_dict[key] = value.value

                            # Call method - smartasync handles async/sync automatically
                            result = method_ref(**params_dict)
                            if inspect.iscoroutine(result):
                                result = await result

                            return {"result": result}
                        except ValidationError as e:
                            raise HTTPException(status_code=422, detail=str(e))
                        except Exception as e:
                            raise HTTPException(status_code=500, detail=str(e))

                    # Set proper name and annotations for FastAPI introspection
                    endpoint_func.__name__ = f"{handler_name}_{api_method_name}"
                    endpoint_func.__annotations__ = {"body": model_cls, "return": dict}

                    return endpoint_func

                endpoint_func = make_post_endpoint(method, RequestModel)

                # Register with FastAPI as POST
                app.post(route_path, summary=f"{handler_name}.{api_method_name}")(endpoint_func)

        else:
            # No parameters - simple GET endpoint
            def make_simple_endpoint(method_ref):
                async def endpoint():
                    try:
                        # Call method - smartasync handles async/sync automatically
                        result = method_ref()
                        # If result is coroutine, await it
                        if inspect.iscoroutine(result):
                            result = await result

                        return {"result": result}
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=str(e))

                return endpoint

            endpoint_func = make_simple_endpoint(method)
            app.get(route_path, summary=f"{handler_name}.{api_method_name}")(endpoint_func)

    # Force schema reset to ensure our custom function is used
    app.openapi_schema = None

    # Custom OpenAPI schema generation to fix dynamic model schemas
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        from fastapi.openapi.utils import get_openapi

        # Generate base schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Fix schema for endpoints with dynamic models
        for endpoint_info in endpoints:
            if endpoint_info["RequestModel"]:
                route_path = endpoint_info["route_path"]
                model_class = endpoint_info["RequestModel"]

                # Get the Pydantic model schema
                model_schema = model_class.model_json_schema()

                # Update the OpenAPI schema for this path
                if route_path in openapi_schema.get("paths", {}):
                    post_op = openapi_schema["paths"][route_path].get("post", {})
                    if "requestBody" in post_op:
                        # Replace the generic Body schema with our model schema
                        post_op["requestBody"]["content"]["application/json"][
                            "schema"
                        ] = model_schema

                        # Add model to components/schemas if it references other schemas
                        if "$defs" in model_schema:
                            if "components" not in openapi_schema:
                                openapi_schema["components"] = {}
                            if "schemas" not in openapi_schema["components"]:
                                openapi_schema["components"]["schemas"] = {}

                            # Add all definitions to components
                            for def_name, def_schema in model_schema["$defs"].items():
                                openapi_schema["components"]["schemas"][def_name] = def_schema

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Add root endpoint with links to documentation
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint with HTML links to API documentation."""
        from fastapi.responses import HTMLResponse

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 10px;
                }}
                .version {{
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 20px;
                }}
                .description {{
                    color: #666;
                    margin-bottom: 30px;
                    line-height: 1.6;
                }}
                .links {{
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                }}
                .link-card {{
                    display: block;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 6px;
                    text-decoration: none;
                    color: #333;
                    transition: all 0.2s;
                    border-left: 4px solid #007bff;
                }}
                .link-card:hover {{
                    background: #e9ecef;
                    transform: translateX(5px);
                }}
                .link-title {{
                    font-weight: 600;
                    font-size: 16px;
                    margin-bottom: 5px;
                    color: #007bff;
                }}
                .link-desc {{
                    font-size: 14px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>
                <div class="version">Version {version}</div>
                <div class="description">{description}</div>

                <div class="links">
                    <a href="/docs" class="link-card">
                        <div class="link-title">📖 Swagger UI</div>
                        <div class="link-desc">Interactive API documentation with try-it-out functionality</div>
                    </a>

                    <a href="/redoc" class="link-card">
                        <div class="link-title">📚 ReDoc</div>
                        <div class="link-desc">Alternative API documentation with a clean, three-panel design</div>
                    </a>

                    <a href="/openapi.json" class="link-card">
                        <div class="link-title">⚙️ OpenAPI Schema</div>
                        <div class="link-desc">Raw OpenAPI specification in JSON format</div>
                    </a>
                </div>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    return app
