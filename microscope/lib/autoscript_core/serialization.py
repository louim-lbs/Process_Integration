import struct
import sys

from .common import DataType, DataTypeDefinition, InvalidOperationException


class ReferenceValidity:
    UNKNOWN = 0
    VALID = 1
    INVALID = 2


class ValueSerializationException(Exception):
    def __init__(self, message):
        super().__init__(message)


class BytesBuilder(object):
    def __init__(self):
        self._bytes = bytearray()

    def add_bytes(self, new_bytes):
        self._bytes.extend(new_bytes)

    def get_data(self):
        return self._bytes


class BytesChopper(object):
    def __init__(self, data, offset=0):
        self._offset = offset
        self._data = data

    def chop(self, number_of_bytes):
        offset = self._offset
        self._offset += number_of_bytes
        return self._data[offset:(offset + number_of_bytes)]

    def bytes_left(self):
        return len(self._data) - self._offset


class ReprAttr:
    """
    ReprAttr contains information about a representative attribute to be used in object representation string.

    Here, object representation string refers to the string provided by __repr__() method.
    ReprAttr class was originally introduced to support nice __repr__() implementations of structures.
    """

    def __init__(self, attr_name, format_string):
        """
        Creates new ReprAttr containing information about a representative attribute.

        :param attr_name: Name of the attribute.
        :param format_string: Format string to be used for attribute value formatting.
        """
        self.attr_name = attr_name
        self.format_string = format_string


class StructureItem(object):
    def __init__(self, uid, dtd, value, is_optional):
        self.uid = uid
        self.dtd = dtd
        self.has_value = True
        self.value = value
        self.is_optional = is_optional

    def set_value(self, value):
        self.has_value = True
        self.value = value

    def clear(self):
        self.has_value = False
        self.value = None


class StructureBase(object):
    def __init__(self, name=""):
        self._items = dict()
        self._name = name

    def _serialize_to(self, bytes_builder: BytesBuilder, serializer):
        for uid, item in self._items.items():
            BasicValueSerializer.serialize_int32(item.uid, bytes_builder)
            serializer.serialize_value(item.dtd, item.value, bytes_builder)

    def _deserialize_from(self, chopper: BytesChopper, deserializer):
        self._clear_items()

        while chopper.bytes_left() > 0:
            uid = BasicValueDeserializer.deserialize_int32(chopper)
            dtd, value = deserializer.deserialize_value(chopper)

            if self._has_item(uid):
                item = self._items[uid]
                if dtd != item.dtd:
                    raise ValueSerializationException(self._construct_ineligible_value_error_message("deserialization", item.uid, item.dtd, item.is_optional, value))
                self._set_item(uid, value)

    def _init_item(self, uid, dtd, value, is_optional=True):
        if self._has_item(uid):
            raise InvalidOperationException(self._name + " structure item " + uid + "had already been initialized.")

        if not self._is_value_eligible(value, dtd, is_optional):
            raise InvalidOperationException(self._construct_ineligible_value_error_message("initialization", uid, dtd, is_optional, value))

        self._items[uid] = StructureItem(uid, dtd, value, is_optional)

    def _set_item(self, uid, value):
        if not self._has_item(uid):
            raise InvalidOperationException(self._name + " structure does not contain item " + uid + ".")

        item = self._items[uid]
        if not self._is_value_eligible(value, item.dtd, item.is_optional):
            raise InvalidOperationException(self._construct_ineligible_value_error_message("assignment", item.uid, item.dtd, item.is_optional, value))

        item.set_value(value)

    def _get_item(self, uid):
        if not self._has_item(uid):
            raise InvalidOperationException(self._name + " structure does not contain item " + uid + ".")

        item = self._items[uid]
        return item.value

    def _has_item(self, uid):
        return uid in self._items

    def _clear_items(self):
        for uid, item in self._items.items():
            item.clear()

    def _is_value_eligible(self, value, dtd, is_optional):
        if value is None:
            if not is_optional and (dtd == DataType.BOOL or dtd == DataType.DOUBLE or dtd == DataType.INT32 or dtd == DataType.INT64):
                return False
            else:
                return True

        if (dtd == DataType.BOOL and isinstance(value, bool)) or \
                (dtd == DataType.BYTE_ARRAY and isinstance(value, (bytearray, bytes))) or \
                (dtd == DataType.DOUBLE and isinstance(value, (float, int))) or \
                (dtd == DataType.INT32 and isinstance(value, int)) or \
                (dtd == DataType.INT64 and isinstance(value, int)) or \
                (dtd == DataType.STRING and isinstance(value, str)) or \
                (dtd.primary_id == DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID and isinstance(value, DynamicObjectHandle)) or \
                (dtd.primary_id == DataType.DYNAMIC_OBJECT_PRIMARY_ID and isinstance(value, DynamicObject)) or \
                (dtd.primary_id == DataType.LIST_PRIMARY_ID and isinstance(value, (list, tuple))) or \
                (dtd.primary_id == DataType.STRUCTURE_PRIMARY_ID and isinstance(value, StructureBase) and dtd.secondary_id == value._name):
            return True

        return False

    def _construct_ineligible_value_error_message(self, operation, uid, dtd, is_optional, value):
        value_description = "null value" if value is None else "value of " + value.__class__.__name__ + " type"
        error_message = self._name + " structure item " + str(uid) + " " + operation + " cannot proceed because the given " + value_description + \
            " is not eligible for this " + ("optional" if is_optional else "non-optional") + " item of " + repr(dtd) + " type."
        return error_message

    def _generate_repr(self, repr_attrs):
        """
        Generates object representation string according to the given representative attribute set.

        :param repr_attrs: Set of representative attributes in a form of ReprAttr object array.
        :return: Object representation string suitable for object __repr__() implementation.
        """

        repr_attr_strings = []
        for repr_attr in repr_attrs:
            attr_value = getattr(self, repr_attr.attr_name)
            if attr_value is not None:
                repr_attr_strings.append(repr_attr.attr_name + "=" + repr_attr.format_string % attr_value)

        repr_string = "%s(%s)" % (type(self).__name__, ', '.join(repr_attr_strings))
        return repr_string


