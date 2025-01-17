"""Functional programming utilities."""


def bind(func, *bind_args, **bind_kwargs):
    """Bind arguments to a function."""

    def _bound_fn(*args, **kwargs):
        kwargs = bind_kwargs | kwargs
        iargs = iter(args)
        args = (next(iargs) if arg is ... else arg for arg in bind_args)
        return func(*args, *iargs, **kwargs)

    return _bound_fn
