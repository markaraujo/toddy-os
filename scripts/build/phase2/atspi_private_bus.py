"""Run unchanged AT-SPI tests on real private D-Bus/compiled registry processes."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    assert os.getuid() == 101 and os.environ.get('DBUS_SESSION_BUS_ADDRESS')
    # Upstream atspi-misc.c accepts AT_SPI_BUS_ADDRESS. Keep configuration and
    # activation services private: no installed/global bus or session mock.
    with tempfile.TemporaryDirectory(prefix='toddy-a11y-', dir='/tmp') as tmp:
        root = Path(tmp)
        services = root / 'dbus-1/accessibility-services'
        services.mkdir(parents=True)
        service = services / 'org.a11y.atspi.Registry.service'
        service.write_text('[D-BUS Service]\nName=org.a11y.atspi.Registry\n'
                           'Exec=/build/compile/registryd/at-spi2-registryd\n')
        template = Path('/src/bus/accessibility.conf.in').read_text()
        assert template.count('@DATADIR@') == template.count('@SOCKET_ADDRESS@') == 1
        config = root / 'accessibility.conf'
        expected_address = 'unix:path=' + str(root / 'bus')
        config.write_text(template.replace('@DATADIR@', str(root))
                          .replace('@SOCKET_ADDRESS@', expected_address))
        with (Path('/build') / ('private-a11y-' + sys.argv[1] + '.log')).open('xb') as log:
            daemon = subprocess.Popen(['dbus-daemon', '--nofork', '--print-address=1',
                                       '--config-file=' + str(config)],
                                      stdout=subprocess.PIPE, stderr=log, text=True,
                                      env=dict(os.environ, AT_SPI_BUS_ADDRESS=expected_address))
            try:
                address = daemon.stdout.readline().strip()
                assert address.startswith(expected_address) and daemon.poll() is None
                env = dict(os.environ, AT_SPI_BUS_ADDRESS=address)
                result = subprocess.run(['meson', 'test', '-C', '/build/compile',
                                         '--no-rebuild', '--num-processes', '1',
                                         '--print-errorlogs', *sys.argv[2:]], env=env)
                return result.returncode
            finally:
                if daemon.poll() is None:
                    daemon.terminate()
                daemon.wait(timeout=10)


if __name__ == '__main__':
    raise SystemExit(main())
