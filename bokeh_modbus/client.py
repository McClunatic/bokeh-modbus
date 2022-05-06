"""A simple asynchronous client."""

import asyncio
import datetime
import functools
import logging
import time

from typing import List, Tuple

import numpy as np

from bokeh.document import Document
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.server.server import Server

from pymodbus.client.asynchronous.async_io import ModbusClientProtocol
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
from pymodbus.client.asynchronous import schedulers


# Set up basic logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def convert_bits(timeb: List[bool], sinb: List[bool]) -> Tuple[float, float]:
    """Converts `timeb` bits and `sinb` bits to time and float.

    Args:
        timeb: 64 bits representing current server time.
        sinb: 32 bits representing current server sin(t).

    Returns:
        Tuple of `(epoch_time, sin(epoch_time))`.`
    """

    # Convert time bits
    bstring = ''.join(['1' if bit else '0' for bit in timeb])
    tyme = np.asarray(int(bstring, 2), dtype=np.uint64).view(np.float64).item()

    # Convert sin(t) bits
    bstring = ''.join(['1' if bit else '0' for bit in sinb])
    sin = np.asarray(int(bstring, 2), dtype=np.uint32).view(np.float32).item()

    return tyme, sin


async def read_coils(
    protocol: ModbusClientProtocol,
) -> Tuple[float, float]:
    """Reads Modbus coils using client `protocol`.

    Args:
        protocol: Modbus protocol instance.

    Returns:
        Tuple of `(epoch_time, sin(epoch_time))`.`
    """

    while True:
        try:
            # Read coils for time bits
            rrt = await protocol.read_coils(0, 64)
            time_bits = rrt.bits

            # Read coils for sin(t) bits
            rrs = await protocol.read_coils(64, 32)
            sin_bits = rrs.bits

            epoch_time, sin = convert_bits(time_bits, sin_bits)
            return epoch_time, sin
        except asyncio.CancelledError:
            break


def bkapp(doc: Document, protocol: ModbusClientProtocol):

    source = ColumnDataSource(dict(
        x=[datetime.datetime.fromtimestamp(time.time())],
        y=[np.sin(time.time())],
    ))

    p = figure(sizing_mode='stretch_both', x_axis_type='datetime')
    p.circle(x='x', y='y', source=source)
    p.x_range.follow = 'end'
    p.x_range.follow_interval = datetime.timedelta(seconds=15)

    async def callback(
        # source: ColumnDataSource = source,
        protocol: ModbusClientProtocol = protocol,
    ):
        epoch_time, sin = await read_coils(protocol)
        x = datetime.datetime.fromtimestamp(epoch_time)
        y = sin
        log.debug('time: %s\tsin(t): %.6f', x, y)
        source.stream(dict(x=[x], y=[y]))

    doc.add_periodic_callback(callback, 200)
    doc.add_root(p)


async def main():
    """Runs the asynchronous client."""

    _, client_task = AsyncModbusTCPClient(
        schedulers.ASYNC_IO,
        port=5020,
        loop=asyncio.get_running_loop(),
    )
    client = await client_task

    bokeh_app = functools.partial(bkapp, protocol=client.protocol)
    bokeh_server = Server(bokeh_app, port=8888)
    bokeh_server.start()
    await asyncio.Event().wait()


if __name__ == '__main__':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        log.debug('Closing Modbus client and Bokeh server')
        pass
