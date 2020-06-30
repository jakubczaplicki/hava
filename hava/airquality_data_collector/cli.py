import asyncio
import os
import sys
import logging
from argparse import ArgumentParser
from logging.handlers import TimedRotatingFileHandler

from .service import create_air_quality_data_collector

DEFAULT_SENSOR = os.getenv('AIR_QUALITY_SENSOR', 'sds011')
DEFAULT_SERIAL_PORT = os.getenv('SDS011_SERIAL_PORT', '/dev/ttyUSB0')
DEFAULT_DB_URI = os.getenv('DB_URI', 'measurements.db')
DEFAULT_FONT_SIZE = int(os.getenv('HAVA_FONT_SIZE', '60'))

STARTUP_TIMEOUT = 20

log = logging.getLogger(__name__)


def configure_logging(args):
    if args.log_level == 'NONE':
        return
    kwargs = dict(
        level=args.log_level
    )
    if args.log_file != '-':
        handler = TimedRotatingFileHandler(
            args.log_file,
            when='midnight',
            backupCount=6,
        )
        kwargs['handlers'] = [handler]
    logging.basicConfig(**kwargs)


def parse_args(args, parser=ArgumentParser()):
    parser.add_argument('--serial-port',
                        default=DEFAULT_SERIAL_PORT,
                        help="Serial Port for SDS011")
    parser.add_argument('--db-uri',
                        default=DEFAULT_DB_URI,
                        help='Database URI')
    parser.add_argument('--log-level', default='INFO')
    parser.add_argument('--log-file', default='-')

    parser.add_argument('--font-size',
                        default=DEFAULT_FONT_SIZE,
                        help='Display font size',
                        type=int)
    args = parser.parse_args(args)
    return args


def main(args=sys.argv[1:]):
    args = parse_args(args)
    configure_logging(args)

    loop = asyncio.get_event_loop()
    try:
        data_collector = loop.run_until_complete(
            asyncio.wait_for(
                create_air_quality_data_collector(args=args, loop=loop),
                STARTUP_TIMEOUT))
    except asyncio.TimeoutError as e:
        log.critical('Startup timed out: %s', e)
        raise
    except Exception as e:
        log.critical('Unable to setup the service: %s', e)
        raise

    try:
        log.info('Ready...')
        loop.run_until_complete(data_collector.run())
    except KeyboardInterrupt:
        log.info('Keyboard Interrupt, shutting down.')
    except Exception as e:
        log.exception('There was an unexpected error during processing: %s', e)
    finally:
        loop.run_until_complete(data_collector.close())
        log.info('Bye.')
        loop.close()


if __name__ == '__main__':
    main()
