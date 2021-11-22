import unittest

from .serialization import *
from .common import InvalidOperationException


class SerializationTestsHelper:
    INT32_VALUE1 = 305419896
    INT32_VALUE2 = -2147483648
    DOUBLE_VALUE1 = 123451234512345  # most accurate representation is 1.23451234512345E14
    STRING_VALUE1 = "ABCD"
    BYTE_ARRAY1 = bytes([0x12, 0x34, 0x56, 0x78, 0x90])
    TRUE_BOOL_SERIALIZED_BYTES = bytes([DataType.BOOL.primary_id, ReferenceValidity.VALID, 0x01])
    FALSE_BOOL_SERIALIZED_BYTES = bytes([DataType.BOOL.primary_id, ReferenceValidity.VALID, 0x00])
    EMPTY_STRING_SERIALIZED_BYTES = bytes([DataType.STRING.primary_id, ReferenceValidity.VALID, 0x00, 0x00, 0x00, 0x00])
    NULL_STRING_SERIALIZED_BYTES = bytes([DataType.STRING.primary_id, ReferenceValidity.INVALID])
    EMPTY_BYTE_ARRAY_SERIALIZED_BYTES = bytes([DataType.BYTE_ARRAY.primary_id, ReferenceValidity.VALID, 0x00, 0x00, 0x00, 0x00])
    NULL_BYTE_ARRAY_SERIALIZED_BYTES = bytes([DataType.BYTE_ARRAY.primary_id, ReferenceValidity.INVALID])

    @staticmethod
    def provide_int32_value1_serialized_bytes():
        data_type_definition_bytes = bytes([DataType.INT32.primary_id])
        reference_validity_byte = bytes([ReferenceValidity.VALID])
        integral_number_bytes = bytes([0x12, 0x34, 0x56, 0x78])
        int32_value_bytes = data_type_definition_bytes + reference_validity_byte + integral_number_bytes

        return int32_value_bytes

    @staticmethod
    def provide_int32_value2_serialized_bytes():
        data_type_definition_bytes = bytes([DataType.INT32.primary_id])
        reference_validity_byte = bytes([ReferenceValidity.VALID])
        integral_number_bytes = bytes([0x80, 0x00, 0x00, 0x00])
        int32_value_bytes = data_type_definition_bytes + reference_validity_byte + integral_number_bytes

        return int32_value_bytes

    @staticmethod
    def provide_double_value1_serialized_bytes():
        data_type_definition_bytes = bytes([DataType.DOUBLE.primary_id])
        reference_validity_byte = bytes([ReferenceValidity.VALID])
        floating_point_number_bytes = bytes([0x42, 0xDC, 0x11, 0xCE, 0xBE, 0xBB, 0x76, 0x40])  # 0x42DC11CEBEBB7640
        double_value_bytes = data_type_definition_bytes + reference_validity_byte + floating_point_number_bytes

        return double_value_bytes

    @staticmethod
    def provide_string_value1_serialized_bytes():
        data_type_definition_bytes = bytes([DataType.STRING.primary_id])
        reference_validity_byte = bytes([ReferenceValidity.VALID])
        string_length_bytes = bytes([0x00, 0x00, 0x00, 0x04])
        utf8_string_bytes = bytes([ord('A'), ord('B'), ord('C'), ord('D')])
        string_value_bytes = data_type_definition_bytes + reference_validity_byte + string_length_bytes + utf8_string_bytes

        return string_value_bytes

    @staticmethod
    def provide_byte_array1_serialized_bytes():
        data_type_definition_bytes = bytes([DataType.BYTE_ARRAY.primary_id])
        reference_validity_byte = bytes([ReferenceValidity.VALID])
        byte_array_length_bytes = bytes([0x00, 0x00, 0x00, 0x05])
        byte_array_content_bytes = bytes([0x12, 0x34, 0x56, 0x78, 0x90])
        byte_array_bytes = data_type_definition_bytes + reference_validity_byte + byte_array_length_bytes + byte_array_content_bytes

        return byte_array_bytes

    @staticmethod
    def provide_test_structure1_serialized_bytes():
        data_type_definition_bytes = bytes([DataType.STRUCTURE_PRIMARY_ID, 0x00, 0x00, 0x00, 0x0E, ord('T'), ord('e'), ord('s'), ord('t'), ord('S'), ord('t'), ord('r'), ord('u'), ord('c'), ord('t'), ord('u'), ord('r'), ord('e'), ord('1')])
        reference_validity_byte = bytes([ReferenceValidity.VALID])
        content_length_bytes = bytes([0x00, 0x00, 0x00, 0x16])
        item1_bytes = bytes([0x00, 0x00, 0x00, 0x01, DataType.INT32.primary_id, 0x01, 0x00, 0x00, 0x00, 0x01])  # 1st item: ID, DTD, RVF, value of 1
        item2_bytes = bytes([0x00, 0x00, 0x00, 0x02, DataType.STRING.primary_id, 0x01, 0x00, 0x00, 0x00, 0x02, ord('S'), ord('1')])  # 2nd item: ID, DTD, RVF, value length, value of 'S1'
        test_structure1_bytes = data_type_definition_bytes + reference_validity_byte + content_length_bytes + item1_bytes + item2_bytes
        return test_structure1_bytes

    @staticmethod
    def provide_list1_serialized_bytes():
        data_type_definition_bytes = bytes([DataType.LIST_PRIMARY_ID, DataType.INT32.primary_id])
        reference_validity_byte = bytes([ReferenceValidity.VALID])
        item_count_bytes = bytes([0x00, 0x00, 0x00, 0x03])
        item1_bytes = bytes([0x01, 0x00, 0x00, 0x00, 0x01])  # 1st item: RVF, value of 1
        item2_bytes = bytes([0x01, 0x00, 0x00, 0x00, 0x02])  # 2nd item: RVF, value of 2
        item3_bytes = bytes([0x01, 0x00, 0x00, 0x00, 0x03])  # 3rd item: RVF, value of 3
        list1_bytes = data_type_definition_bytes + reference_validity_byte + item_count_bytes + item1_bytes + item2_bytes + item3_bytes
        return list1_bytes

    @staticmethod
    def create_test_structure1():
        return TestStructure1()


class SerializerTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test__serialize_int__when_int32_value1_is_given__returns_int32_value1_serialized_bytes(self):
        expected_serialized_bytes = SerializationTestsHelper.provide_int32_value1_serialized_bytes()
        bytes_builder = BytesBuilder()

        BasicValueSerializer.serialize_value(DataType.INT32, SerializationTestsHelper.INT32_VALUE1, bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(expected_serialized_bytes, serialized_bytes)

    def test__serialize_int__when_int32_value2_is_given__returns_int32_value2_serialized_bytes(self):
        expected_serialized_bytes = SerializationTestsHelper.provide_int32_value2_serialized_bytes()
        bytes_builder = BytesBuilder()

        BasicValueSerializer.serialize_value(DataType.INT32, SerializationTestsHelper.INT32_VALUE2, bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(expected_serialized_bytes, serialized_bytes)

    def test_serialize_double__when_double_value1_is_given__returns_double_value_serialized_bytes(self):
        expected_serialized_bytes = SerializationTestsHelper.provide_double_value1_serialized_bytes()
        bytes_builder = BytesBuilder()

        BasicValueSerializer.serialize_value(DataType.DOUBLE, SerializationTestsHelper.DOUBLE_VALUE1, bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(expected_serialized_bytes, serialized_bytes)

    def test__serialize_value__when_true_bool_is_given__returns_true_bool_serialized_bytes(self):
        bytes_builder = BytesBuilder()

        BasicValueSerializer.serialize_value(DataType.BOOL, True, bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(SerializationTestsHelper.TRUE_BOOL_SERIALIZED_BYTES, serialized_bytes)

    def test__serialize_value__when_false_bool_is_given__returns_false_bool_serialized_bytes(self):
        bytes_builder = BytesBuilder()

        BasicValueSerializer.serialize_value(DataType.BOOL, False, bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(SerializationTestsHelper.FALSE_BOOL_SERIALIZED_BYTES, serialized_bytes)

    def test__serialize_value__when_string_value1_is_given__returns_string_value1_serialized_bytes(self):
        expected_serialized_bytes = SerializationTestsHelper.provide_string_value1_serialized_bytes()
        bytes_builder = BytesBuilder()

        BasicValueSerializer.serialize_value(DataType.STRING, SerializationTestsHelper.STRING_VALUE1, bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(expected_serialized_bytes, serialized_bytes)

    def test__serialize_value__when_empty_string_is_given__returns_empty_string_serialized_bytes(self):
        bytes_builder = BytesBuilder()

        BasicValueSerializer.serialize_value(DataType.STRING, "", bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(SerializationTestsHelper.EMPTY_STRING_SERIALIZED_BYTES, serialized_bytes)

    def test__serialize_value__when_null_string_is_given__returns_null_string_serialized_bytes(self):
        bytes_builder = BytesBuilder()

        BasicValueSerializer.serialize_value(DataType.STRING, None, bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(SerializationTestsHelper.NULL_STRING_SERIALIZED_BYTES, serialized_bytes)

    def test__serialize_value__when_byte_array1_is_given__returns_byte_array1_serialized_bytes(self):
        expected_serialized_bytes = SerializationTestsHelper.provide_byte_array1_serialized_bytes()
        bytes_builder = BytesBuilder()

        BasicValueSerializer.serialize_value(DataType.BYTE_ARRAY, SerializationTestsHelper.BYTE_ARRAY1, bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(expected_serialized_bytes, serialized_bytes)

    def test__serialize_value__when_empty_byte_array_is_given__returns_empty_byte_array_serialized_bytes(self):
        bytes_builder = BytesBuilder()

        BasicValueSerializer.serialize_value(DataType.BYTE_ARRAY, bytes(), bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(SerializationTestsHelper.EMPTY_BYTE_ARRAY_SERIALIZED_BYTES, serialized_bytes)

    def test__serialize_value__when_null_byte_array_is_given__returns_null_byte_array_serialized_bytes(self):
        bytes_builder = BytesBuilder()

        BasicValueSerializer.serialize_value(DataType.BYTE_ARRAY, None, bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(SerializationTestsHelper.NULL_BYTE_ARRAY_SERIALIZED_BYTES, serialized_bytes)

    def test__serialize_value__when_test_structure1_is_given__returns_test_structure1_serialized_bytes(self):
        advanced_value_serializer = AdvancedValueSerializer()
        data_type_definition = DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, "TestStructure1")
        test_structure1 = TestStructure1()
        test_structure1._set_item(1, 0x01)
        test_structure1._set_item(2, "S1")
        bytes_builder = BytesBuilder()

        advanced_value_serializer.serialize_value(data_type_definition, test_structure1, bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(SerializationTestsHelper.provide_test_structure1_serialized_bytes(), serialized_bytes)

    def test__serialize_value__when_list1_is_given__returns_list1_serialized_bytes(self):
        advanced_value_serializer = AdvancedValueSerializer()
        data_type_definition = DataTypeDefinition(DataType.LIST_PRIMARY_ID, template_argument=DataType.INT32)
        list1 = [0x01, 0x02, 0x03]
        bytes_builder = BytesBuilder()

        advanced_value_serializer.serialize_value(data_type_definition, list1, bytes_builder)

        serialized_bytes = bytes_builder.get_data()
        self.assertEqual(SerializationTestsHelper.provide_list1_serialized_bytes(), serialized_bytes)

    def test__serialize_value__when_unknown_serialized_data_type_is_given__throws_proper_exception(self):
        advanced_value_serializer = AdvancedValueSerializer()
        bytes_builder = BytesBuilder()

        proper_exception_thrown = False
        try:
            advanced_value_serializer.serialize_value(DataType.UNKNOWN, object(), bytes_builder)
        except ValueSerializationException:
            proper_exception_thrown = True

        self.assertTrue(proper_exception_thrown)


class DeserializerTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test__deserialize_value__when_int32_value1_serialized_bytes_are_given__returns_int32_value1(self):
        serialized_bytes = SerializationTestsHelper.provide_int32_value1_serialized_bytes()
        bytes_chopper = BytesChopper(serialized_bytes)

        data_type, value = BasicValueDeserializer.deserialize_value(bytes_chopper)

        self.assertEqual(SerializationTestsHelper.INT32_VALUE1, value)
        self.assertEqual(DataType.INT32, data_type)

    def test__deserialize_value__when_int32_value2_serialized_bytes_are_given__returns_int32_value2(self):
        serialized_bytes = SerializationTestsHelper.provide_int32_value2_serialized_bytes()
        bytes_chopper = BytesChopper(serialized_bytes)

        data_type, value = BasicValueDeserializer.deserialize_value(bytes_chopper)

        self.assertEqual(SerializationTestsHelper.INT32_VALUE2, value)
        self.assertEqual(DataType.INT32, data_type)

    def test__deserialize_value__when_double_value1_serialized_bytes_are_given__returns_double_value1(self):
        serialized_bytes = SerializationTestsHelper.provide_double_value1_serialized_bytes()
        bytes_chopper = BytesChopper(serialized_bytes)

        data_type, value = BasicValueDeserializer.deserialize_value(bytes_chopper)

        self.assertEqual(SerializationTestsHelper.DOUBLE_VALUE1, value)
        self.assertEqual(DataType.DOUBLE, data_type)

    def test__deserialize_value__when_true_bool_serialized_bytes_are_given__returns_true_boolean(self):
        bytes_chopper = BytesChopper(SerializationTestsHelper.TRUE_BOOL_SERIALIZED_BYTES)

        data_type, value = BasicValueDeserializer.deserialize_value(bytes_chopper)

        self.assertEqual(True, value)
        self.assertEqual(DataType.BOOL, data_type)

    def test__deserialize_value__when_false_bool_serialized_bytes_are_given__returns_false_boolean(self):
        bytes_chopper = BytesChopper(SerializationTestsHelper.FALSE_BOOL_SERIALIZED_BYTES)

        data_type, value = BasicValueDeserializer.deserialize_value(bytes_chopper)

        self.assertEqual(False, value)
        self.assertEqual(DataType.BOOL, data_type)

    def test__deserialize_value__when_string_value1_serialized_bytes_are_given__returns_string_value1(self):
        serialized_bytes = SerializationTestsHelper.provide_string_value1_serialized_bytes()
        bytes_chopper = BytesChopper(serialized_bytes)

        data_type, value = BasicValueDeserializer.deserialize_value(bytes_chopper)

        self.assertEqual(SerializationTestsHelper.STRING_VALUE1, value)
        self.assertEqual(DataType.STRING, data_type)

    def test__deserialize_value__when_empty_string_serialized_bytes_are_given__returns_empty_string(self):
        bytes_chopper = BytesChopper(SerializationTestsHelper.EMPTY_STRING_SERIALIZED_BYTES)

        data_type, value = BasicValueDeserializer.deserialize_value(bytes_chopper)

        self.assertEqual("", value)
        self.assertEqual(DataType.STRING, data_type)

    def test__deserialize_value__when_null_string_serialized_bytes_are_given__returns_null_string(self):
        bytes_chopper = BytesChopper(SerializationTestsHelper.NULL_STRING_SERIALIZED_BYTES)

        data_type, value = BasicValueDeserializer.deserialize_value(bytes_chopper)

        self.assertEqual(None, value)
        self.assertEqual(DataType.STRING, data_type)

    def test__deserialize_value__when_byte_array1_serialized_bytes_are_given__returns_byte_array1(self):
        serialized_bytes = SerializationTestsHelper.provide_byte_array1_serialized_bytes()
        bytes_chopper = BytesChopper(serialized_bytes)

        data_type, value = BasicValueDeserializer.deserialize_value(bytes_chopper)

        self.assertEqual(SerializationTestsHelper.BYTE_ARRAY1, value)
        self.assertEqual(DataType.BYTE_ARRAY, data_type)

    def test__deserialize_value__when_empty_byte_array_serialized_bytes_are_given__returns_empty_byte_array(self):
        bytes_chopper = BytesChopper(SerializationTestsHelper.EMPTY_BYTE_ARRAY_SERIALIZED_BYTES)

        data_type, value = BasicValueDeserializer.deserialize_value(bytes_chopper)

        self.assertEqual(bytes(), value)
        self.assertEqual(DataType.BYTE_ARRAY, data_type)

    def test__deserialize_value__when_null_byte_array_serialized_bytes_are_given__returns_null_byte_array(self):
        bytes_chopper = BytesChopper(SerializationTestsHelper.NULL_BYTE_ARRAY_SERIALIZED_BYTES)

        data_type, value = BasicValueDeserializer.deserialize_value(bytes_chopper)

        self.assertEqual(None, value)
        self.assertEqual(DataType.BYTE_ARRAY, data_type)

    def test__deserialize_value__when_test_structure1_serialized_bytes_are_given__returns_test_structure1(self):
        advanced_value_deserializer = AdvancedValueDeserializer()
        bytes_chopper = BytesChopper(SerializationTestsHelper.provide_test_structure1_serialized_bytes())
        advanced_value_deserializer.structure_factory.register_structure_constructor("TestStructure1", SerializationTestsHelper.create_test_structure1)

        data_type, value = advanced_value_deserializer.deserialize_value(bytes_chopper)

        self.assertEqual(DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, "TestStructure1"), data_type)
        self.assertIsInstance(value, TestStructure1)
        self.assertEqual(value._get_item(1), 0x01)
        self.assertEqual(value._get_item(2), "S1")

    def test__deserialize_value__when_list1_serialized_bytes_are_given__returns_list1(self):
        advanced_value_deserializer = AdvancedValueDeserializer()
        bytes_chopper = BytesChopper(SerializationTestsHelper.provide_list1_serialized_bytes())

        data_type, value = advanced_value_deserializer.deserialize_value(bytes_chopper)

        self.assertEqual(DataTypeDefinition(DataType.LIST_PRIMARY_ID, template_argument=DataType.INT32), data_type)
        self.assertIsInstance(value, list)
        self.assertEqual(value, [0x01, 0x02, 0x03])

    def test__deserialize_value__when_unknown_serialized_data_type_is_given__throws_proper_exception(self):
        advanced_value_deserializer = AdvancedValueDeserializer()
        bytes_chopper = BytesChopper([0x00, 0x00])

        proper_exception_thrown = False
        try:
            advanced_value_deserializer.deserialize_value(bytes_chopper)
        except ValueSerializationException:
            proper_exception_thrown = True

        self.assertTrue(proper_exception_thrown)


class TestStructure1(StructureBase):
    def __init__(self):
        super(TestStructure1, self).__init__()
        self._name = "TestStructure1"

        self._init_item(1, DataType.INT32, None, True)
        self._init_item(2, DataType.STRING, None, False)


class StructureFactoryTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test__create_instance__when_structure_type_is_registered__returns_requested_structure_instance(self):
        structure_factory = StructureFactory()
        structure_factory.register_structure_constructor("TestStructure1", SerializationTestsHelper.create_test_structure1)

        test_structure1 = structure_factory.create_structure("TestStructure1")

        self.assertIsInstance(test_structure1, TestStructure1)

    def test__create_instance__when_structure_type_is_not_registered__returns_unknown_structure_instance(self):
        structure_factory = StructureFactory()
        structure_factory.register_structure_constructor("TestStructure1", SerializationTestsHelper.create_test_structure1)

        test_structure1 = structure_factory.create_structure("TestStructure2")

        self.assertIsInstance(test_structure1, UnknownStructure)


class TestDynamicObject1Handle(DynamicObjectHandle):
    def __init__(self, id):
        super(TestDynamicObject1Handle, self).__init__(id)


class DynamicObjectHandleFactoryTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test__create_instance__when_dynamic_object_type_is_registered__returns_requested_dynamic_object_handle(self):
        dynamic_object_handle_factory = DynamicObjectHandleFactory()
        dynamic_object_handle_factory.register_dynamic_object_handle_constructor("TestDynamicObject1", DynamicObjectHandleFactoryTests.__create_test_dynamic_object1_handle)

        test_dynamic_object1_handle = dynamic_object_handle_factory.create_dynamic_object_handle("TestDynamicObject1", "ID1")

        self.assertIsInstance(test_dynamic_object1_handle, TestDynamicObject1Handle)
        self.assertEqual("ID1", test_dynamic_object1_handle.id)

    def test__create_instance__when_dynamic_object_type_is_not_registered__throws_proper_exception(self):
        dynamic_object_handle_factory = DynamicObjectHandleFactory()
        dynamic_object_handle_factory.register_dynamic_object_handle_constructor("TestDynamicObject1", DynamicObjectHandleFactoryTests.__create_test_dynamic_object1_handle)

        proper_exception_thrown = False
        try:
            dynamic_object_handle_factory.create_dynamic_object_handle("TestDynamicObject2", "ID1")
        except ValueSerializationException:
            proper_exception_thrown = True

        self.assertTrue(proper_exception_thrown)

    @staticmethod
    def __create_test_dynamic_object1_handle(id):
        return TestDynamicObject1Handle(id)


class StructureBaseTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test__init_item__non_optional_int_not_null__initializes_item_accordingly(self):
        structure = StructureBase("structure")
        structure._init_item(1, DataType.INT32, 100, False)

        item_value = structure._get_item(1)
        self.assertEqual(int, type(item_value))
        self.assertEqual(100, item_value)

    def test__init_item__optional_int_null__initializes_item_accordingly(self):
        structure = StructureBase("structure")
        structure._init_item(1, DataType.INT32, None, True)

        item_value = structure._get_item(1)
        self.assertIsNone(item_value)

    def test__init_item__non_optional_string_not_null__initializes_item_accordingly(self):
        structure = StructureBase("structure")
        structure._init_item(1, DataType.STRING, "ABC", False)

        item_value = structure._get_item(1)
        self.assertEqual(str, type(item_value))
        self.assertEqual("ABC", item_value)

    def test__init_item__optional_string_null__initializes_item_accordingly(self):
        structure = StructureBase("structure")
        structure._init_item(1, DataType.STRING, None, True)

        item_value = structure._get_item(1)
        self.assertIsNone(item_value)

    def test__init_item__byte_array__initializes_item_accordingly1(self):
        structure = StructureBase("structure")
        structure._init_item(1, DataType.BYTE_ARRAY, bytearray([4, 5, 3]), False)

        item_value = structure._get_item(1)
        self.assertEqual(bytearray, type(item_value))
        self.assertEqual(bytearray([4, 5, 3]), item_value)

    def test__init_item__byte_array__initializes_item_accordingly2(self):
        structure = StructureBase("structure")
        structure._init_item(1, DataType.BYTE_ARRAY, bytes([4, 5, 3]), False)

        item_value = structure._get_item(1)
        self.assertEqual(bytes, type(item_value))
        self.assertEqual(bytes([4, 5, 3]), item_value)

    def test__init_item__list__initializes_item_accordingly1(self):
        structure = StructureBase("structure")
        structure._init_item(1, DataTypeDefinition(DataType.LIST_PRIMARY_ID, template_argument=DataType.INT32), [4, 5, 3], False)

        item_value = structure._get_item(1)
        self.assertEqual(list, type(item_value))
        self.assertEqual([4, 5, 3], item_value)

    def test__init_item__list__initializes_item_accordingly2(self):
        structure = StructureBase("structure")
        structure._init_item(1, DataTypeDefinition(DataType.LIST_PRIMARY_ID, template_argument=DataType.INT32), (4, 5, 3), False)

        item_value = structure._get_item(1)
        self.assertEqual(tuple, type(item_value))
        self.assertEqual((4, 5, 3), item_value)

    def test__init_item__inconsistent_non_optional_parameter__throws_exception(self):
        structure = StructureBase("structure")

        with self.assertRaises(InvalidOperationException):
            structure._init_item(1, DataType.INT32, None, False)

    def test__init_item__inconsistent_parameter_type1__throws_exception(self):
        structure = StructureBase("structure")

        with self.assertRaises(InvalidOperationException):
            structure._init_item(1, DataType.INT32, "ABC", False)

    def test__init_item__inconsistent_parameter_type2__throws_exception(self):
        structure = StructureBase("structure")

        with self.assertRaises(InvalidOperationException):
            structure._init_item(1, DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="TestStructure"), "ABC", False)
