"""Api for homework_4"""
import datetime
import hashlib
import json
import logging
import uuid
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, HTTPServer

from scoring import get_interests, get_score

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


class ValidationError(Exception):
    """Class for validation errors"""


class Field:
    """Class for field validation"""

    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        """Validate field"""
        if value is None:
            if self.required:
                raise ValidationError("Field is required")
            return None
        if value == "" and not self.nullable:
            raise ValidationError("Field is not nullable")
        return self.parse(value)

    def parse(self, value):
        """Parse field"""
        return value


class CharField(Field):
    """Class for string field validation"""
    def parse(self, value):
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")
        return value


class EmailField(CharField):
    """Class for email field validation"""
    def parse(self, value):
        value = super().parse(value)
        if "@" not in value:
            raise ValidationError("Invalid email")
        return value


class PhoneField(Field):
    """Class for phone field validation"""
    def parse(self, value):
        if isinstance(value, str):
            if not value.isdigit():
                raise ValidationError("Phone must be digits")
        elif isinstance(value, int):
            value = str(value)
        else:
            raise ValidationError("Invalid phone type")
        if not (len(value) == 11 and value.startswith("7")):
            raise ValidationError("Phone must be 11 digits and start with 7")
        return value


class DateField(Field):
    """Class for date field validation"""
    def parse(self, value):
        try:
            return datetime.datetime.strptime(value, "%d.%m.%Y")
        except Exception as e:
            raise ValidationError("Invalid date format, should be DD.MM.YYYY") from e


class BirthDayField(DateField):
    """Class for birthday field validation"""
    def parse(self, value):
        date = super().parse(value)
        today = datetime.datetime.today()
        age = (today - date).days / 365.25
        if age > 70:
            raise ValidationError("Age must be less than or equal to 70")
        return date


class GenderField(Field):
    """Class for gender field validation"""
    def parse(self, value):
        if not isinstance(value, int):
            raise ValidationError("Gender must be int")
        if value not in [0, 1, 2]:
            raise ValidationError("Gender must be 0, 1 or 2")
        return value


class ClientIDsField(Field):
    """Class for client IDs field validation"""
    def parse(self, value):
        if not isinstance(value, list):
            raise ValidationError("ClientIDs must be a list")
        if not value:
            raise ValidationError("ClientIDs list is empty")
        for item in value:
            if not isinstance(item, int):
                raise ValidationError("All client IDs must be integers")
        return value


class ArgumentsField(Field):
    """Class for arguments field validation"""
    def parse(self, value):
        if not isinstance(value, dict):
            raise ValidationError("Arguments must be a dict")
        return value


class DeclarativeMeta(type):
    """Metaclass for validating fields"""
    def __new__(mcs, name, bases, namespace):
        fields = {key: val for key, val in namespace.items() if isinstance(val, Field)}
        for key in fields:
            namespace.pop(key)
        namespace['__fields__'] = fields
        return type.__new__(mcs, name, bases, namespace)


class Request(metaclass=DeclarativeMeta):
    """Base class for requests"""
    __fields__: dict  # for static analysis tools

    def __init__(self, data):
        self.errors = {}
        self.cleaned_data = {}
        for name, field in self.__fields__.items():
            raw_value = data.get(name)
            try:
                parsed_value = field.validate(raw_value)
                self.cleaned_data[name] = parsed_value
                setattr(self, name, parsed_value)
            except ValidationError as e:
                self.errors[name] = str(e)

    def is_valid(self):
        """Check if the request is valid"""
        return not self.errors


class OnlineScoreRequest(Request):
    """Request for online score"""
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate_pairs(self):
        """Check if the request contains at least one valid pair of fields"""
        valid_pairs = [
            self.phone and self.email,
            self.first_name and self.last_name,
            self.gender is not None and self.birthday is not None
        ]
        if not any(valid_pairs):
            raise ValidationError("At least one valid pair must be present")


class ClientsInterestsRequest(Request):
    """Request for clients interests"""
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class MethodRequest(Request):
    """Request for method"""
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        """Check if the user is an admin"""
        return self.login == ADMIN_LOGIN


def check_auth(request):
    """Check authentication"""
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode('utf-8')).hexdigest()
    return digest == request.token


def method_handler(request, ctx, store):
    """Handle method request"""
    try:
        req = MethodRequest(request['body'])
    except Exception as e:
        return str(e), INVALID_REQUEST

    if not req.is_valid():
        return req.errors, INVALID_REQUEST

    if not check_auth(req):
        return ERRORS[FORBIDDEN], FORBIDDEN

    arguments = req.arguments
    if req.method == "online_score":
        score_req = OnlineScoreRequest(arguments)
        if not score_req.is_valid():
            return score_req.errors, INVALID_REQUEST
        try:
            score_req.validate_pairs()
        except ValidationError as e:
            return str(e), INVALID_REQUEST
        ctx['has'] = [k for k, v in score_req.cleaned_data.items() if v is not None]
        if req.is_admin:
            return {"score": 42}, OK
        return {"score": get_score(store, **score_req.cleaned_data)}, OK

    elif req.method == "clients_interests":
        ci_req = ClientsInterestsRequest(arguments)
        if not ci_req.is_valid():
            return ci_req.errors, INVALID_REQUEST
        ctx['nclients'] = len(ci_req.cleaned_data['client_ids'])
        return {cid: get_interests(store, cid) for cid in ci_req.cleaned_data['client_ids']}, OK
    else:
        return ERRORS[INVALID_REQUEST], INVALID_REQUEST


class MainHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for the server."""
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        """Get the request id from the header."""
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        """Handle the HTTP POST requests."""
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except Exception:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info(f"{self.path}: {data_string} {context["request_id"]}")
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception(f"Unexpected error: {e}")
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
        self.wfile.write(json.dumps(r).encode('utf-8'))
        return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    args = parser.parse_args()
    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info(f"Starting server at {args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
