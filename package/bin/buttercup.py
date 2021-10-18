import os.path as op
import sys

from solnlib import conf_manager, log
from splunklib import modularinput as smi

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
            realm="__REST_CREDENTIAL__#{}#configs/conf-{}_settings".format(APP_NAME, CONF_NAME))

        logging_details = settings_cfm.get_conf(CONF_NAME+"_settings").get("logging")

        log_level = (
            logging_details.get('loglevel')
            if (logging_details.get('loglevel'))
            else 'INFO'
        )
        return log_level

    except Exception:
        logger.error(
            "Failed to fetch the log details from the configuration taking INFO as default level."
        )
        return 'INFO'


class BUTTERCUP_INPUT(smi.Script):

    def __init__(self):
        super(BUTTERCUP_INPUT, self).__init__()

    def get_scheme(self):
        scheme = smi.Scheme("Buttercup")
        scheme.description = "Go to the add-on's configuration UI and configure modular inputs under the Inputs menu."
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = True

        scheme.add_argument(
            smi.Argument(
                "name",
                title="Name",
                description="Name",
                required_on_create=True
            )
        )

        scheme.add_argument(
            smi.Argument(
                "interval",
                required_on_create=True
            )
        )

        scheme.add_argument(
            smi.Argument(
                'ipAddr',
                required_on_create=True
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
        input_name = list(inputs.inputs.keys())[0]

        input_items = {}
        input_items = inputs.inputs[input_name]
        ip = input_items.get("ipAddr")

        # Generate logger with input name
        _, input_name = (input_name.split('//', 2))
        logger = log.Logs().get_logger('{}_input'.format(APP_NAME))

        # Log level configuration
        log_level = get_log_level(session_key, logger)
        logger.setLevel(log_level)

        logger.debug("Modular input invoked.")

        # Input logic here

        logger.debug("Modular input completed")


if __name__ == "__main__":
    exit_code = BUTTERCUP_INPUT().run(sys.argv)
    sys.exit(exit_code)
