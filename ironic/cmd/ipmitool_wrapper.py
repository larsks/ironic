'''ipmitool wrapper for spawning serial-over-lan connections

This wrapper avoids serial console lockout by calling
"ipmitool ... sol deactivate" before calling "ipmitool ... sol activate".
'''

import os
import subprocess
import sys

from oslo_config import cfg

from ironic.common.i18n import _

CONF = cfg.CONF

options = [
    cfg.BoolOpt('force-sol-deactivate',
                default=True,
                help=_('Deactivating sol session before starting a new one'))
]


def main():
    # Split the command line on '--' into arguments for our script and the
    # ipmitool command itself.
    idx = sys.argv.index('--')
    our_args = sys.argv[1:idx]
    ipmitool_args = sys.argv[idx + 1:]

    CONF.register_opts(options, group='console')
    CONF(our_args, project='ironic')

    if (
            CONF.console.force_sol_deactivate and
            ipmitool_args[-2:] == ['sol', 'activate']
    ):
        cmd = ipmitool_args[:-2] + ['sol', 'deactivate']
        with open(os.devnull, 'w+') as null:
            subprocess.call(cmd, stdout=null, stderr=null, stdin=null)

    os.execvp(ipmitool_args[0], ipmitool_args)


if __name__ == '__main__':
    sys.exit(main())
