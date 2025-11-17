# SmartPublisher - Session Transcript

---

## Setup: Create Example App

```bash
$ mkdir -p ~/myshop
$ cd ~/myshop
$ cat > main.py << 'EOF'
from smartswitch import Switcher
from smartpublisher import PublishedClass

class ShopHandler:
    api = Switcher(name="shop")

    def __init__(self):
        self.products = [
            {"id": 1, "name": "Laptop", "price": 999.99},
            {"id": 2, "name": "Mouse", "price": 29.99},
            {"id": 3, "name": "Keyboard", "price": 79.99}
        ]

    @api
    def list(self) -> dict:
        return {"products": self.products, "total": len(self.products)}

    @api
    def get(self, product_id: int) -> dict:
        for p in self.products:
            if p["id"] == product_id:
                return {"product": p}
        return {"error": f"Product {product_id} not found"}

    @api
    def create(self, name: str, price: float) -> dict:
        new_id = max(p["id"] for p in self.products) + 1
        product = {"id": new_id, "name": name, "price": price}
        self.products.append(product)
        return {"status": "created", "product": product}

class MyShop(PublishedClass):
    def on_init(self):
        self.publish("shop", ShopHandler())
EOF
```

---

## Session: Registry Operations

```bash
$ smpub .apps add myshop ~/myshop main MyShop
✓ App 'myshop' registered
  Path: /home/user/myshop

$ smpub .apps list
Registered apps (1):
  myshop → /home/user/myshop

$ smpub .apps list --global
No apps registered globally.

$ smpub .apps getapp myshop
{
  "name": "myshop",
  "path": "/home/user/myshop",
  "module": "main",
  "class": "MyShop"
}
```

---

## Session: Bash Completion

```bash
$ smpub <TAB>
.apps    myshop

$ smpub .apps <TAB>
add      list     remove   getapp

$ smpub myshop <TAB>
shop     _system

$ smpub myshop shop <TAB>
list     get      create
```

---

## Session: App Commands

```bash
$ smpub myshop shop list
{
  "products": [
    {"id": 1, "name": "Laptop", "price": 999.99},
    {"id": 2, "name": "Mouse", "price": 29.99},
    {"id": 3, "name": "Keyboard", "price": 79.99}
  ],
  "total": 3
}

$ smpub myshop shop get --product_id 1
{
  "product": {
    "id": 1,
    "name": "Laptop",
    "price": 999.99
  }
}

$ smpub myshop shop create --name "Monitor" --price 299.99
{
  "status": "created",
  "product": {
    "id": 4,
    "name": "Monitor",
    "price": 299.99
  }
}

$ smpub myshop shop list
{
  "products": [
    {"id": 1, "name": "Laptop", "price": 999.99},
    {"id": 2, "name": "Mouse", "price": 29.99},
    {"id": 3, "name": "Keyboard", "price": 79.99},
    {"id": 4, "name": "Monitor", "price": 299.99}
  ],
  "total": 4
}
```

---

## Session: System Commands

```bash
$ smpub myshop _system list_handlers
{
  "total": 2,
  "handlers": {
    "_system": {
      "class": "SystemCommands",
      "has_api": true,
      "methods": ["list_handlers", "get_handler_info", "get_api_tree"]
    },
    "shop": {
      "class": "ShopHandler",
      "has_api": true,
      "methods": ["list", "get", "create"]
    }
  }
}

$ smpub myshop _system get_handler_info --handler_name shop
{
  "name": "shop",
  "class": "ShopHandler",
  "docstring": "Handler per gestione prodotti.",
  "api_schema": {
    "name": "shop",
    "methods": {
      "list": {
        "description": "Lista tutti i prodotti.",
        "parameters": []
      },
      "get": {
        "description": "Ottieni prodotto per ID.",
        "parameters": [
          {"name": "product_id", "type": "int", "required": true}
        ]
      },
      "create": {
        "description": "Crea nuovo prodotto.",
        "parameters": [
          {"name": "name", "type": "str", "required": true},
          {"name": "price", "type": "float", "required": true}
        ]
      }
    }
  }
}

$ smpub myshop _system get_api_tree
{
  "name": "root",
  "children": {
    "shop": {
      "name": "shop",
      "methods": ["list", "get", "create"]
    },
    "_system": {
      "name": "system",
      "methods": ["list_handlers", "get_handler_info", "get_api_tree"]
    }
  }
}
```

