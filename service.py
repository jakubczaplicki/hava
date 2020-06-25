"""
Bit rate :9600
Data bit :8
Parity bit:NO
Stop bit:1
Data Packet frequency:1Hz

Check-sum: Check-sum=DATA1+DATA2+...+DATA6.
PM2.5 value: PM2.5 (μg /m3) = ((PM2.5 High byte *256) + PM2.5 low byte)/10
PM10 value: PM10 (μg /m3) = ((PM10 high byte*256) + PM10 low byte)/10
"""
import asyncio
import contextlib
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import aiosqlite
import pygame

from hava.airquality_data_collector.serial_port import SerialPort

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (250, 250, 210)

log = logging.getLogger(__name__)


class AirQualityDataCollector:

    def __init__(self, args, loop=None):
        self._closing = False
        self.args = args
        self.loop = loop

        self.serial = SerialPort(self.args.serial_port)
        self.executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix='DefaultSerialPortThreadPoolExecutor'
        )
        self.store_data_interval = 60

        self.task_store_data = None

    async def setup(self):
        self.serial.open()
        log.info('Opened port %r', self.serial.device)
        log.info('Testing DB connection to %r', self.args.db_uri)
        try:
            async with aiosqlite.connect(self.args.db_uri) as db:
                cursor = await db.execute('SELECT * FROM air')
                rows = await cursor.fetchall()
                await cursor.close()
                log.info('Successfully fetched %s rows', len(rows))
        except Exception as e:
            log.error('%s: %s.', type(e).__name__, e)
            raise
        # setup display
        # XXX: factor out hardcoded values to cli
        os.putenv('DISPLAY', ':0')
        os.putenv('SDL_FBDEV', '/dev/fb1')
        pygame.init()
        self.lcd = pygame.display.set_mode((480, 320))
        pygame.display.toggle_fullscreen()
        self.font_small = pygame.font.SysFont("freemono", 25)
        self.font_medium = pygame.font.SysFont("freemono", 32)
        self.font_medium2 = pygame.font.SysFont("freemono", 35)
        self.font_big = pygame.font.SysFont("freemono", 50)
        self.lcd.fill(BLACK)
        pygame.display.update()

    def parse_sds011_data(self, data):
        if data and len(data) > 9:
            if (sum(data[2:8]) % 256) == data[8]:
                pm25 = (((data[3] * 256) + data[2]) / 10)
                pm10 = (((data[5] * 256) + data[4]) / 10)
                return pm25, pm10
            log.error("SDS011: checksum error")
        return None, None

    async def get_sds011_data(self):
        data = await self.loop.run_in_executor(
            self.executor,
            self.serial.read
        )
        return data

    async def run(self):
        # Keep fetching measurements as fast as possible counting moving average
        # After N seconds trigger a task to save data to a db.
        log.info('Starting a periodic task to read data from %r',
                 self.args.serial_port)
        try:
            start_time = time.time()
            n = 0
            avg_pm25 = avg_pm10 = None
            while not self._closing:
                try:
                    raw_data = await self.get_sds011_data()
                    pm25, pm10 = self.parse_sds011_data(raw_data)
                    n += 1
                except Exception as e:
                    log.error('Could not read data from %r: %s: %s.',
                              self.args.serial_port, type(e).__name__, e)
                    await asyncio.sleep(1)
                    continue
                if pm25 is None or pm10 is None:
                    log.error('Missing data from %r: (%s, %s).',
                              self.args.serial_port, pm25, pm10)
                    await asyncio.sleep(1)
                    continue
                self.display_data(int(time.time()), pm25, pm10)
                # Calculate moving avg: new_avg = old_avg * (n-1)/n + new_val/n
                avg_pm25 = ((avg_pm25 * (n - 1) / n + pm25 / n)
                            if avg_pm25 else pm25)
                avg_pm10 = ((avg_pm10 * (n - 1) / n + pm10 / n)
                            if avg_pm10 else pm10)
                log.debug('%r moving avg: %r, %r', n, avg_pm25, avg_pm10)
                stop_time = time.time()
                session_time = stop_time - start_time
                if session_time >= self.store_data_interval:
                    log.info("Session time took %d seconds", session_time)
                    measured_at = int(time.time())
                    avg_pm25 = round(avg_pm25, 2)
                    avg_pm10 = round(avg_pm10, 2)
                    coro = self.store_data(measured_at, avg_pm25, avg_pm10)
                    self.task_store_data = self.loop.create_task(coro)
                    avg_pm25 = pm25
                    avg_pm10 = pm10
                    n = 0
                    start_time = time.time()
                    asyncio.sleep(0)
        except asyncio.CancelledError:
            log.info('Data read task has been cancelled.')
            raise

    async def store_data(self, created_at, pm25, pm10):
        log.info('Starting a task to store: %s, %s, %s', created_at, pm25, pm10)
        async with aiosqlite.connect(self.args.db_uri) as db:
            await db.execute(
                'INSERT INTO air (created_at, pm25, pm10) '
                'VALUES (?, ?, ?)', (created_at, pm25, pm10)
            )
            await db.commit()
        log.info('Data storage task has finished.')

    def display_data(self, measured_at, pm25, pm10):
        # XXX : this should probably be optimised
        t = datetime.fromtimestamp(measured_at).strftime("%d-%m-%Y %H:%M:%S")
        self.lcd.fill(BLACK)
        text_surface_name = self.font_medium.render(
            'Stowarzyszenie Pracownia', True, WHITE)
        text_surface_def1 = self.font_small.render(
            'Mobilna stacja pomiaru', True, WHITE)
        text_surface_def2 = self.font_small.render(
            'pyłu zawieszonego.', True, WHITE)
        text_surface_pm25 = self.font_big.render(
            'PM2.5: {:.2f} µm'.format(pm25), True, WHITE)
        text_surface_pm10 = self.font_big.render(
            'PM1.0: {:.2f} µm'.format(pm10), True, WHITE)
        text_surface_date = self.font_medium2.render(
            '%s' % t, True, WHITE)
        self.lcd.blit(text_surface_name, (7, 8))
        self.lcd.blit(text_surface_def1, (5, 60))
        self.lcd.blit(text_surface_def2, (5, 90))
        self.lcd.blit(text_surface_pm25, (10, 160))
        self.lcd.blit(text_surface_pm10, (10, 210))
        self.lcd.blit(text_surface_date, (10, 270))
        img = pygame.image.load('logo.png')
        img = pygame.transform.scale(img, (150, 150))
        self.lcd.blit(img, (480 - 150, 30))
        pygame.display.update()

    async def close(self):
        self._closing = True
        for task in [self.task_store_data]:
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task


async def create_air_quality_data_collector(args, loop):
    collector = AirQualityDataCollector(args, loop=loop)
    await collector.setup()
    return collector
