

import unittest
from weasyl.configuration_builder import (
    BoolOption, ConfigOption, DuplicateCode, InvalidValue, create_configuration)


class ConfigOptionTests(unittest.TestCase):
    def test_simple_option(self):
        val_a = 1234
        val_b = "hello"
        val_c = None
        op = ConfigOption("op", {val_a: "a", val_b: "b", val_c: "c"})

        self.assertEqual(val_a, op.get_value("a"))
        self.assertEqual(val_b, op.get_value("b"))
        self.assertEqual(val_c, op.get_value("c"))
        self.assertEqual(None, op.get_value("q"))

        self.assertEqual("a", op.get_code(val_a))
        self.assertEqual("b", op.get_code(val_b))
        self.assertEqual("c", op.get_code(val_c))
        self.assertEqual("", op.get_code("something else"))


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.Config = create_configuration([
            BoolOption("walrus", "w"),
            BoolOption("penguin", "p"),
            BoolOption("badger", "b"),
            ConfigOption("shape", {"square": "s", "triangle": "t", "circle": "c"}),
        ])

    def test_parse(self):
        c = self.Config.from_code("wbs")
        self.assertTrue(c.walrus)
        self.assertFalse(c.penguin)
        self.assertTrue(c.badger)
        self.assertEqual("square", c.shape)

    def test_parse_unrecognized_codes(self):
        c = self.Config.from_code("qwbs123")
        self.assertTrue(c.walrus)
        self.assertFalse(c.penguin)
        self.assertTrue(c.badger)
        self.assertEqual("square", c.shape)

    def test_unparse(self):
        c = self.Config()
        c.penguin = True
        c.badger = True
        c.shape = "triangle"
        # note: codes sorted alphabetically
        self.assertEqual("bpt", c.to_code())

    def test_invalid_values(self):
        c = self.Config()
        self.assertRaises(InvalidValue, setattr, c, 'penguin', 'A')
        self.assertRaises(InvalidValue, setattr, c, 'shape', 'purple')


class CreateConfigurationTests(unittest.TestCase):
    def test_all_option_codes(self):
        Config = create_configuration([
            BoolOption("walrus", "w"),
            BoolOption("penguin", "p"),
            BoolOption("badger", "b"),
            ConfigOption("shape", {"square": "s", "triangle": "t", "circle": "c"}),
        ])
        self.assertEqual(sorted("stcbwp"), sorted(Config.all_option_codes))

    def test_duplicate_codes(self):
        def create_config_with_duplicate():
            return create_configuration([
                BoolOption("bagel", "b"),
                ConfigOption("number", {10: "a", 12: "b", 13: "c"}),
            ])
        self.assertRaises(DuplicateCode, create_config_with_duplicate)
