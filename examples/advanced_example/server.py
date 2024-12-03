import sys
from pydantic import BaseModel, Field
from typing import List, Iterator
from concurrent.futures import ThreadPoolExecutor

sys.path.append('../../')
from fastgrpc.fastgrpc import FastGRPC

# Create a service with a custom name
service = FastGRPC(service_name='AdvancedService')

# Complex nested Pydantic models
class Item(BaseModel):
    id: int
    name: str
    price: float

class Order(BaseModel):
    order_id: int
    items: List[Item]
    total_price: float = 0.0

# In-memory database for orders
orders_db = {}

# Endpoint for creating an order
@service.endpoint()
def create_order(order: Order) -> Order:
    order.total_price = sum(item.price for item in order.items)
    orders_db[order.order_id] = order
    return order

# Endpoint for retrieving an order
@service.endpoint()
def get_order(order_id: int) -> Order:
    if order_id not in orders_db:
        raise ValueError(f"Order with ID {order_id} not found")
    return orders_db[order_id]

# Endpoint with server-side streaming
@service.endpoint(stream_response=True)
def list_orders(empty) -> Iterator[Order]:
    for order in orders_db.values():
        yield order

# Endpoint with client-side streaming
class OrderSummary(BaseModel):
    total_orders: int
    total_amount: float

@service.endpoint(stream_request=True)
def stream_orders(order_iterator: Iterator[Order]) -> OrderSummary:
    total_orders = 0
    total_amount = 0.0
    for order in order_iterator:
        order.total_price = sum(item.price for item in order.items)
        orders_db[order.order_id] = order
        total_orders += 1
        total_amount += order.total_price
    return OrderSummary(total_orders=total_orders, total_amount=total_amount)

# Endpoint with bidirectional streaming
class ChatMessage(BaseModel):
    user: str
    message: str

@service.endpoint(stream_request=True, stream_response=True)
def chat(message_stream: Iterator[ChatMessage]) -> Iterator[ChatMessage]:
    for message in message_stream:
        response = ChatMessage(user="Server", message=f"Echo: {message.message}")
        yield response

if __name__ == "__main__":
    # Generate .proto files and start the server
    service.generate_protos()
    service.serve() 