# -*- coding: utf-8 -*-
import json
import uuid
from _datetime import datetime
import hashlib
import functools
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
from optparse import OptionParser

from constants import UNKNOWN, MALE, FEMALE, ADMIN_LOGIN, ADMIN_SALT, SALT
from scoring import get_interests, get_score


class ValidationError(Exception):
    def __init__(self, msg):
        self.msg = str(msg)

    def __str__(self):
        return self.msg


class Field:
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable
        self.value = None

    def __get__(self, obj, objtype=None):
        logging.debug(f'get value {self.value}')
        return self.value

    def __set__(self, obj, value):
        if value is None and (self.required or not self.nullable):
            raise AttributeError('Value is required', value)
        elif not value and not self.nullable:
            raise AttributeError('Value is required', value)
        elif value is None and not self.required:
            self.value = None
        else:
            self.validate(value)
            self.value = value

    def validate(self, value):
        raise NotImplementedError


class CharField(Field):

    def validate(self, value):
        logging.debug('validating chars')
        if not isinstance(value, str):
            raise ValidationError('Char Field got non-string type')


class ListField(Field):

    def validate(self, value):
        logging.debug('validating list')
        if not isinstance(value, list):
            raise ValidationError('List Field got non-list type')


class DictField(Field):

    def validate(self, value):
        logging.debug('validating list')
        if not isinstance(value, dict):
            raise ValidationError('Dict Field got non-dict type')


class EmailField(CharField):

    def validate(self, value):
        logging.debug('validating mail')
        super().validate(value)
        if not ('@' in value):
            raise ValidationError("No '@' in Email Field")


class PhoneField(Field):

    def validate(self, value):
        logging.debug('validating phone')
        value = str(value)
        if not (len(value) == 11):
            raise ValidationError('Phone Field must contain 11 numbers')
        elif not value.isdigit():
            raise ValidationError('Phone Field must contain only digits')
        elif not value.startswith('7'):
            raise ValidationError("Phone Field must starts with '7'")


class DateField(CharField):

    def validate(self, value):
        logging.debug('validating date')
        super().validate(value)
        try:
            datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError as e:
            raise ValidationError(e)


class BirthDayField(DateField):

    def validate(self, value):
        logging.debug('validating bthday')
        super().validate(value)
        value = datetime.strptime(value, "%d.%m.%Y").date()
        today = datetime.now().date()
        if not (today - value).days // 365 < 70:
            raise ValidationError('Incorrect date: (> 70 years old)')


class GenderField(Field):

    def validate(self, value):
        logging.debug('validating gender')
        if value not in (UNKNOWN, MALE, FEMALE):
            raise ValidationError('Unexpected gender')


class ClientIDsField(ListField):

    def validate(self, value):
        logging.debug('validating client ids')
        super().validate(value)
        if not all(map(lambda x: type(x) is int, value)):
            raise ValidationError('Cliend IDs may contains only integers')


class ArgumentsField(DictField):

    def validate(self, value):
        super().validate(value)


class ApiRequest:
    def __init__(self, **kwargs):
        self.api_fields = [k for k, v in self.__class__.__dict__.items()
                           if isinstance(v, Field)]
        logging.debug(f'API FIELDS {self.api_fields}')
        self.kwargs = kwargs
        self.has = []

    def validate(self):
        bad_fields = []
        required_field_errs = []
        for field in self.api_fields:
            if field in self.kwargs:
                value = self.kwargs[field]
                self.has.append(field)
            else:
                value = None
            try:
                logging.debug(f'SET {field} TO {value}')
                setattr(self, field, value)
            except ValidationError as e:
                logging.debug(f'FAILED TO SET {field} TO {value}')
                bad_fields.append((field, e.args[0]))
            except AttributeError:
                required_field_errs.append(field)
        if required_field_errs:
            raise AttributeError(f'This fields is required: {required_field_errs}')
        if bad_fields:
            raise TypeError(f'Bad fields: {bad_fields}')
        logging.debug('CALL REQUEST VALIDATE')
        return True


class MethodRequest(ApiRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=True)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


class ClientsInterestsRequest(MethodRequest):
    client_ids = ClientIDsField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)

    def __init__(self, ctx, **kwargs):
        super(ClientsInterestsRequest, self).__init__(**kwargs)
        ctx.update({"nclients": len(kwargs.get('client_ids'))})


class OnlineScoreRequest(MethodRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        super().validate()
        if ('first_name' in self.has and 'last_name' in self.has) or \
                ('email' in self.has and 'phone' in self.has) or \
                ('birthday' in self.has and 'gender' in self.has):
            return True
        else:
            raise AttributeError("Required at least one of this fields pars: ('first_name', 'last_name'), "
                                 "('email', 'phone'), ('birthday', 'gender')")


def check_auth(request: MethodRequest):
    if request.login == ADMIN_LOGIN:
        digest = hashlib.sha512((datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode('utf-8')).hexdigest()
    logging.info(f'DIGEST: {digest}')
    if digest == request.token:
        return True
    return False


def login_required(method_handler: callable):
    @functools.wraps(method_handler)
    def wrapper(request: MethodRequest, ctx, store):
        if check_auth(request):
            res = method_handler(request, ctx, store)
        else:
            res = (HTTPStatus.FORBIDDEN, HTTPStatus.FORBIDDEN.phrase)
        return res
    return wrapper


def method_handler(request, ctx, store):
    methods = {
        'online_score': online_score_handler,
        'clients_interests': clients_interests_handler,
    }
    try:
        req_obj = MethodRequest(**request["body"])
        req_obj.validate()
        code, response = methods[req_obj.method](req_obj, ctx, store)
    except AttributeError as e:
        return e.args[0], HTTPStatus.UNPROCESSABLE_ENTITY
    except TypeError as e:
        return e.args[0], HTTPStatus.UNPROCESSABLE_ENTITY
    else:
        return response, code


@login_required
def online_score_handler(request: MethodRequest, ctx, store):
    api_request = OnlineScoreRequest(**request.arguments)
    api_request.validate()
    if api_request.is_admin:
        return HTTPStatus.OK, {"score": 42}
    logging.debug(f'HAS: {api_request.has}')
    ctx['has'] = api_request.has
    score = get_score(store,
                      phone=api_request.phone,
                      email=api_request.email,
                      birthday=api_request.birthday,
                      gender=api_request.gender,
                      first_name=api_request.first_name,
                      last_name=api_request.last_name)
    return HTTPStatus.OK, {"score": score}


@login_required
def clients_interests_handler(request: MethodRequest, ctx, store):
    api_request = ClientsInterestsRequest(ctx, **request.arguments)
    api_request.validate()
    logging.debug(f'HAS: {api_request.has}')
    ctx['has'] = api_request.has
    return HTTPStatus.OK, {cid: get_interests(store, cid) for cid in api_request.client_ids}


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, HTTPStatus.OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = HTTPStatus.BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = HTTPStatus.INTERNAL_SERVER_ERROR
            else:
                code = HTTPStatus.NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code == HTTPStatus.OK:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode('utf-8'))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
