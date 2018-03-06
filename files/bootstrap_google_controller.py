# !/usr/bin/env python3
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
# pylint: disable=c0111,c0301,c0325,c0103,r0913,r0902,e0401,C0302, R0914
import asyncio
import logging
import os
import hashlib
from pathlib import Path
from subprocess import check_output, check_call
import traceback
import sys
import yaml
import json
from juju import tag
from juju.controller import Controller
from juju.client import client
sys.path.append('/opt')
from sojobo_api import settings  #pylint: disable=C0413
from sojobo_api.api import w_datastore as datastore, w_juju as juju  #pylint: disable=C0413

async def bootstrap_google_controller(c_name, region, cred_name):#pylint: disable=E0001
    try:
        # Check if the credential is valid.
        username = settings.JUJU_ADMIN_USER
        password = settings.JUJU_ADMIN_PASSWORD
        valid_cred_name = 't{}'.format(hashlib.md5(cred_name.encode('utf')).hexdigest())
        credential = juju.get_credential(username, cred_name)

        juju.get_controller_types()['google'].check_valid_credentials(credential)

        # Create credential file that can be used to bootstrap controller.
        cred_path = '/home/{}/credentials'.format(settings.SOJOBO_USER)
        if not os.path.exists(cred_path):
            os.mkdir(cred_path)
        filepath = '{}/google-{}.json'.format(cred_path, valid_cred_name)
        with open(filepath, 'w+') as credfile:
            json.dump(credential['credential'], credfile)
        path = '/tmp/credentials.yaml'
        data = {'credentials':
                    {'google':
                        {valid_cred_name:
                            {'auth-type': 'jsonfile',
                             'file': filepath}}}}
        with open(path, 'w') as dest:
            yaml.dump(data, dest, default_flow_style=True)

        logger.info('Adding the credential...')
        check_call(['juju', 'add-credential', 'google', '-f', path, '--replace'])

        logger.info('Bootstrapping controller...')
        check_call(['juju', 'bootstrap', '--agent-version=2.3.0', 'google/{}'.format(region), c_name, '--credential', valid_cred_name])
        os.remove(path)

        logger.info('Setting admin password...')
        check_output(['juju', 'change-user-password', 'admin', '-c', c_name],
                     input=bytes('{}\n{}\n'.format(password, password), 'utf-8'))

        con_data = {}
        logger.info('Updating controller in database...')
        with open(os.path.join(str(Path.home()), '.local', 'share', 'juju', 'controllers.yaml'), 'r') as data:
            con_data = yaml.load(data)
        datastore.set_controller_state(
            c_name,
            'ready',
            endpoints=con_data['controllers'][c_name]['api-endpoints'],
            uuid=con_data['controllers'][c_name]['uuid'],
            ca_cert=con_data['controllers'][c_name]['ca-cert'])

        logger.info('Connecting to controller...')
        controller = Controller()

        logger.info('Adding existing credentials and default models to database...')
        credentials = datastore.get_credentials(username)
        await controller.connect(endpoint=con_data['controllers'][c_name]['api-endpoints'][0],
                                 username=username, password=password, cacert=con_data['controllers'][c_name]['ca-cert'])
        for cred in credentials:
            if cred['name'] != cred_name:
                await juju.update_cloud(controller, 'google', cred['name'], username)

        controller_facade = client.ControllerFacade.from_connection(controller.connection())
        models = await controller_facade.AllModels()
        for model in models.user_models:
            if model:
                logger.info(model.model.name)
                m_key = juju.construct_model_key(c_name, model.model.name)
                datastore.create_model(m_key, model.model.name, state='Model is being deployed', uuid='')
                datastore.add_model_to_controller(c_name, m_key)
                datastore.set_model_state(m_key, 'ready', credential=cred_name, uuid=model.model.uuid)
                datastore.set_model_access(m_key, username, 'admin')
        logger.info('Controller succesfully created!')
    except Exception:  #pylint: disable=W0703
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for l in lines:
            logger.error(l)
        datastore.set_controller_state(c_name, 'error')
    finally:
        await juju.disconnect(controller)


if __name__ == '__main__':
    logger = logging.getLogger('bootstrap_google_controller')
    hdlr = logging.FileHandler('{}/log/bootstrap_google_controller.log'.format(settings.SOJOBO_API_DIR))
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    loop.run_until_complete(bootstrap_google_controller(sys.argv[1], sys.argv[2],
                                              sys.argv[3]))
    loop.close()
