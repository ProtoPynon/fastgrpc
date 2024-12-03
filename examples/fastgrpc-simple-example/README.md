1. Generate the protos

```bash
python -m fastgrpc generate-protos examples/simple_example/server.py:service --proto-path examples/simple_example/proto --python-out-path examples/simple_example/generated
```

2. Run the server

```bash
python examples/simple_example/server.py
```
