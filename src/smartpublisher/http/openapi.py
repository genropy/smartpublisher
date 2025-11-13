"""
OpenAPI schema generation from published handlers.

Converts handler methods to OpenAPI 3.0 schema using existing
get_api_json() functionality.
"""

from typing import Any, Dict


def generate_openapi_schema(
    publisher, title: str = "API", version: str = "0.1.0", description: str = "Auto-generated API"
) -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 schema from published handlers.

    Args:
        publisher: Publisher instance with registered handlers
        title: API title
        version: API version
        description: API description

    Returns:
        OpenAPI 3.0 schema dictionary
    """
    schema = {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": version,
            "description": description,
        },
        "paths": {},
        "components": {"schemas": {}},
    }

    # Iterate through all OpenAPI-enabled handlers
    for path, handler_info in publisher._openapi_handlers.items():
        handler = handler_info["handler"]

        # Get API schema from handler
        api_schema = handler.smpublisher.get_api_json()

        # Generate paths for each method
        for method_name, method_info in api_schema["methods"].items():
            # Path: /handler_name/method_name
            endpoint_path = f"{path}/{method_name}"

            # Create operation object
            operation = {
                "summary": (
                    method_info.get("docstring", "").split("\n")[0]
                    if method_info.get("docstring")
                    else method_name
                ),
                "description": method_info.get("docstring", ""),
                "operationId": f"{handler_info['name']}_{method_name}",
                "tags": [handler_info["name"]],
                "parameters": [],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                    "422": {"description": "Validation error"},
                },
            }

            # Add parameters
            request_body_required = False
            request_body_properties = {}

            for param in method_info["parameters"]:
                param_name = param["name"]
                param_type = param["type"]
                param_required = param["required"]
                param_default = param.get("default")

                # Map Python types to OpenAPI types
                openapi_type = _python_type_to_openapi(param_type)

                param_schema = {"type": openapi_type, "description": f"Parameter {param_name}"}

                if param_default is not None:
                    param_schema["default"] = param_default

                request_body_properties[param_name] = param_schema

                if param_required:
                    request_body_required = True

            # Add request body if there are parameters
            if request_body_properties:
                required_params = [p["name"] for p in method_info["parameters"] if p["required"]]

                operation["requestBody"] = {
                    "required": request_body_required,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": request_body_properties,
                                "required": required_params if required_params else [],
                            }
                        }
                    },
                }

            # Add to paths (use POST for all operations)
            if endpoint_path not in schema["paths"]:
                schema["paths"][endpoint_path] = {}

            schema["paths"][endpoint_path]["post"] = operation

    return schema


def _python_type_to_openapi(python_type: str) -> str:
    """
    Convert Python type string to OpenAPI type.

    Args:
        python_type: Python type name (str, int, float, bool, etc.)

    Returns:
        OpenAPI type string
    """
    type_mapping = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "list": "array",
        "dict": "object",
        "Any": "object",
    }

    return type_mapping.get(python_type, "string")
