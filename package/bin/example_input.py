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
CONF_NAME = "ta_conf21"

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

class EXAMPLE_INPUT(smi.Script):

    def __init__(self):
        super(EXAMPLE_INPUT, self).__init__()

    def get_scheme(self):
        scheme = smi.Scheme('Example Input')
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
            account_name = input_items.get('account')
            account_details = get_account_details(session_key, account_name, logger)
            checkpoint = checkpointer.FileCheckpointer(meta_configs['checkpoint_dir'])
            access_token = account_details.get('password')

            
                    
        except Exception as e:
            logger.exception(e)
            sys.exit(1)
        

        logger.debug("Modular input completed")

if __name__ == '__main__':
    exit_code = EXAMPLE_INPUT().run(sys.argv)
    sys.exit(exit_code)