---

## Session: HTTP Server (Terminal 1)

```bash
$ smpub serve myshop --port 8000
Starting myshop on http://0.0.0.0:8000
Swagger UI: http://localhost:8000/docs
Health: http://localhost:8000/_http/health
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## Session: HTTP Requests (Terminal 2)

```bash
$ curl http://localhost:8000/shop/list
{
  "result": {
    "products": [
      {"id": 1, "name": "Laptop", "price": 999.99},
      {"id": 2, "name": "Mouse", "price": 29.99},
      {"id": 3, "name": "Keyboard", "price": 79.99},
      {"id": 4, "name": "Monitor", "price": 299.99}
    ],
    "total": 4
  }
}

$ curl "http://localhost:8000/shop/get?product_id=1"
{
  "result": {
    "product": {
      "id": 1,
      "name": "Laptop",
      "price": 999.99
    }
  }
}

$ curl -X POST http://localhost:8000/shop/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Webcam", "price": 89.99}'
{
  "result": {
    "status": "created",
    "product": {
      "id": 5,
      "name": "Webcam",
      "price": 89.99
    }
  }
}

$ curl http://localhost:8000/_http/health
{
  "status": "healthy",
  "app": "MyShop",
  "handlers": 2
}

$ curl http://localhost:8000/_http/openapi
{
  "openapi": "3.0.0",
  "info": {
    "title": "MyShop API",
    "version": "0.1.0"
  },
  "paths": {
    "/shop/list": {
      "get": {
        "summary": "Lista tutti i prodotti.",
        "parameters": [],
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {"type": "object"}
              }
            }
          }
        }
      }
    },
    "/shop/get": {
      "get": {
        "summary": "Ottieni prodotto per ID.",
        "parameters": [
          {
            "name": "product_id",
            "in": "query",
            "required": false,
            "schema": {"type": "string"}
          }
        ],
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {"type": "object"}
              }
            }
          }
        }
      }
    },
    "/shop/create": {
      "post": {
        "summary": "Crea nuovo prodotto.",
        "parameters": [
          {
            "name": "name",
            "in": "body",
            "required": false,
            "schema": {"type": "string"}
          },
          {
            "name": "price",
            "in": "body",
            "required": false,
            "schema": {"type": "string"}
          }
        ],
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {"type": "object"}
              }
            }
          }
        }
      }
    }
  }
}

$ curl -s http://localhost:8000/_http/metrics
{
  "total_handlers": 2,
  "handlers": ["_system", "shop"]
}
```

---

## Session: Cleanup

```bash
$ # Stop server in Terminal 1 with CTRL+C
^C
INFO:     Shutting down
INFO:     Finished server shutdown.

$ smpub .apps remove myshop
✓ App 'myshop' removed

$ smpub .apps list
No apps registered.
```

---

## Complete Flow Example

```bash
$ # Create app
$ mkdir -p ~/projects/taskapp && cd ~/projects/taskapp

$ cat > main.py << 'EOF'
from smartswitch import Switcher
from smartpublisher import PublishedClass

class TaskHandler:
    api = Switcher(name="tasks")

    def __init__(self):
        self.tasks = []
        self.next_id = 1

    @api
    def add(self, title: str, priority: str = "normal") -> dict:
        task = {"id": self.next_id, "title": title, "priority": priority, "done": False}
        self.tasks.append(task)
        self.next_id += 1
        return {"status": "added", "task": task}

    @api
    def list(self, show_done: bool = False) -> dict:
        if show_done:
            return {"tasks": self.tasks, "total": len(self.tasks)}
        else:
            pending = [t for t in self.tasks if not t["done"]]
            return {"tasks": pending, "total": len(pending)}

    @api
    def complete(self, task_id: int) -> dict:
        for task in self.tasks:
            if task["id"] == task_id:
                task["done"] = True
                return {"status": "completed", "task": task}
        return {"error": f"Task {task_id} not found"}