class UnknownStructure(StructureBase):
    """
    UnknownStructure represents a structure not known to the local node.

    UnknownStructure is used instead of an actual structure when the type of the structure
    is not registered on the local node and deserialization mechanism can not instantiate
    it. That may happen when one of the communicating nodes is newer. Reporting failure
    is not desired in such cases because the unknown structure may be just a part
    of a bigger structure whose remaining parts can still be used normally.
    """
    
    def __init__(self, name):
        self._name = name


class StructureFactory:

    def __init__(self):
        self._internal_dict = dict()

    def register_structure_constructor(self, name: str, method):
        self._internal_dict[name] = method

    def create_structure(self, name: str):
        if name in self._internal_dict.keys():
            new_structure = self._internal_dict[name]()
        else:
            new_structure = UnknownStructure(name)

        return new_structure


class DynamicObjectHandle(object):
    __slots__ = ["id"]

    def __init__(self, _id):
        self.id = _id


class DynamicObjectHandleFactory:

    def __init__(self):
        self._internal_dict = dict()

    def register_dynamic_object_handle_constructor(self, name: str, method):
        self._internal_dict[name] = method

    def create_dynamic_object_handle(self, name: str, _id: str) -> DynamicObjectHandle:
        if name in self._internal_dict.keys():
            dynamic_object = self._internal_dict[name](_id)
            return dynamic_object
        else:
            raise ValueSerializationException("There is no dynamic object named '" + name + "' registered in factory.")


