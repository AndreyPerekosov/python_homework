#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
import scoring

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class BaseRequest():

    @classmethod
    def property_set(cls, prop):
        prop_list = []
        for attr in cls.__dict__.keys():
            if hasattr(cls.__dict__[attr], prop):
                if cls.__dict__[attr].__dict__[prop]:
                    prop_list.append(attr)
        return set(prop_list)

    def validate(self, data_dict):
        invalid_fields = []
        for data_attr in data_dict.keys():
            if hasattr(self, data_attr):
                try:
                    setattr(self, data_attr, data_dict[data_attr])
                except Exception as e:
                    invalid_fields.append((data_attr, e))
        return invalid_fields

    def get_context(self, context):
        raise NotImplementedError


class BaseField():
    """
    Define base logic of parametrs field
    """

    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable


class TypedProperty(BaseField):
    """
    Define base logic that working with content of fields
    """

    def __init__(self, type, default=None, **kwargs):
        self.type = type
        self.default = default
        super().__init__(**kwargs)

    def __set_name__(self, cls, name):
        self.name = '_' + name

    def __get__(self, instance, cls):
        return getattr(instance, self.name, self.default)

    def __set__(self, instance, value):
        if (self.nullable and not value) or (isinstance(value, self.type) and value):
            setattr(instance, self.name, value)
        else:
            if not self.nullable and not value:
                raise ValueError("Blank value are not required")
            else:
                raise TypeError("Must be a %s" % self.type)


class _MetaField(type):
    """
    Define metaclass that provides include into inherit base
    class TypedProperty
    """
    def __new__(cls, name, bases, attrs):
        if TypedProperty not in bases:
            bases = list(bases)
            bases.append(TypedProperty)
            bases = tuple(bases)
        return type.__new__(cls, name, bases, attrs)


class CharField(metaclass=_MetaField):
    def __init__(self, **kwargs):
        super().__init__(type=str, **kwargs)


class ArgumentsField(metaclass=_MetaField):
    def __init__(self, **kwargs):
        super().__init__(type=dict, **kwargs)


class EmailField(CharField):
    def __set__(self, instance, value):
        if '@' in value or not value:
            super().__set__(instance, value)
        else:
            raise TypeError("Must be correct email")


class PhoneField(metaclass=_MetaField):

    def __init__(self, **kwargs):
        super().__init__(type=str, **kwargs)

    def __set__(self, instance, value):
        if not value:
            super().__set__(instance, value)
        if isinstance(value, (str, int)):
            value = str(value)
            if len(value) == 11 and value[0] == '7':
                super().__set__(instance, value)
            else:
                raise ValueError("Must be telefone number like 7*******")
        else:
            raise TypeError("Must be string or int number")


class DateField(metaclass=_MetaField):
    def __init__(self, **kwargs):
        super().__init__(type=str, **kwargs)

    def __set__(self, instance, value):
        if not value or datetime.datetime.strptime(value, '%d.%m.%Y'):
            super().__set__(instance, value)


class BirthDayField(metaclass=_MetaField):

    def __init__(self, **kwargs):
        super().__init__(type=str, **kwargs)

    def __set__(self, instance, value):
        if not value or ((datetime.datetime.now() - datetime.datetime.strptime(value, '%d.%m.%Y')).days / 365 <= 70):
            super().__set__(instance, value)
        else:
            raise ValueError("Sorry! A person should be younger than 71 years old")


class GenderField(metaclass=_MetaField):
    def __init__(self, **kwargs):
        super().__init__(type=int, **kwargs)

    def __set__(self, instance, value):
        if not value or value in [UNKNOWN, MALE, FEMALE]:
            super().__set__(instance, value)
        else:
            raise ValueError("Value must be integer 0, 1, 2")


class ClientIDsField(metaclass=_MetaField):
    def __init__(self, **kwargs):
        super().__init__(type=list, **kwargs)
    def __set__(self, instance, value):
        if len(list(filter(lambda item: isinstance(item, int), value))) == len(value) or not value:
            super().__set__(instance, value)
        else:
            raise ValueError("Items of list must be integer type")


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def get_context(self, args):
        return len(self.client_ids)


class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self, data_dict):
        errors = super().validate(data_dict)
        if not errors:
            if (self.first_name and self.last_name) \
            or (self.email and self.phone) \
            or (self.birthday and (self.gender or self.gender == 0)):
                return errors
            else:
                errors.append('Pair fields are blank or null. See readme for detail')
        return errors

    def get_context(self, args):
        return list(filter(lambda item: args[item] or args[item] == 0, args))


class MethodRequest(BaseRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        encoded = (datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')
        digest = hashlib.sha512(encoded).hexdigest()
    else:
        encoded = (request.account + request.login + SALT).encode('utf-8')
        digest = hashlib.sha512(encoded).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    response, code = None, None
    req = MethodRequest()
    if not req.property_set('required').issubset(set(request['body'].keys())):
        return ERRORS[INVALID_REQUEST], INVALID_REQUEST
    errors = req.validate(request['body'])
    if errors:
        return ERRORS[BAD_REQUEST], BAD_REQUEST
    if not check_auth(req):
        return ERRORS[FORBIDDEN], FORBIDDEN
    method_inst = OnlineScoreRequest() if req.method == 'online_score' else ClientsInterestsRequest()
    if not method_inst.property_set('required').issubset(req.arguments.keys()):
        return f"required fields:{method_inst.property_set('required').difference(req.arguments.keys())}", INVALID_REQUEST
    errors = method_inst.validate(req.arguments)
    if errors:
        return errors, INVALID_REQUEST
    if isinstance(method_inst, OnlineScoreRequest):
        ctx['has'] = method_inst.get_context(req.arguments)
        if req.is_admin:
            return {"score": 42}, OK
        else:
            return {"score": scoring.get_score(store, method_inst.phone,
                    method_inst.email, method_inst.birthday,
                    method_inst.gender, method_inst.first_name,
                    method_inst.last_name)}, OK
    else:
        ctx['nclients'] = method_inst.get_context(req.arguments)
        return {str(item): scoring.get_interests(store, item) for item in method_inst.client_ids}, OK


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
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
