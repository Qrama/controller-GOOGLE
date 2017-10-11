# !/usr/bin/env python3.6
# Copyright (C) 2017  Qrama
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# pylint: disable=c0111,c0301,c0325, r0903,w0406
import os
from subprocess import check_output, check_call
from sojobo_api import settings
from sojobo_api.api import w_errors as errors
from flask import abort
import yaml
import json
from juju.client.connection import JujuData


CRED_KEYS = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email',
             'client_id', 'auth_uri', 'token_uri', 'auth_provider_x509_cert_url',
             'client_x509_cert_url']


class Token(object):
    def __init__(self, url, username, password):
        self.type = 'google'
        self.supportlxd = False
        self.url = url


def create_controller(name, region, credentials, cred_name):
    check_call(['juju', 'add-credential', 'google', '-f', create_credentials_file(cred_name, credentials), '--replace'])
    output = check_output(['juju', 'bootstrap', '--agent-version=2.2.2', 'google/{}'.format(region), name, '--credential', cred_name])
    return output


def get_supported_series():
    return ['precise', 'trusty', 'xenial', 'yakkety']

def get_supported_regions():
    return ['us-east1', 'us-central1', 'us-west1', 'europe-west1', 'asia-east1', 'asia-northeast1', 'asia-southeast1']

def create_credentials_file(name, credentials):
    if len(CRED_KEYS) == len(list(credentials.keys())):
        for cred in CRED_KEYS:
            if not cred in list(credentials.keys()):
                error = errors.key_does_not_exist(cred)
                abort(error[0], error[1])
    cred_path = '/home/{}/credentials'.format(settings.SOJOBO_USER)
    if not os.path.exists(cred_path):
        os.mkdir(cred_path)
    filepath = '{}/google-{}.json'.format(cred_path, name)
    with open(filepath, 'w+') as credfile:
        json.dump(credentials, credfile)
    path = '/tmp/credentials.yaml'
    data = {'credentials': {'google': {name: {'auth-type': 'jsonfile',
                                              'file': filepath}}}}
    with open(path, 'w') as dest:
        yaml.dump(data, dest, default_flow_style=True)
    return path


def generate_cred_file(name, credentials):
    if len(CRED_KEYS) == len(list(credentials.keys())):
        for cred in CRED_KEYS:
            if not cred in list(credentials.keys()):
                error = errors.key_does_not_exist(cred)
                abort(error[0], error[1])
    result = {
        'type': 'jsonfile',
        'name': name,
        'key': {'file': str(json.dumps(credentials))}
    }
    return result
