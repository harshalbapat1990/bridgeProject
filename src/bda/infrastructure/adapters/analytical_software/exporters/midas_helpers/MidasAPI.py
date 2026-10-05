from enum import Enum
import requests

class ApiResponseStatus(Enum):
    SUCCESS = (200, "Success", "Your request arrived successfully on your MIDAS CIVIL NX model.")
    CREATED = (201, "Created", "Successfully delivered your request to your model.")
    BAD_REQUEST = (400, "Bad Request", "Input wrong command or body")
    FORBIDDEN = (403, "Forbidden", "Does not open API command for users")
    NOT_FOUND = (404, "Not found", "Client did not connect to API server.")

    def __init__(self, code, title, message):
        self.code = code
        self.title = title
        self.message = message

    @classmethod
    def from_code(cls, code):
        for status in cls:
            if status.code == code:
                return status
        return None


class MidasAPI:
    def __init__(self, baseURL, mapiKey, print_requests:bool = False):
        self.baseURL = baseURL
        self.mapiKey = mapiKey
        assert baseURL != "", 'Base URL cannot be empty.'
        assert mapiKey != "", 'MAPI-Key cannot be empty.'
        self.print_requests = print_requests

    # function for MIDAS Open API
    def request(self, method, command, json=None):
        url = self.baseURL + command
        headers = {
            "Content-Type": "application/json",
            "MAPI-Key": self.mapiKey
        }

        if command.startswith('/db'):
            prefix = 'Assign'
        elif command.startswith(('/doc', '/post', '/view', '/ope')):
            prefix = 'Argument'
        else:
            assert False, f'command must be one of: [/db, /doc, /post, /view, /ope]'

        body = {prefix: json}

        if method == "POST":
            response = requests.post(url=url, headers=headers, json=body)
        elif method == "PUT":
            response = requests.put(url=url, headers=headers, json=body)
        elif method == "GET":
            response = requests.get(url=url, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url=url, headers=headers)
        else:
            assert False, "Method must be POST, PUT, GET, DELETE"

        if self.print_requests:
            print(method, command, response.status_code)
        return response

    def test_connection(self):
        try:
            resp = self.request("GET", "/db/unit")
            return resp
        except:
            return None

    def is_connected(self):
        try:
            resp = self.request("GET", '/db/unit')
            return resp.status_code == 200
        except Exception as e:
            raise Exception(e)

    @classmethod
    def validate_response(cls, response):
        status = ApiResponseStatus.from_code(response.status_code)
        return f"{status.code}: {status.title} - {status.message}"