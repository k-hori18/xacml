import mysql.connector
from datetime import datetime
from neo4jrestclient.client import GraphDatabase
from pathlib import Path
import configparser
import requests

_GLOBAL_PATH = str(Path(__file__).resolve().parent)


class PEPConfig:
    # Class to manage PEP Config

    _CONFIG_PATH = _GLOBAL_PATH + '/config.ini'

    def __init__(self):
        # constructor
        # load config file
        self._ini_file = configparser.ConfigParser()
        self._ini_file.read(PEPConfig._CONFIG_PATH)

    def get_pdp_host(self):
        return self._ini_file.get('pdp', 'host')

    def get_pdp_port(self):
        return self._ini_file.get('pdp', 'port')

    def get_pdp_domain(self):
        return self._ini_file.get('pdp', 'domain')

def _get_server_address(student_id):
    #neo4jから生徒情報サーバのIPアドレスを取得する
    url = "http://133.16.239.120:7474/db/data/"
    gdb = GraphDatabase(url)

    query = "MATCH(n:Student{{id:'{}'}}) RETURN n.server;"
    result = gdb.query(query.format(student_id),data_contents=True)
    result = result[0][0]

    return result


def _confirm_server_alive(student_id):
    server = _get_server_address(student_id)
    user = 'davtest'
    password = 'test'
    url = 'http://{}/webdav/davtest/test.txt'
    
    try:
        req = requests.get(url.format(server), auth=(user,password))
        with open(_GLOBAL_PATH + '/test.txt', mode='w') as f:
            f.write(req.text)
        return req.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def _download_file(student_id, file_id):
    server = _get_server_address(student_id)
    user = 'davtest'
    password = 'test'
    url = 'http://{}/webdav/davtest/' + file_id

    try:
        req = requests.get(url.format(server), auth=(user,password))
        with open(_GLOBAL_PATH + '/' + file_id, mode='w') as f:
            f.write(req.text)
        return _GLOBAL_PATH + '/' + file_id
    except requests.exceptions.ConnectionError:
        return False
    return 0