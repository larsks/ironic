import logging
import signal
import subprocess
import multiprocessing
import time

RESTART_POLICY = ['never', 'always', 'on-error', 'on-success']

LOG = logging.getLogger(__name__)


class SupervisorExit (Exception):
    '''Force main supervisor loop to exit.

    This is raised by Supervisor._run_start_command if subprocess.Popen()
    is unable to run start_command.
    '''
    pass


class Supervisor(multiprocessing.Process):
    '''A simple process supervisor.

    A Supervisor instance will run a command, wait for it to finish,
    and optionally restart it based on the `restart` setting, which
    may be one of:

    - `never` -- do not restart the command
    - `always` -- restart the command whenever it exits
    - `on-error` -- restart the command if it fails
    - `on-success` -- restart the command if it succeeds

    If provided, a Supervisor will run `stop_command` after the main
    command exits.  The return code of the stop_command is logged but
    otherwise ignored.

    A command will not be restarted more than once every
    `restart_interval` seconds.
    '''

    def __init__(self, start_command,
                 stop_command=None,
                 restart=None,
                 restart_interval=None,
                 shell=False,
                 close_fds=True):

        '''Initialize a new Supervisor object.

        :param start_command: command to execute
        :param stop_command: command to execute when start_command exits
        :param restart: when to restart start_command
        :param restart_interval: minimum time between restarts
        :param shell: whether to execute command via /bin/sh
        :param close_fds: when True, close all file descriptors before forking
        '''

        super(Supervisor, self).__init__()
        self.daemon = True

        self._quit = False
        self._proc = None

        self.start_command = start_command
        self.stop_command = stop_command
        self.restart = restart if restart else 'never'
        self.restart_interval = restart_interval if restart_interval else 0
        self.shell = shell
        self.close_fds = close_fds

        if self.restart not in RESTART_POLICY:
            raise ValueError(self.restart)

    def _run_start_command(self):
        '''Run the start command.

        Returns the exit code and runtime of the command.
        '''

        LOG.info('running command %s', self.start_command)

        t_start = time.time()

        try:
            self._proc = subprocess.Popen(self.start_command,
                                          shell=self.shell,
                                          close_fds=self.close_fds)
            self._proc.communicate()
            res = self._proc.wait()
        except OSError as e:
            LOG.error('failed to run command: %s', e)

            # An OSError at this point means we are unable to run
            # start_command (missing executable, bad permissions,
            # etc), so just force the main loop to exit.
            raise SupervisorExit

        t_stop = time.time()
        t_delta = t_stop - t_start

        LOG.log(logging.INFO if res == 0 else logging.ERROR,
                'command exited with status %d after %d seconds',
                res, t_delta)

        return res, t_delta

    def _run_stop_command(self):
        '''Run the stop command.'''

        LOG.info('running stop command %s', self.stop_command)
        try:
            stop_res = subprocess.call(self.stop_command,
                                       shell=self.shell)
            LOG.log(logging.INFO if stop_res == 0 else logging.ERROR,
                    'stop command exited with status %d',
                    stop_res)
        except OSError as e:
            LOG.error('failed to run stop command: %s', e)

    def run(self):
        '''Run start_command, restarting it as necessary.'''

        signal.signal(signal.SIGINT, lambda sig, frame: self._cleanup())
        signal.signal(signal.SIGTERM, lambda sig, frame: self._cleanup())

        LOG.info('starting processing supervisor (restart=%s)',
                 self.restart)

        while not self._quit:
            try:
                res, t_delta = self._run_start_command()
            except SupervisorExit:
                break

            if self.stop_command:
                self._run_stop_command()

            if self.restart == 'never':
                LOG.info('not restarting: '
                         'restart is never')
                break
            elif res == 0 and self.restart == 'on-error':
                LOG.info('not restarting: '
                         'command was successful and restart is on-error')
                break
            elif res != 0 and self.restart == 'on-success':
                LOG.info('not restarting: '
                         'command failed and restart is on-success')
                break
            elif self._quit:
                break

            if t_delta < self.restart_interval:
                LOG.info('waiting before restarting command')
                time.sleep(self.restart_interval - t_delta)

        LOG.info('process monitor no longer running')

    def _cleanup(self):
        self._quit = True
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait()
            except OSError:
                pass
