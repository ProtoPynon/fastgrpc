import sys
from pydantic import BaseModel

sys.path.append('../../')
from fastgrpc.fastgrpc import FastGRPC

# Create a service with a custom name
service = FastGRPC(service_name='Calculator')

# Example using type hints for simple parameters
@service.endpoint()
def add(a: int, b: int) -> int:
    return a + b

# Example using Pydantic models for more complex types
class GreetRequest(BaseModel):
    name: str
    title: str = ""  # Optional field with default value

class GreetResponse(BaseModel):
    message: str
    greeting_count: int

@service.endpoint()
def greet_defined_with_type_annotation(request: GreetRequest) -> GreetResponse:
    return GreetResponse(
        message=f"Hello, {request.name}!",
        greeting_count=1
    )

@service.endpoint(request_model=GreetRequest, response_model=GreetResponse)
def greet_defined_with_decorator(request):
    title_prefix = f"{request.title} " if request.title else ""
    return GreetResponse(
        message=f"Hello, {title_prefix}{request.name}!",
        greeting_count=1
    )

if __name__ == "__main__":
    # Generate the protos
    # This will generate .proto files in the /protos directory and Python files in the ./generated directory
    service.generate_protos()
    
    # Start the gRPC server
    # This will use the generated Python files from the specified output path
    service.serve()
