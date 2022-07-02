import unittest
from api import CharField, ListField, DictField, EmailField, PhoneField, DateField, BirthDayField, GenderField, \
    ClientIDsField, ArgumentsField, ValidationError
from constants import UNKNOWN, MALE, FEMALE


def cases(cases_list):
    def deco(func):
        def wrapper(self):
            for case in cases_list:
                func(self, case)

        return wrapper
    return deco


class TestCharField(unittest.TestCase):
    @cases([5, dict(), list(), True])
    def test_CharField_validate_incorrect_value(self, value):
        with self.assertRaises(ValidationError):
            CharField.validate(CharField(), value)

    def test_CharField_validate_correct_value(self):
        self.assertTrue((CharField.validate(CharField(), '5') is None))


class TestListField(unittest.TestCase):
    @cases([5, dict(), 'ab', True])
    def test_ListField_validate_incorrect_value(self, value):
        with self.assertRaises(ValidationError):
            ListField.validate(ListField(), value)

    def test_ListField_validate_correct_value(self):
        self.assertTrue(ListField.validate(ListField(), [1, 2, 3]) is None)


class TestDictField(unittest.TestCase):
    @cases([5, list(), 'ab', True])
    def test_DictField_validate_incorrect_value(self, value):
        with self.assertRaises(ValidationError):
            DictField.validate(DictField(), value)

    def test_DictField_validate_correct_value(self):
        self.assertTrue(DictField.validate(DictField(), {'name': 'Alexy', 'surname': 'Vassili'}) is None)


class TestEmailField(unittest.TestCase):
    @cases([5, list(), 'ab', True, 'ab.com', 'ab at ab.com'])
    def test_EmailField_validate_incorrect_value(self, value):
        with self.assertRaises(ValidationError):
            EmailField.validate(EmailField(), value)

    def test_EmailField_validate_correct_value(self):
        self.assertTrue(EmailField.validate(EmailField(), 'petros@gmail.com') is None)


class TestPhoneField(unittest.TestCase):
    @cases([5, list(), 'ab', True, 89632223344, 7963222334, 789632223344,
            '89632223344', '7963222334', '789632223344'])
    def test_PhoneField_validate_incorrect_value(self, value):
        with self.assertRaises(ValidationError):
            PhoneField.validate(PhoneField(), value)

    def test_PhoneField_validate_correct_value(self):
        self.assertTrue(PhoneField.validate(PhoneField(), '79637222999') is None)
        self.assertTrue(PhoneField.validate(PhoneField(), 79637222999) is None)


class TestDateField(unittest.TestCase):
    @cases(['08.05..2003', '08.052003', '08/05/2003', '08:05:2003', '08052003'])
    def test_DateField_validate_incorrect_value(self, value):
        with self.assertRaises(ValidationError):
            DateField.validate(DateField(), value)

    def test_DateField_validate_correct_value(self):
        self.assertTrue(DateField.validate(DateField(), '08.05.2003') is None)
        self.assertTrue(DateField.validate(DateField(), '08.05.1920') is None)


class TestBirthDayField(unittest.TestCase):
    def test_BirthDayField_validate_incorrect_value(self):
        with self.assertRaises(ValidationError):
            # > 70 years
            BirthDayField.validate(BirthDayField(), '09.05.1945')

    def test_BirthDayField_validate_correct_value(self):
        self.assertTrue(BirthDayField.validate(BirthDayField(), '09.05.1997') is None)


class TestGenderField(unittest.TestCase):
    def test_GenderField_validate_incorrect_value(self):
        with self.assertRaises(ValidationError):
            GenderField.validate(GenderField(), -1)
        with self.assertRaises(ValidationError):
            GenderField.validate(GenderField(), 100)

    def test_GenderField_validate_correct_value(self):
        self.assertTrue(GenderField.validate(GenderField(), UNKNOWN) is None)
        self.assertTrue(GenderField.validate(GenderField(), MALE) is None)
        self.assertTrue(GenderField.validate(GenderField(), FEMALE) is None)


class TestClientIDsField(unittest.TestCase):
    def test_ClientIDsField_validate_incorrect_value(self):
        with self.assertRaises(ValidationError):
            # not a List
            ClientIDsField.validate(ClientIDsField(), (1, 2, 3, 4, 5))
        with self.assertRaises(ValidationError):
            # not int
            ClientIDsField.validate(ClientIDsField(), (1, 2, 3, 4, '5'))

    def test_ClientIDsField_validate_correct_value(self):
        self.assertTrue(ClientIDsField.validate(ClientIDsField(), [1, 2, 3, 4, 5]) is None)


class TestArgumentsField(unittest.TestCase):
    def test_ArgumentsField_validate_incorrect_value(self):
        with self.assertRaises(ValidationError):
            # non-dict type
            ArgumentsField.validate(ArgumentsField(), [1, 2, 3, 4, 5])

    def test_ArgumentsField_validate_correct_value(self):
        self.assertTrue(ArgumentsField.validate(ArgumentsField(), {"phone": "79175002040",
                                                     "email": "stuv@otus.ru",
                                                     "first_name": "Сергей",
                                                     "last_name": "Костюков",
                                                     "birthday": "01.01.1990",
                                                     "gender": 1}
                                              ) is None)


if __name__ == "__main__":
    unittest.main()