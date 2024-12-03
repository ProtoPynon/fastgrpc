import argparse
from .fastgrpc import FastGRPC
import importlib.util
import sys

def load_service(path):
    # Split the path into file path and variable name
    splits = path.split(':')
    file_path, var_name = splits[0], splits[1] if len(splits) > 1 else 'service'
    
    # Load the module from the file path
    spec = importlib.util.spec_from_file_location("module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Get the service variable
    return getattr(module, var_name)

def main():
    parser = argparse.ArgumentParser(description='FastGRPC CLI')
    parser.add_argument('command', choices=['generate-protos', 'serve'], help='Command to execute')
    parser.add_argument('service_path', help='Path to service file and variable (e.g., ./app.py:service)')
    parser.add_argument('--proto-path', default='./protos', help='Path to generate .proto files')
    parser.add_argument('--python-out-path', default='./generated', help='Path to output generated Python files')
    parser.add_argument('--service-name', help='Name of the gRPC service')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=50051, help='Port to bind the server to')
    parser.add_argument('--no-rebuild-protos', action='store_true', help='Do not rebuild .proto files before serving')
    args = parser.parse_args()

    service = load_service(args.service_path)

    if args.service_name:
        # Update the service name if provided
        service.service_name = args.service_name

    if args.command == 'generate-protos':
        service.generate_protos(proto_path=args.proto_path, python_out_path=args.python_out_path)
    elif args.command == 'serve':
        # Optionally rebuild protos before serving
        if not args.no_rebuild_protos:
            service.generate_protos(proto_path=args.proto_path, python_out_path=args.python_out_path)
        service.serve(host=args.host, port=args.port, python_out_path=args.python_out_path)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