class BasicValueSerializer:

    @staticmethod
    def serialize_values(values):
        bytes_builder = BytesBuilder()

        for data_type, value in zip(values.data_types, values.values):
            BasicValueSerializer.serialize_value(data_type, value, bytes_builder)

        values.serialized_bytes = bytes_builder.get_data()

    @staticmethod
    def serialize_value(data_type: DataTypeDefinition, value, bytes_builder: BytesBuilder):
        BasicValueSerializer.serialize_data_type_definition(data_type, bytes_builder)
        BasicValueSerializer._serialize_value_internal(data_type, value, bytes_builder)

    @staticmethod
    def _serialize_value_internal(data_type, value, bytes_builder):
        if value is None or data_type == DataType.VOID:
            bytes_builder.add_bytes(int.to_bytes(ReferenceValidity.INVALID, 1, byteorder='big'))
            return

        bytes_builder.add_bytes(int.to_bytes(ReferenceValidity.VALID, 1, byteorder='big'))

        if data_type == DataType.INT32:
            BasicValueSerializer.serialize_int32(value, bytes_builder)
        elif data_type == DataType.INT64:
            BasicValueSerializer.serialize_int64(value, bytes_builder)
        elif data_type == DataType.DOUBLE:
            BasicValueSerializer.serialize_double(value, bytes_builder)
        elif data_type == DataType.BOOL:
            BasicValueSerializer.serialize_bool(value, bytes_builder)
        elif data_type == DataType.STRING:
            BasicValueSerializer.serialize_string(value, bytes_builder)
        elif data_type == DataType.BYTE_ARRAY:
            BasicValueSerializer.serialize_byte_array(value, bytes_builder)
        else:
            raise ValueSerializationException("Unsupported parameter type of 0x" + '{:02X}'.format(data_type.primary_id) + ".")

    @staticmethod
    def serialize_byte(value, bytes_builder):
        int_value = int(value)
        bytes_builder.add_bytes(int_value.to_bytes(1, byteorder='big'))

    @staticmethod
    def serialize_int32(value, bytes_builder):
        int_value = int(value)
        bytes_builder.add_bytes(struct.pack("!i", int_value))

    @staticmethod
    def serialize_int64(value, bytes_builder):
        int_value = int(value)
        bytes_builder.add_bytes(struct.pack("!q", int_value))

    @staticmethod
    def serialize_double(value, bytes_builder):
        float_value = float(value)
        bytes_builder.add_bytes(struct.pack('!d', float_value))

    @staticmethod
    def serialize_string(value, bytes_builder):
        string_value = str(value)
        string_bytes = string_value.encode('utf-8')
        BasicValueSerializer.serialize_int32(len(string_bytes), bytes_builder)
        bytes_builder.add_bytes(string_bytes)

    @staticmethod
    def serialize_bool(value, bytes_builder):
        bool_value = bool(value)
        bytes_builder.add_bytes(bytes([1]) if bool_value else bytes([0]))

    @staticmethod
    def serialize_byte_array(data, bytes_builder):
        data_bytes = bytes(data)
        BasicValueSerializer.serialize_int32(len(data_bytes), bytes_builder)
        bytes_builder.add_bytes(data_bytes)

    @staticmethod
    def serialize_data_type_definition(data_type: DataTypeDefinition, bytes_builder: BytesBuilder):
        if data_type.primary_id == DataType.DYNAMIC_OBJECT_PRIMARY_ID:
            BasicValueSerializer.serialize_byte(DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID, bytes_builder)
            BasicValueSerializer.serialize_string(data_type.secondary_id, bytes_builder)
            return

        BasicValueSerializer.serialize_byte(data_type.primary_id, bytes_builder)
        if data_type.primary_id == DataType.STRUCTURE_PRIMARY_ID or data_type.primary_id == DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID:
            BasicValueSerializer.serialize_string(data_type.secondary_id, bytes_builder)
        elif data_type.primary_id == DataType.LIST_PRIMARY_ID:
            BasicValueSerializer.serialize_data_type_definition(data_type.template_argument, bytes_builder)


class BasicValueDeserializer:

    @staticmethod
    def deserialize_values(values):
        bytes_chopper = BytesChopper(values.serialized_bytes)
        data_type, value = BasicValueDeserializer.deserialize_value(bytes_chopper)

        values.add_value(data_type, value)

    @staticmethod
    def deserialize_value(chopper: BytesChopper):
        data_type = BasicValueDeserializer.deserialize_data_type_definition(chopper)
        value = BasicValueDeserializer.deserialize_value_internal(chopper, data_type)

        return data_type, value

    @staticmethod
    def deserialize_value_internal(chopper: BytesChopper, data_type: DataTypeDefinition):
        reference_validity = chopper.chop(1)[0]
        if reference_validity == ReferenceValidity.INVALID:
            return None

        if data_type == DataType.INT32:
            value = BasicValueDeserializer.deserialize_int32(chopper)
        elif data_type == DataType.INT64:
            value = BasicValueDeserializer.deserialize_int64(chopper)
        elif data_type == DataType.DOUBLE:
            value = BasicValueDeserializer.deserialize_double(chopper)
        elif data_type == DataType.BOOL:
            value = BasicValueDeserializer.deserialize_bool(chopper)
        elif data_type == DataType.STRING:
            value = BasicValueDeserializer.deserialize_string(chopper)
        elif data_type == DataType.BYTE_ARRAY:
            value = BasicValueDeserializer.deserialize_byte_array(chopper)
        elif data_type == DataType.VOID:
            value = None
        else:
            raise ValueSerializationException("Unsupported parameter type '{}'.".format(data_type))

        return value

    @staticmethod
    def deserialize_byte(chopper: BytesChopper):
        return chopper.chop(1)[0]

    @staticmethod
    def deserialize_int32(chopper: BytesChopper):
        int_value = struct.unpack("!i", chopper.chop(4))[0]
        return int_value

    @staticmethod
    def deserialize_int64(chopper: BytesChopper):
        int_value = struct.unpack("!q", chopper.chop(8))[0]
        return int_value

    @staticmethod
    def deserialize_double(chopper: BytesChopper):
        double_value = struct.unpack("!d", chopper.chop(8))[0]
        return double_value

    @staticmethod
    def deserialize_bool(chopper: BytesChopper):
        bool_value_bytes = chopper.chop(1)
        bool_value = True if bool_value_bytes[0] != 0x00 else False
        return bool_value

    @staticmethod
    def deserialize_string(chopper: BytesChopper):
        length = BasicValueDeserializer.deserialize_int32(chopper)
        string_value = chopper.chop(length).decode('utf-8')
        return string_value

    @staticmethod
    def deserialize_byte_array(chopper: BytesChopper):
        length = BasicValueDeserializer.deserialize_int32(chopper)
        data_bytes = chopper.chop(length)
        return data_bytes

    @staticmethod
    def deserialize_data_type_definition(chopper: BytesChopper):
        primary_id = BasicValueDeserializer.deserialize_byte(chopper)
        if primary_id == DataType.STRUCTURE_PRIMARY_ID or primary_id == DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID or primary_id == DataType.DYNAMIC_OBJECT_PRIMARY_ID:
            secondary_id = BasicValueDeserializer.deserialize_string(chopper)
            dtd = DataTypeDefinition(primary_id=primary_id, secondary_id=secondary_id)
        elif primary_id == DataType.LIST_PRIMARY_ID:
            template_argument = BasicValueDeserializer.deserialize_data_type_definition(chopper)
            dtd = DataTypeDefinition(primary_id=primary_id, template_argument=template_argument)
        else:
            dtd = DataTypeDefinition(primary_id=primary_id)
        return dtd