class TaskApp(PublishedClass):
    def on_init(self):
        self.publish("tasks", TaskHandler())
EOF

$ # Register and use
$ smpub .apps add taskapp ~/projects/taskapp main TaskApp
✓ App 'taskapp' registered
  Path: /home/user/projects/taskapp

$ smpub taskapp tasks add --title "Write docs" --priority "high"
{
  "status": "added",
  "task": {
    "id": 1,
    "title": "Write docs",
    "priority": "high",
    "done": false
  }
}

$ smpub taskapp tasks add --title "Review PR"
{
  "status": "added",
  "task": {
    "id": 2,
    "title": "Review PR",
    "priority": "normal",
    "done": false
  }
}

$ smpub taskapp tasks add --title "Deploy to prod" --priority "high"
{
  "status": "added",
  "task": {
    "id": 3,
    "title": "Deploy to prod",
    "priority": "high",
    "done": false
  }
}

$ smpub taskapp tasks list
{
  "tasks": [
    {"id": 1, "title": "Write docs", "priority": "high", "done": false},
    {"id": 2, "title": "Review PR", "priority": "normal", "done": false},
    {"id": 3, "title": "Deploy to prod", "priority": "high", "done": false}
  ],
  "total": 3
}

$ smpub taskapp tasks complete --task_id 2
{
  "status": "completed",
  "task": {
    "id": 2,
    "title": "Review PR",
    "priority": "normal",
    "done": true
  }
}

$ smpub taskapp tasks list
{
  "tasks": [
    {"id": 1, "title": "Write docs", "priority": "high", "done": false},
    {"id": 3, "title": "Deploy to prod", "priority": "high", "done": false}
  ],
  "total": 2
}

$ smpub taskapp tasks list --show_done true
{
  "tasks": [
    {"id": 1, "title": "Write docs", "priority": "high", "done": false},
    {"id": 2, "title": "Review PR", "priority": "normal", "done": true},
    {"id": 3, "title": "Deploy to prod", "priority": "high", "done": false}
  ],
  "total": 3
}

$ # Serve via HTTP
$ smpub serve taskapp --port 9000 &
[1] 23456
Starting taskapp on http://0.0.0.0:9000
Swagger UI: http://localhost:9000/docs
Health: http://localhost:9000/_http/health

$ curl -X POST http://localhost:9000/tasks/add \
  -H "Content-Type: application/json" \
  -d '{"title": "Fix bug #123", "priority": "urgent"}'
{
  "result": {
    "status": "added",
    "task": {
      "id": 4,
      "title": "Fix bug #123",
      "priority": "urgent",
      "done": false
    }
  }
}

$ curl http://localhost:9000/tasks/list
{
  "result": {
    "tasks": [
      {"id": 1, "title": "Write docs", "priority": "high", "done": false},
      {"id": 3, "title": "Deploy to prod", "priority": "high", "done": false},
      {"id": 4, "title": "Fix bug #123", "priority": "urgent", "done": false}
    ],
    "total": 3
  }
}

$ kill %1
[1]+  Terminated              smpub serve taskapp --port 9000

$ smpub .apps list
Registered apps (2):
  myshop → /home/user/myshop
  taskapp → /home/user/projects/taskapp
```

---

## Quick Reference

```bash
# Registry
smpub .apps add <name> <path> [module] [class]
smpub .apps list [--global]
smpub .apps getapp <name>
smpub .apps remove <name>

# App commands
smpub <app> <handler> <method> [--arg value ...]

# System commands
smpub <app> _system list_handlers
smpub <app> _system get_handler_info --handler_name <handler>
smpub <app> _system get_api_tree

# HTTP server
smpub serve <app> [--port PORT]

# Bash completion
smpub <TAB>
smpub .apps <TAB>
smpub <app> <TAB>
smpub <app> <handler> <TAB>
```
