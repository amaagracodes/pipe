# Your first op

TODO: the "hello world" — call the built-in `echo`, then write a `Pipe`.

## Call a built-in op

```python
import pipe

pipe.echo("hi")  # 'hi'
```

## Write your own

TODO: subclass `Pipe`, implement `forward`, call it. Keep it pure.

```python
class Upper(pipe.Pipe):
    def forward(self, data: str) -> str:
        return data.upper()

Upper()("hi")  # 'HI'
```

TODO: next steps — link to Streaming and Composing.