class AdvancedValueSerializer:

    def serialize_values(self, values):
        bytes_builder = BytesBuilder()

        for data_type, value in zip(values.data_types, values.values):
            self.serialize_value(data_type, value, bytes_builder)

        values.serialized_bytes = bytes_builder.get_data()

    def serialize_value(self, data_type: DataTypeDefinition, value, bytes_builder: BytesBuilder):
        self.check_for_circular_references(value)
        BasicValueSerializer.serialize_data_type_definition(data_type, bytes_builder)
        self._serialize_value_internal(data_type, value, bytes_builder)

    def _serialize_value_internal(self, data_type, value, bytes_builder):
        if value is None or data_type == DataType.VOID:
            bytes_builder.add_bytes(int.to_bytes(ReferenceValidity.INVALID, 1, byteorder='big'))
            return

        bytes_builder.add_bytes(int.to_bytes(ReferenceValidity.VALID, 1, byteorder='big'))

        if data_type == DataType.INT32:
            BasicValueSerializer.serialize_int32(value, bytes_builder)
        elif data_type == DataType.INT64:
            BasicValueSerializer.serialize_int64(value, bytes_builder)
        elif data_type == DataType.DOUBLE:
            BasicValueSerializer.serialize_double(value, bytes_builder)
        elif data_type == DataType.BOOL:
            BasicValueSerializer.serialize_bool(value, bytes_builder)
        elif data_type == DataType.STRING:
            BasicValueSerializer.serialize_string(value, bytes_builder)
        elif data_type == DataType.BYTE_ARRAY:
            BasicValueSerializer.serialize_byte_array(value, bytes_builder)
        elif data_type.primary_id == DataType.STRUCTURE_PRIMARY_ID:
            self.serialize_structure(value, bytes_builder)
        elif data_type.primary_id == DataType.LIST_PRIMARY_ID:
            self.serialize_list(data_type, value, bytes_builder)
        elif data_type.primary_id == DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID:
            self.serialize_dynamic_object_handle(value, bytes_builder)
        elif data_type.primary_id == DataType.DYNAMIC_OBJECT_PRIMARY_ID:
            self.serialize_dynamic_object(value, bytes_builder)
        else:
            raise ValueSerializationException("Unsupported parameter type of 0x" + '{:02X}'.format(data_type.primary_id) + ".")

    def serialize_structure(self, structure: StructureBase, bytes_builder: BytesBuilder):
        internal_bytes_builder = BytesBuilder()
        structure._serialize_to(internal_bytes_builder, self)
        bytes = internal_bytes_builder.get_data()

        BasicValueSerializer.serialize_byte_array(bytes, bytes_builder)

    def serialize_list(self, data_type: DataTypeDefinition, list, bytes_builder: BytesBuilder):
        BasicValueSerializer.serialize_int32(len(list), bytes_builder)
        for item in list:
            self._serialize_value_internal(data_type.template_argument, item, bytes_builder)

    def serialize_dynamic_object_handle(self, dynamic_object_handle: DynamicObjectHandle, bytes_builder: BytesBuilder):
        BasicValueSerializer.serialize_string(dynamic_object_handle.id, bytes_builder)

    def serialize_dynamic_object(self, dynamic_object, bytes_builder: BytesBuilder):
        BasicValueSerializer.serialize_string(dynamic_object._handle.id, bytes_builder)

    def check_for_circular_references(self, item, list_of_objects=None):
        if not isinstance(item, (list, tuple, StructureBase)):
            return

        if list_of_objects is None:
            list_of_objects = list()

        for obj in list_of_objects:
            if obj is item:
                raise ValueSerializationException("Circular references of objects are not supported in serialization.")

        list_of_objects.append(item)

        if isinstance(item, (list, tuple)):
            [self.check_for_circular_references(i, list_of_objects) for i in item]
        else:  # it's StructureBase
            [self.check_for_circular_references(obj, list_of_objects) for id, obj in
             item._items.items()]

        list_of_objects.remove(item)


