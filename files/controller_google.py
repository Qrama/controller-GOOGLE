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
# pylint: disable=c0111,c0301,c0325, r0903,w0406,e0401
import os
from subprocess import check_output, check_call, Popen
from sojobo_api import settings
from sojobo_api.api import w_errors as errors, w_datastore as datastore, w_juju as juju
from flask import abort
import yaml
import json


CRED_KEYS = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email',
             'client_id', 'auth_uri', 'token_uri', 'auth_provider_x509_cert_url',
             'client_x509_cert_url']


class Token(object):
    def __init__(self, url):
        self.type = 'google'
        self.supportlxd = False
        self.url = url

def create_controller(name, data):
    Popen(["python3", "{}/scripts/bootstrap_google_controller.py".format(settings.SOJOBO_API_DIR),
           name, data['region'], data['credential']])
    return 202, 'Environment {} is being created in region {}'.format(name, data['region'])

def get_supported_series():
    return ['trusty', 'xenial', 'yakkety']

def get_supported_regions():
    return ['us-east1', 'us-central1', 'us-west1', 'europe-west1', 'asia-east1', 'asia-northeast1', 'asia-southeast1']


def check_valid_credentials(credentials):
    wrong_keys = []
    if len(CRED_KEYS) == len(list(credentials.keys())):
        for cred in CRED_KEYS:
            if not cred in list(credentials.keys()):
                wrong_keys.append(cred)
    if len(wrong_keys)>0:
        error = errors.key_does_not_exist(wrong_keys)
        abort(error[0], error[1])

def generate_cred_file(name, credentials):
    result = {
        'type': 'jsonfile',
        'name': name,
        'key': {'file': str(json.dumps(credentials))}
    }
    return result

def add_credential(user, data):
    Popen(["python3", "{}/scripts/add_google_credential.py".format(settings.SOJOBO_API_DIR),
           user, str(data), settings.SOJOBO_API_DIR])
    return 202, 'Credentials are being added for user {}'.format(user)
