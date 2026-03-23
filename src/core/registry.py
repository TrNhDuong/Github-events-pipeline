class TransformRegistry:
    _registry = {}

    @classmethod
    def register(cls, name: str):
        def wrapper(transform_class):
            cls._registry[name] = transform_class
            return transform_class
        return wrapper

    @classmethod
    def get_transformer(cls, name: str):
        if name not in cls._registry:
            raise ValueError(f"Transform '{name}' not found")
        return cls._registry[name]()

    @classmethod
    def list_transforms(cls):
        return list(cls._registry.keys())

class ParseRegistry:
    _registry = {}

    @classmethod
    def register(cls, name: str):
        def wrapper(parse_class):
            cls._registry[name] = parse_class
            return parse_class
        return wrapper

    @classmethod
    def get_parse(cls, name: str):
        if name not in cls._registry:
            raise ValueError(f"Parse '{name}' not found")
        return cls._registry[name]()

    @classmethod
    def list_parse(cls):
        return list(cls._registry.keys())