class AdvancedValueDeserializer:

    def __init__(self):
        self._structure_factory = StructureFactory()
        self._dynamic_object_handle_factory = DynamicObjectHandleFactory()

    @property
    def structure_factory(self):
        return self._structure_factory

    @property
    def dynamic_object_handle_factory(self):
        return self._dynamic_object_handle_factory

    def deserialize_values(self, values):
        bytes_chopper = BytesChopper(values.serialized_bytes)
        data_type, value = self.deserialize_value(bytes_chopper)

        values.add_value(data_type, value)

    def deserialize_value(self, chopper: BytesChopper):
        data_type = BasicValueDeserializer.deserialize_data_type_definition(chopper)
        value = self.deserialize_value_internal(chopper, data_type)

        return data_type, value

    def deserialize_value_internal(self, chopper: BytesChopper, data_type: DataTypeDefinition):
        reference_validity = chopper.chop(1)[0]
        if reference_validity == ReferenceValidity.INVALID:
            return None

        if data_type == DataType.INT32:
            value = BasicValueDeserializer.deserialize_int32(chopper)
        elif data_type == DataType.INT64:
            value = BasicValueDeserializer.deserialize_int64(chopper)
        elif data_type == DataType.DOUBLE:
            value = BasicValueDeserializer.deserialize_double(chopper)
        elif data_type == DataType.BOOL:
            value = BasicValueDeserializer.deserialize_bool(chopper)
        elif data_type == DataType.STRING:
            value = BasicValueDeserializer.deserialize_string(chopper)
        elif data_type == DataType.BYTE_ARRAY:
            value = BasicValueDeserializer.deserialize_byte_array(chopper)
        elif data_type.primary_id == DataType.STRUCTURE_PRIMARY_ID:
            value = self.deserialize_structure(chopper, data_type)
        elif data_type.primary_id == DataType.LIST_PRIMARY_ID:
            value = self.deserialize_list(chopper, data_type)
        elif data_type.primary_id == DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID:
            value = self.deserialize_dynamic_object_handle(chopper, data_type)
        elif data_type.primary_id == DataType.DYNAMIC_OBJECT_PRIMARY_ID:
            value = self.deserialize_dynamic_object_handle(chopper, data_type)
        elif data_type == DataType.VOID:
            value = None
        else:
            raise ValueSerializationException("Unsupported parameter type '{}'.".format(data_type))

        return value

    def deserialize_structure(self, chopper: BytesChopper, data_type: DataTypeDefinition):
        data = BasicValueDeserializer.deserialize_byte_array(chopper)
        new_structure = self._structure_factory.create_structure(data_type.secondary_id)
        internal_bytes_chopper = BytesChopper(data)
        new_structure._deserialize_from(internal_bytes_chopper, self)
        return new_structure

    def deserialize_list(self, chopper: BytesChopper, data_type: DataTypeDefinition):
        size = BasicValueDeserializer.deserialize_int32(chopper)
        result = list()
        for i in range(0, size):
            item = self.deserialize_value_internal(chopper, data_type.template_argument)
            result.append(item)
        return result

    def deserialize_dynamic_object_handle(self, chopper: BytesChopper, data_type: DataTypeDefinition) -> DynamicObjectHandle:
        identifier = BasicValueDeserializer.deserialize_string(chopper)
        return self._dynamic_object_handle_factory.create_dynamic_object_handle(data_type.secondary_id, identifier)
