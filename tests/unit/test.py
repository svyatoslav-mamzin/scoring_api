from api import CharField, ListField, DictField, EmailField, PhoneField, DateField, BirthDayField, GenderField, \
    ClientIDsField, ArgumentsField, ValidationError
from constants import UNKNOWN, MALE, FEMALE
import hashlib
import datetime
import unittest
import constants
import api


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


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.settings = {}

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.settings)

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(
                (datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode('utf-8')).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api.SALT
            request["token"] = hashlib.sha512(msg.encode('utf-8')).hexdigest()

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(constants.INVALID_REQUEST, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_bad_auth(self, request):
        _, code = self.get_response(request)
        self.assertEqual(constants.FORBIDDEN, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    ])
    def test_invalid_method_request(self, request):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(constants.INVALID_REQUEST, code)
        self.assertTrue(len(response))

    @cases([
        {},
        {"phone": "79175002040"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79175002040", "email": "stupnikovotus.ru"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.1890"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "XXX"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": 1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "s", "last_name": 2},
        {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ])
    def test_invalid_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(constants.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(constants.OK, code, arguments)
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)
        self.assertEqual(sorted(self.context["has"]), sorted(arguments.keys()))

    def test_ok_score_admin_request(self):
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(constants.OK, code)
        score = response.get("score")
        self.assertEqual(score, 42)

    @cases([
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    ])
    def test_invalid_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(constants.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_ok_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(constants.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        # self.assertTrue(all(v and isinstance(v, list) and all(isinstance(i, basestring) for i in v)
        #                for v in response.values()))
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))


if __name__ == "__main__":
    unittest.main()