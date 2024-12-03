import grpc
from typing import TYPE_CHECKING
import importlib
import sys
import os

from fastgrpc_simple_example.generated.calculator_pb2_grpc import CalculatorStub
from fastgrpc_simple_example.generated.calculator_pb2 import GreetRequest, GreetResponse

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = CalculatorStub(channel)

        # Test simple addition
        response = stub.add(type('Request', (), {'a': 5, 'b': 3})())
        print(f"5 + 3 = {response.result}")

        # Test greet with type annotation
        request = GreetRequest(name="Alice")
        response = stub.greet_defined_with_type_annotation(request)
        print(f"Greeting 1: {response.message} (Count: {response.greeting_count})")

        # Test greet with decorator and title
        request = GreetRequest(name="Bob", title="Dr.")
        response = stub.greet_defined_with_decorator(request)
        print(f"Greeting 2: {response.message} (Count: {response.greeting_count})")

if __name__ == "__main__":
    run()
