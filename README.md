# FastGRPC

FastGRPC is a Python framework that simplifies the creation of gRPC services using Pydantic models and Python type annotations. It streamlines the process of defining gRPC services by automatically generating `.proto` files and handling the underlying gRPC server setup. With FastGRPC, you can focus on writing business logic without worrying about the boilerplate code typically associated with gRPC services.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Getting Started](#getting-started)
  - [Defining a Service](#defining-a-service)
  - [Running the Service](#running-the-service)
- [CLI Usage](#cli-usage)
- [Examples](#examples)
  - [Simple Addition Service](#simple-addition-service)
  - [Complex Service with Pydantic Models](#complex-service-with-pydantic-models)
  - [Using Compositional and Recursive Data Structures](#using-compositional-and-recursive-data-structures)
- [License](#license)

## Features

- **Automatic `.proto` Generation**: Define your gRPC services using Python functions and Pydantic models, and let FastGRPC handle the `.proto` file generation.
- **Type Hinting Support**: Utilize Python type hints for request and response types for cleaner and more intuitive code.
- **Pydantic Model Integration**: Leverage Pydantic models for data validation and serialization.
- **Simplified Server Setup**: Automatically compile `.proto` files and start the gRPC server with minimal configuration.
- **Custom Service Names**: Easily specify custom service names to suit your project needs.

## Installation

FastGRPC requires Python 3.7 or higher. Install the package via pip:

```bash
pip install fastgrpc
```

Ensure that you have `grpcio`, `grpcio-tools`, `pydantic`, and `python2proto` installed as they are required dependencies.

## Getting Started

### Defining a Service

Create a Python script for your service (e.g., `calculator_service.py`) and define your endpoints using the `@service.endpoint()` decorator:

```python
from pydantic import BaseModel
from fastgrpc.fastgrpc import FastGRPC

# Initialize the service with a custom name
service = FastGRPC(service_name='Calculator')

# Define an endpoint using type hints for request and response
@service.endpoint()
def add(a: int, b: int) -> int:
    return a + b

# Define an endpoint using Pydantic models
class MultiplyRequest(BaseModel):
    x: float
    y: float

class MultiplyResponse(BaseModel):
    result: float

@service.endpoint(request_model=MultiplyRequest, response_model=MultiplyResponse)
def multiply(request):
    return MultiplyResponse(result=request.x * request.y)
```

### Running the Service

You can run your service directly or use the FastGRPC CLI.

#### Direct Execution

```bash
python calculator_service.py
```

Ensure that your script includes the following at the end to generate protos and start the server:

```python
if __name__ == "__main__":
    # Generate the protos and start the server
    service.generate_protos()
    service.serve()
```

#### Using the CLI

First, ensure your script exposes the `service` variable. Then run:

```bash
fastgrpc serve ./calculator_service.py:service
```

## CLI Usage

FastGRPC provides a CLI for generating protos and serving your services.

### Commands

- `generate-protos`: Generate `.proto` files and Python modules.
- `serve`: Start the gRPC server.

### Options

- `--proto-path`: Path to generate `.proto` files (default: `./protos`).
- `--python-out-path`: Path to output generated Python files (default: `./generated`).
- `--service-name`: Name of the gRPC service.
- `--host`: Host to bind the server to (default: `0.0.0.0`).
- `--port`: Port to bind the server to (default: `50051`).
- `--no-rebuild-protos`: Do not rebuild `.proto` files before serving.

### Examples

#### Generate Protos

```bash
fastgrpc generate-protos ./calculator_service.py:service
```

#### Serve Without Rebuilding Protos

```bash
fastgrpc serve ./calculator_service.py:service --no-rebuild-protos
```

## Examples

### Simple Addition Service

Create `add_service.py`:

```python:add_service.py
from fastgrpc.fastgrpc import FastGRPC

service = FastGRPC(service_name='Adder')

@service.endpoint()
def add(a: int, b: int) -> int:
    return a + b

if __name__ == "__main__":
    service.generate_protos()
    service.serve()
```

Run the service:

```bash
python add_service.py
```

### Complex Service with Pydantic Models

Create `user_service.py`:

```python:user_service.py
from pydantic import BaseModel
from fastgrpc.fastgrpc import FastGRPC

service = FastGRPC(service_name='UserService')

class User(BaseModel):
    id: int
    name: str
    email: str

users_db = {}

@service.endpoint()
def create_user(user: User) -> User:
    users_db[user.id] = user
    return user

@service.endpoint()
def get_user(user_id: int) -> User:
    return users_db[user_id]

if __name__ == "__main__":
    service.generate_protos()
    service.serve()
```

Run the service:

```bash
python user_service.py
```

### Using Compositional and Recursive Data Structures

FastGRPC fully supports compositional and recursive data structures through Pydantic models. This allows you to define complex request and response types with nested models, lists, and even recursive references.

#### Compositional Data Structures

Compositional data structures involve nesting one Pydantic model within another. This is useful when you have structured data that naturally contains substructures.

**Example: Nested Models**

Let's create a service that manages orders containing multiple items.

**Create `order_service.py`:**

```python:order_service.py
from typing import List
from pydantic import BaseModel
from fastgrpc.fastgrpc import FastGRPC

service = FastGRPC(service_name='OrderService')

class Item(BaseModel):
    product_id: int
    quantity: int

class Order(BaseModel):
    order_id: int
    items: List[Item]

orders_db = {}

@service.endpoint()
def create_order(order: Order) -> Order:
    orders_db[order.order_id] = order
    return order

@service.endpoint()
def get_order(order_id: int) -> Order:
    return orders_db[order_id]

if __name__ == "__main__":
    service.generate_protos()
    service.serve()
```

**Run the service:**

```bash
python order_service.py
```

In this example, the `Order` model contains a list of `Item` models, showcasing compositional data structures.

#### Recursive Data Structures

Recursive data structures are models that reference themselves, directly or indirectly. This is common in scenarios like representing trees or linked lists.

**Example: Recursive Models**

Let's create a service that manages a hierarchical category structure.

**Create `category_service.py`:**

```python:category_service.py
from typing import List, Optional
from pydantic import BaseModel, Field
from fastgrpc.fastgrpc import FastGRPC

service = FastGRPC(service_name='CategoryService')

class Category(BaseModel):
    id: int
    name: str
    subcategories: Optional[List['Category']] = Field(default_factory=list)

    class Config:
        # Allow forward references
        arbitrary_types_allowed = True
        orm_mode = True

Category.update_forward_refs()

categories_db = {}

@service.endpoint()
def create_category(category: Category) -> Category:
    categories_db[category.id] = category
    return category

@service.endpoint()
def get_category(id: int) -> Category:
    return categories_db[id]

if __name__ == "__main__":
    service.generate_protos()
    service.serve()
```

**Run the service:**

```bash
python category_service.py
```

In this example, the `Category` model references itself in the `subcategories` field, demonstrating how to handle recursive data structures with FastGRPC.

**Note:** When using recursive models, remember to call `update_forward_refs()` after the model definition.

### Client Implementation for Complex Data Structures

You can interact with these complex services using the generated stubs. Here's how you might interact with the `OrderService`:

```python:client_order_service.py
import grpc
from generated.order_service_pb2 import Order, Item
from generated.order_service_pb2_grpc import OrderServiceStub

channel = grpc.insecure_channel('localhost:50051')
client = OrderServiceStub(channel)

# Create an order
order = Order(
    order_id=1,
    items=[
        Item(product_id=101, quantity=2),
        Item(product_id=202, quantity=5)
    ]
)

response = client.create_order(order)
print(response)
```

Similarly, for the `CategoryService`, you can create and retrieve hierarchical categories.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Feel free to contribute to the project or report any issues on the [GitHub repository](https://github.com/yourusername/fastgrpc).
