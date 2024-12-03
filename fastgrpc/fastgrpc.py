from functools import wraps
from python2proto import pydantic_models_to_protos
import grpc
from concurrent import futures
import os
import sys
import subprocess
from typing import Callable, Dict, Type, Any, get_type_hints
from google.protobuf.json_format import MessageToDict, ParseDict
from pydantic import BaseModel, create_model
import inspect
import stringcase
import importlib


class FastGRPC:
    def __init__(self, service_name='FastGRPCService'):
        self.service_name = service_name
        self._endpoints: Dict[str, Dict] = {}
        self._models = set()

    def endpoint(self, request_model: Type = None, response_model: Type = None):
        def decorator(func: Callable):
            # Generate request model from function signature if not provided
            if request_model is None:
                sig = inspect.signature(func)
                fields = {}
                for name, param in sig.parameters.items():
                    if param.annotation == inspect.Parameter.empty:
                        raise TypeError(f"Parameter '{name}' in function '{func.__name__}' must have a type annotation")
                    else:
                        fields[name] = (param.annotation, ...)
                RequestModel = create_model(f"{func.__name__}_Request", **fields)
                request_model_cls = RequestModel
                self._models.add(RequestModel)
            else:
                request_model_cls = request_model
                self._models.add(request_model)

            # Generate response model from function return type if not provided
            if response_model is None:
                return_annotation = get_type_hints(func).get('return', Any)
                if return_annotation is Any:
                    raise TypeError(f"Function '{func.__name__}' must have a return type annotation")
                if isinstance(return_annotation, type) and issubclass(return_annotation, BaseModel):
                    response_model_cls = return_annotation
                    self._models.add(response_model_cls)
                else:
                    ResponseModel = create_model(f"{func.__name__}_Response", result=(return_annotation, ...))
                    response_model_cls = ResponseModel
                    self._models.add(ResponseModel)
            else:
                response_model_cls = response_model
                self._models.add(response_model)

            method_name = func.__name__
            self._endpoints[method_name] = {
                'func': func,
                'request_model': request_model_cls,
                'response_model': response_model_cls
            }

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def generate_protos(self, proto_path: str = './protos', python_out_path: str = './generated'):
        import stringcase
        from python2proto import pydantic_models_to_protos

        # Convert set to list
        models_list = list(self._models)
        # Generate message definitions
        proto_messages = pydantic_models_to_protos(models_list)

        # Generate service definitions using the provided service name
        service_name_camel = stringcase.pascalcase(self.service_name)
        service_definitions = f"service {service_name_camel} {{\n"
        for method_name, endpoint_info in self._endpoints.items():
            request_model = endpoint_info['request_model']
            response_model = endpoint_info['response_model']
            service_definitions += f"  rpc {method_name} ({request_model.__name__}) returns ({response_model.__name__});\n"
        service_definitions += "}\n"

        # Combine messages and service definitions
        full_proto = proto_messages + '\n' + service_definitions

        # Write to .proto file
        os.makedirs(proto_path, exist_ok=True)
        proto_filename = f"{stringcase.snakecase(self.service_name)}.proto"
        proto_file_path = os.path.join(proto_path, proto_filename)
        with open(proto_file_path, 'w') as f:
            f.write('syntax = "proto3";\n\n')
            f.write('package fastgrpc;\n\n')
            f.write(full_proto)

        # Ensure the python_out_path directory exists
        os.makedirs(python_out_path, exist_ok=True)

        # Compile the .proto file to Python modules using protoc
        try:
            subprocess.run([
                'python', '-m', 'grpc_tools.protoc',
                f'--proto_path={proto_path}',
                f'--python_out={python_out_path}',
                f'--grpc_python_out={python_out_path}',
                proto_file_path
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error compiling .proto files: {e}")
            sys.exit(1)

    def serve(self, host='0.0.0.0', port=50051, python_out_path: str = './generated'):
        import sys
        import importlib

        # Ensure that python_out_path is in sys.path
        if python_out_path not in sys.path:
            sys.path.insert(0, python_out_path)

        # Import the generated modules based on the service name
        module_name = stringcase.snakecase(self.service_name)
        proto_module_name = f"{module_name}_pb2"
        grpc_module_name = f"{module_name}_pb2_grpc"

        proto_module = importlib.import_module(proto_module_name)
        grpc_module = importlib.import_module(grpc_module_name)

        # Dynamically get the service servicer class
        service_name_camel = stringcase.pascalcase(self.service_name)
        servicer_class_name = f'{service_name_camel}Servicer'
        servicer_base = getattr(grpc_module, servicer_class_name)

        class Servicer(servicer_base):
            def __init__(self, endpoints):
                self._endpoints = endpoints

            # Dynamically create RPC methods
            def __getattr__(self, name):
                if name in self._endpoints:
                    endpoint_info = self._endpoints[name]
                    func = endpoint_info['func']
                    request_model = endpoint_info['request_model']
                    response_model = endpoint_info['response_model']

                    # Get the corresponding protobuf message classes
                    request_pb2 = getattr(proto_module, request_model.__name__)
                    response_pb2 = getattr(proto_module, response_model.__name__)

                    def method(request, context):
                        # Convert protobuf request to Pydantic model
                        request_dict = MessageToDict(request, preserving_proto_field_name=True)
                        request_obj = request_model(**request_dict)

                        # Call the endpoint function
                        response_obj = func(**request_obj.dict())

                        # Convert response Pydantic model to protobuf
                        if isinstance(response_obj, BaseModel):
                            response_dict = response_obj.dict()
                        else:
                            response_dict = {'result': response_obj}
                        response = response_pb2()
                        ParseDict(response_dict, response)

                        return response
                    return method
                raise AttributeError(f"'Servicer' object has no attribute '{name}'")

        # Register the servicer using the dynamic service name
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_servicer_to_server = getattr(
            grpc_module,
            f'add_{service_name_camel}Servicer_to_server'
        )
        add_servicer_to_server(Servicer(self._endpoints), server)

        server.add_insecure_port(f'{host}:{port}')
        print(f'Server started at {host}:{port}')
        server.start()
        server.wait_for_termination()
