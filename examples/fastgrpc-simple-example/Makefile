generate-protos:
	python -m fastgrpc generate-protos fastgrpc_simple_example/server.py:service --python-out-path fastgrpc_simple_example/generated

serve:
	python fastgrpc_simple_example/server.py --proto-path fastgrpc_simple_example/proto --python-out-path fastgrpc_simple_example/generated
