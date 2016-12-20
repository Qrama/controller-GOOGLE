# !/usr/bin/env python3
# Copyright (C) 2016  Qrama
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

from subprocess import check_output, check_call
import yaml


class Token(object):
    def __init__(self, url, username, password):
        self.project_id = None
        self.auth_file = None
        self.type = 'gce'
        self.supportlxd = True
        self.url = url

    def get_credentials(self):
        return {'auth-type': 'access-key', 'project-id': self.project_id, 'auth-file': self.auth_file}

    def get_cloud(self):
        return {'type': 'gce', 'auth-types': ['access-key'], 'endpoint': self.url}


def get_credentials(auth):
    with open('/home/ubuntu/.local/share/juju/credentials.yaml', 'r') as cred:
        credentials = yaml.load(cred)['credentials']['gce'][auth.username]
    return credentials['access-key'], credentials['secret-key']


def create_controller(name, region, credentials, cfile):
    path = create_credentials_file(region, credentials)
    check_call(['juju', 'add-credential', 'gce', '-f', path])
    output = check_output(['juju', 'bootstrap', 'gce/{}'.format(region), name])
    return output


def get_supported_series():
    return ['precise', 'trusty', 'xenial', 'yakkety']


def create_credentials_file(region, credentials):
    path = '/tmp/credentials.yaml'
    data = {'gce': {'default-credential': 'admin',
                    'default-region': region,
                    'admin': {'auth-type': 'access-key',
                              'access-key': credentials['access_key'],
                              'secret-key': credentials['secret_key']}}}
    with open(path, 'w') as dest:
        yaml.dump(data, dest, default_flow_style=True)
    return path
