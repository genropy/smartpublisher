"""
FastAPI application generation from published handlers.

Automatically creates FastAPI app with routes for all
OpenAPI-enabled handlers.
"""

from typing import Any, Dict

try:
    from fastapi import FastAPI, HTTPException, Body
    from fastapi.responses import JSONResponse
    from pydantic import ValidationError
except ImportError:
    raise ImportError("FastAPI is not installed. Install with: pip install smpub[http]")

from ..validation import validate_args


def create_fastapi_app(publisher, **kwargs) -> FastAPI:
    """
    Create FastAPI application from publisher.

    Args:
        publisher: Publisher instance with registered handlers
        **kwargs: Additional FastAPI configuration

    Returns:
        Configured FastAPI application
    """
    # Get app info
    app_name = publisher.__class__.__name__
    app_description = publisher.__class__.__doc__ or f"{app_name} API"

    # Create FastAPI app
    app = FastAPI(
        title=kwargs.get("title", app_name),
        description=kwargs.get("description", app_description),
        version=kwargs.get("version", "0.1.0"),
        **{k: v for k, v in kwargs.items() if k not in ["title", "description", "version"]},
    )

    # Register routes for each handler
    for path, handler_info in publisher._openapi_handlers.items():
        handler = handler_info["handler"]
        handler_name = handler_info["name"]

        # Get API schema
        api_schema = handler.smpublisher.get_api_json()

        # Create routes for each method
        for method_name, method_info in api_schema["methods"].items():
            _create_route(
                app=app,
                path=path,
                method_name=method_name,
                method_info=method_info,
                handler=handler,
                handler_name=handler_name,
            )

    return app


def _create_route(
    app: FastAPI,
    path: str,
    method_name: str,
    method_info: Dict[str, Any],
    handler: Any,
    handler_name: str,
):
    """
    Create a FastAPI route for a handler method.

    Args:
        app: FastAPI application
        path: Base path for handler
        method_name: Method name (without prefix)
        method_info: Method metadata from get_api_json()
        handler: Handler instance
        handler_name: Handler name for route tags
    """
    endpoint_path = f"{path}/{method_name}"

    # Get the actual method from handler
    full_method_name = None
    for attr_name in dir(handler):
        if attr_name.endswith(f"_{method_name}"):
            full_method_name = attr_name
            break

    if not full_method_name:
        return

    method = getattr(handler, full_method_name)

    # Extract docstring for summary
    docstring = method_info.get("docstring", "")
    summary = docstring.split("\n")[0] if docstring else method_name

    # Build parameter descriptions
    param_descriptions = {}
    for param in method_info["parameters"]:
        param_descriptions[param["name"]] = f"{param['name']} ({param['type']})"

    # Create route handler function
    async def route_handler(body: Dict[str, Any] = Body(default={})):
        """Dynamic route handler for method execution."""
        try:
            # Convert body dict to list of string arguments for validation
            args = []
            for param in method_info["parameters"]:
                param_name = param["name"]
                if param_name in body:
                    args.append(str(body[param_name]))
                elif not param["required"]:
                    # Use default value if not provided
                    if param.get("default") is not None:
                        args.append(str(param["default"]))
                else:
                    raise HTTPException(
                        status_code=422, detail=f"Missing required parameter: {param_name}"
                    )

            # Validate using existing Pydantic validation
            validated_params = validate_args(method, args)

            # Execute method (await if needed, smartasync methods return coroutines in async context)
            result = method(**validated_params)

            # Check if result is a coroutine and await it
            import inspect

            if inspect.iscoroutine(result):
                result = await result

            # Return result
            return JSONResponse(content={"status": "success", "result": result})

        except HTTPException:
            # Re-raise HTTPException as-is (don't wrap it)
            raise
        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail={"status": "error", "message": "Validation error", "errors": e.errors()},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

    # Set function metadata for FastAPI
    route_handler.__name__ = f"{handler_name}_{method_name}"
    route_handler.__doc__ = docstring

    # Register route (POST for all operations)
    app.post(
        endpoint_path,
        summary=summary,
        tags=[handler_name],
        response_model=None,
        name=route_handler.__name__,
    )(route_handler)
