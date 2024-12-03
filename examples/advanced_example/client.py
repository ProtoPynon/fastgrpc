import grpc
from generated.advanced_service_pb2_grpc import AdvancedServiceStub
from generated.advanced_service_pb2 import Item, Order, OrderSummary, ChatMessage
from google.protobuf.empty_pb2 import Empty

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = AdvancedServiceStub(channel)

        # Create an order
        items = [
            Item(id=1, name="Widget", price=10.99),
            Item(id=2, name="Gadget", price=15.49)
        ]
        order = Order(order_id=1, items=items)
        response = stub.create_order(order)
        print("Created Order:", response)

        # Get the order
        response = stub.get_order(Order(order_id=1))
        print("Retrieved Order:", response)

        # List orders (server-side streaming)
        print("Listing Orders:")
        for order in stub.list_orders(Empty()):
            print(order)

        # Stream orders (client-side streaming)
        orders = [
            Order(order_id=2, items=[Item(id=3, name="Thingy", price=5.99)]),
            Order(order_id=3, items=[Item(id=4, name="Doohickey", price=2.99)])
        ]
        order_iterator = iter(orders)
        summary = stub.stream_orders(order_iterator)
        print("Order Summary:", summary)

        # Bidirectional streaming (chat)
        def message_generator():
            messages = [
                ChatMessage(user="Client", message="Hello!"),
                ChatMessage(user="Client", message="How are you?"),
                ChatMessage(user="Client", message="Goodbye!")
            ]
            for msg in messages:
                yield msg

        responses = stub.chat(message_generator())
        for response in responses:
            print("Chat Response:", response)

if __name__ == "__main__":
    run()