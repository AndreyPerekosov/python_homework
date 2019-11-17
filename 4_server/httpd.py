from socket import *
import threading
from urllib.parse import unquote
from urllib.parse import urlparse
import os
from datetime import datetime as dt
import argparse
from collections import namedtuple
import logging
import time

Response = namedtuple("Response", "data type length")

config = {
    "DOCUMENT_ROOT": os.getcwd(),
    "WORKERS": 10,
}


FILE_EXT = ["html", "css", "js", "txt"]

MEDIA_EXT = ["jpg", "jpeg", "png", "gif", "swf"]

CONTENT_TYPE = {"html": "text/html", "css": "text/css",
                "js": "text/javascript", "txt": "text/txt",
                "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "gif": "image/gif",
                "swf": "application/x-shockwave-flash"}


ALLOWED_METHODS = ["GET", "HEAD"]

OK = 200
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405

ERRORS = {
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    METHOD_NOT_ALLOWED: "Method Not Allowed",
    OK: "OK"
}

#If port equals 80, it requiers admins permissions
#So the program runs like: sudo python3 name_of_program.py
#And url views like: localhost/something/something.html
HOST = "localhost", 80


def make_response(connect, responce, content_type=None,
                  content_length=None, content=None, verb="GET",
                  server=None, error=True, config=None):
    """
    The function makes responce and closes connection
    """
    connect.sendall((f"HTTP/1.1 {responce[0]} {responce[1]}\r\n").encode('utf-8'))
    connect.sendall((f"Date: {dt.now().strftime('%c')}\r\n").encode('utf-8'))
    connect.sendall((f"Server: {server[0]} {server[1]}\r\n").encode('utf-8'))
    connect.sendall((f"Connection: close\r\n").encode('utf-8'))
    if error:
        connect.sendall(("\r\n").encode('utf-8'))
    else:
        connect.sendall((f"Content-Length: {content_length}\r\n").encode('utf-8'))
        connect.sendall((f"Content-Type: {CONTENT_TYPE[content_type]}\r\n\r\n").encode('utf-8'))
        if verb == "GET":
            connect.sendall(content)
    connect.close()
    if config:
        config["WORKERS"] += 1


def file_reader(root, path):
    """
    The function constructs path and reads file follow this path
    The function returns a namedtuple with
    read data, type of data, length of data
    """
    parse_result = urlparse(path)
    path_list = parse_result.path.split("/")
    if path[-1] == "/":
        path =  unquote(os.path.join(os.path.join(root, *path_list), "index.html"))
        type_ = "html"
    else:
        path = unquote(os.path.join(root, *path_list))
        type_ = path.split(".")[-1].lower()
    if type_ in MEDIA_EXT:
        with open(path, 'rb') as file:
            data = file.read()
    else:
        with open(path) as file:
            data = file.read().encode('utf-8')
    length = len(data)
    return Response(data, type_, length)


def handle_client_connection(client_socket, config):
    """
    The function handle the client connection.
    Incoming parametrs the client socket and dict of config
    """
    request = client_socket.recv(1024).decode('utf-8').strip().split("\r\n")

    # find verb and path
    url = request[0].split(" ")
    verb = url[0]
    if len(url) > 1:
        path = url[1]
    else:
        path = None

    if verb not in ALLOWED_METHODS:
        make_response(client_socket, (str(METHOD_NOT_ALLOWED), ERRORS[METHOD_NOT_ALLOWED]), server = HOST, config = config)
        return
    try:
        data = file_reader(config["DOCUMENT_ROOT"], path)
    except Exception:
        logging.exception("Got exception")
        make_response(client_socket, (str(NOT_FOUND), ERRORS[NOT_FOUND]), server = HOST, config = config)
        return
    if data.type not in FILE_EXT and data.type not in MEDIA_EXT:
        make_response(client_socket, (str(FORBIDDEN), ERRORS[FORBIDDEN]), server = HOST, config = config)
        return
    make_response(client_socket, (str(OK), ERRORS[OK]), content_type=data.type, 
                                  content_length=data.length, content = data.data, 
                                  server=HOST, error=False, config=config, verb=verb)


def main(config):
    logging.basicConfig(format='[%(asctime)s] %(levelname)s %(message)s',
                            level=logging.DEBUG,
                            datefmt=time.strftime('%Y.%m.%d %H:%M:%S'))
    # set command line params
    active_config = dict(config)

    parser = argparse.ArgumentParser(description="Analyzer log file")
    parser.add_argument('-r',
                        type=str,
                        default=active_config["DOCUMENT_ROOT"],
                        help='Sets root of working directory')
    parser.add_argument('-w',
                        type=int,
                        default=active_config["WORKERS"],
                        help='Sets number of workers')
    #set config from console
    args = parser.parse_args()
    active_config["DOCUMENT_ROOT"] = args.r
    active_config["WORKERS"] = args.w


    #starting the server
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((HOST[0], HOST[1]))
    s.listen(5)
    print("Starting the server")
    while True:
        client_socket, adress = s.accept()
        if config["WORKERS"] == 0:
            logging.info("Server is busy. Please try again.")
            make_response(client_socket, (str(FORBIDDEN), ERRORS[FORBIDDEN]), server = HOST)
            continue
        config["WORKERS"] -= 1  
        print("Recieved connection from", adress)
        client_handler = threading.Thread(
        target=handle_client_connection,
        args=(client_socket, active_config)
        )
        client_handler.start()
if __name__ == "__main__":
    main(config)
