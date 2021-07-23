# SPDX-FileCopyrightText: 2020 Splunk Inc
#
# SPDX-License-Identifier: Apache-2.0

import import_declare_test
import sys
import json
import os
import os.path as op
import time
import datetime
import traceback
import requests
from splunklib import modularinput as smi
from solnlib import conf_manager
from solnlib import log
from solnlib.modular_input import checkpointer

MINIMAL_INTERVAL = 30
APP_NAME = __file__.split(op.sep)[-3]
CONF_NAME = "ta_dropbox"

def get_log_level(session_key, logger):
    """
    This function returns the log level for the addon from configuration file.
    :param session_key: session key for particular modular input.
    :return : log level configured in addon.
    """
    try:
        settings_cfm = conf_manager.ConfManager(
            session_key,
            APP_NAME,
            realm="__REST_CREDENTIAL__#{}#configs/conf-{}_settings".format(APP_NAME,CONF_NAME))

        logging_details = settings_cfm.get_conf(
            CONF_NAME+"_settings").get("logging")

        log_level = logging_details.get('loglevel') if (
            logging_details.get('loglevel')) else 'INFO'
        return log_level

    except Exception:
        logger.error(
            "Failed to fetch the log details from the configuration taking INFO as default level.")
        return 'INFO'

def get_account_details(session_key, account_name, logger):
    """
    This function retrieves account details from addon configuration file.
    :param session_key: session key for particular modular input.
    :param account_name: account name configured in the addon.
    :param logger: provides logger of current input.
    :return : account details in form of a dictionary.    
    """
    try:
        cfm = conf_manager.ConfManager(
            session_key, APP_NAME, realm='__REST_CREDENTIAL__#{}#configs/conf-{}_account'.format(APP_NAME,CONF_NAME))
        account_conf_file = cfm.get_conf(CONF_NAME + '_account')
        logger.info(f"Fetched configured account {account_name} details.")
        return {
            "username": account_conf_file.get(account_name).get('username'),
            "password": account_conf_file.get(account_name).get('password'),
        }
    except Exception as e:
        logger.error("Failed to fetch account details from configuration. {}".format(
            traceback.format_exc()))
        sys.exit(1)

def get_start_time(start_time_str):
    if start_time_str:
        try:
            dt = datetime.datetime.strptime(start_time_str, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Incorrect Start Time format. Should be YYYY-MM-DD")
    else:
        dt = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=90)

    return datetime.datetime.strftime(dt, '%Y-%m-%dT%H:%M:%SZ')

def send_http_request(access_token, cursor, start_time, category):
    payload = {}
    if cursor:
        dropbox_get_events_url = 'https://api.dropboxapi.com/2/team_log/get_events/continue'
        payload["cursor"] = cursor
    else:
        dropbox_get_events_url = 'https://api.dropboxapi.com/2/team_log/get_events'
        start_time_formatted = get_start_time(start_time)
        payload['time']={"start_time": start_time_formatted}
        if category:
            payload['category'] = category

    # set up the Dropbox auth header
    headers = {}
    headers["Authorization"] = "Bearer %s" % access_token
    headers["Content-Type"] = "application/json"

    try:
        r = requests.post(dropbox_get_events_url, headers=headers, data=json.dumps(payload), timeout=10)
        r.raise_for_status()
    except Exception as e:
        raise e
    return r

class DROPBOX(smi.Script):

    def __init__(self):
        super(DROPBOX, self).__init__()

    def get_scheme(self):
        scheme = smi.Scheme('Dropbox')
        scheme.description = 'Go to the add-on\'s configuration UI and configure modular inputs under the Inputs menu.'
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = True

        scheme.add_argument(
            smi.Argument(
                'name',
                title='Name',
                description='Name',
                required_on_create=True
            )
        )
        
        scheme.add_argument(
            smi.Argument(
                'interval',
                required_on_create=True,
            )
        )
        
        scheme.add_argument(
            smi.Argument(
                'start_time',
                required_on_create=False,
            )
        )

        scheme.add_argument(
            smi.Argument(
                'category',
                required_on_create=False,
            )
        )
        
        scheme.add_argument(
            smi.Argument(
                'account',
                required_on_create=True,
            )
        )
        
        return scheme

    def validate_input(self, definition):
        interval = int(definition.parameters.get('interval'))

        if interval < MINIMAL_INTERVAL:
            raise ValueError("Interval must be at least {} seconds".format(MINIMAL_INTERVAL))

    def stream_events(self, inputs, ew):

        meta_configs = self._input_definition.metadata
        session_key = meta_configs['session_key']
        
        input_items = {}
        input_name = list(inputs.inputs.keys())[0]
        input_items = inputs.inputs[input_name]
        
        # Generate logger with input name
        _, input_name = (input_name.split('//', 2))
        logger = log.Logs().get_logger('{}_input'.format(APP_NAME))

        # Log level configuration
        log_level = get_log_level(session_key, logger)
        logger.setLevel(log_level)

        checkpoint_key = "{}_{}".format(input_name, 'cursor')

        logger.debug("Modular input invoked.")

        try:
            start_time = input_items.get('start_time')
            category = input_items.get('category')
            account_name = input_items.get('account')
            account_details = get_account_details(session_key, account_name, logger)
            checkpoint = checkpointer.FileCheckpointer(meta_configs['checkpoint_dir'])
            access_token = account_details.get('password')

            has_more = True
            while(has_more):
                # call Dropbox API
                cursor = checkpoint.get(checkpoint_key)
                response = send_http_request(access_token, cursor, start_time, category)
                logger.debug(response)

                # check status code
                if response.status_code != 200:
                    logger.error("%s %s" % (response.status_code, response.content))
                    break

                r_json = json.loads(response.content)
                dropbox_events = r_json['events']
                has_more = r_json['has_more']
                new_cursor = r_json['cursor']

                # log num of events
                logger.info("Got {} events. Has more: {}".format(len(dropbox_events), has_more))

                # convert all Dropbox-events to Splunk-events
                for dropbox_event in dropbox_events:
                    event = smi.Event()
                    event.stanza = input_name
                    event.source = input_name
                    event.data = json.dumps(dropbox_event)
                    ew.write_event(event)
                
                # update checkpoint
                checkpoint.update(checkpoint_key, new_cursor)
                    
        except Exception as e:
            logger.exception(e)
            sys.exit(1)
        

        logger.debug("Modular input completed")

if __name__ == '__main__':
    exit_code = DROPBOX().run(sys.argv)
    sys.exit(exit_code)
