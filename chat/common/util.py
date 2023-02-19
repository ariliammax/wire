# util.py
# in chat.common

from enum import Enum, EnumMeta
from typing import Dict, Optional


class Interface(object):
    """An abstract `interface` that will be used in e.g. `model_from_proto`
       to autogenerate the sort of useful code we would like.

        attributes:
          `_fields_enum`: An `Enum` subclass which has members of the names
                          of the field name and values of the field type.
    """
    _fields_enum: Optional[type] = None


class Model(object):
    """The abstract "models" created from `interface`s.
       Useful for making new models, or (de)serializing.
    """
    _fields: Dict[str, type] = {}

    # TODO: is this necessary? I think not necessarily, but will
    # be at a minimum useful for awkard class attributes sharing object
    # attributes names, so best to just discourage it entirely.
    _reserved_fields = ['_fields',
                        '_reserved_fields']

    def serialize(self) -> bytes:
        raise NotImplementedError()

    @classmethod
    def deserialize(cls, data: bytes):
        raise NotImplementedError()

    @staticmethod
    def model_with_fields(**fields: Dict[str, type]) -> type:
        for name in fields:
            if name in Model._reserved_fields:
                raise ValueError(f'Field \'{name!s}\' is a reserved name.')

        class __impl_model__(Model):
            # copy is likely safest here...
            _fields = {k: v for k, v in fields.items()}

        return __impl_model__.add_getters_setters()

    @classmethod
    def add_getters_setters(model):
        for name, value in model._fields.items():

            if type(value) is not type:
                raise ValueError(f'Field \'{name!s}\' with value '
                                 f'\'{value!r}\' which is not a `type`.')

            # note: you do NOT want to put `private_name` within any of the
            #       implementations that will be `setattr`ed, since then
            #       `private_name` the variable will be bound to the function.
            #       Another way would be to explicitly `del` it, but uh, that's
            #       not very pythonic...
            #
            #       For some stupid, hacky reason the default works.
            #       I guess since it puts it in the function's `__defaults__`
            #       attribute...
            private_name = f'_{name!s}'

            # the getter we'll add to `model`.
            def __impl_setter__(self: model,
                                val: Optional[value],
                                private_name: str = private_name):
                setattr(self, private_name, val)
                return self

            setattr(model, f'set_{name!s}', __impl_setter__)

            # the setter we'll add to `model`.
            def __impl_getter__(self: model,
                                private_name: str = private_name):
                return getattr(self, private_name, None)

            setattr(model, f'get_{name!s}', __impl_getter__)

        # the `__init__` we'll add to `model`.
        # this might get weird with inheritence, but as long as the inherited
        # call `add_getters_setters`, then we should be good.
        def __impl_init__(self, **kwargs) -> model:
            for name in self._fields:
                if name in kwargs:
                    getattr(self, f'set_{name!s}', lambda _: _)(kwargs
                                                                [name])
                else:
                    setattr(self, f'_{name!s}', None)

        setattr(model, '__init__', __impl_init__)

        return model.clean_getters_setters()

    @classmethod
    def clean_getters_setters(model):
        for attr_name in dir(model):
            match attr_name[:4]:
                case 'get_':
                    if attr_name[4:] not in model._fields:
                        setattr(model, attr_name, None)
                case 'set_':
                    if attr_name[4:] not in model._fields:
                        setattr(model, attr_name, None)
        return model

    @classmethod
    def add_fields(cls, **new_fields: Dict[str, type]) -> type:
        return (Model.model_with_fields(**dict(list(cls._fields.items()) +
                                               list(new_fields.items())))
                .add_getters_setters())

    @classmethod
    def omit_fields(cls, **rm_fields: Dict[str, type]) -> type:
        for fname in rm_fields:
            if fname not in cls._fields:
                raise ValueError(f'Cannot omit field \'{fname!s}\'; '
                                 f'it is not a field of {cls!s}.')
        return (Model.model_with_fields({n: t
                                         for n, t in cls._fields.items()
                                         if n not in rm_fields})
                .add_getters_setters())


def model_from_proto(iface: type) -> type:
    """Materializes a class with getters and setters from an interface.

        Raises: A `ValueError` if `iface` is not `interface` subclass,
                               if `iface._fields_enum` is not `Enum` subclass
                               if `iface._fields_enum`'s members do not have
                                 `str` names and `type` values.

        Returns: A `class` generated by the `iface : interface`.
    """
    if not issubclass(iface, Interface):
        raise ValueError(f'Arg `iface` ({iface!r}) is not a subclass of '
                         f'`interface` (type is {type(iface)!r}).')

    if not hasattr(iface, '_fields_enum'):
        raise ValueError(f'Arg `iface` ({iface!r}) does not have a '
                         f'`_fields_enum` attribute.')

    not_enum = False
    if (type(iface._fields_enum) is not Enum and
            type(iface._fields_enum) is not EnumMeta):
        not_enum = True

    if not not_enum:
        if (not issubclass(iface._fields_enum, Enum) and
                not issubclass(iface._fields_enum, EnumMeta)):
            not_enum = True

    if not_enum:
        raise ValueError(f'Arg `iface`\'s `_fields_enum` attribute '
                         f'({iface._fields_enum!r}) is not an `Enum` '
                         f'(type is {type(iface._fields_enum)!r}).')

    # we may iterate an `Enum`'s members dictionary by `__members__`.
    return Model.model_from_fields(**dict([(member.name, member.value)
                                           for _, member in
                                           iface._fields_enum.__members__
                                           .items()]))
