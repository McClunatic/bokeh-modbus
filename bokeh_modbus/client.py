"""A simple asynchronous client."""

import asyncio
import logging
import time

from typing import List

import numpy as np

from pymodbus.client.asynchronous.async_io import ModbusClientProtocol
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
from pymodbus.client.asynchronous import schedulers

# Set up basic logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def convert_bits(timeb: List[bool], sinb: List[bool]):
    """Converts `timeb` bits and `sinb` bits to time and float.

    Args:
        timeb: 64 bits representing current server time.
        sinb: 32 bits representing current server sin(t).
    """

    # Convert time bits
    bstring = ''.join(['1' if bit else '0' for bit in timeb])
    localtime = time.localtime(
        np.asarray(int(bstring, 2), dtype=np.uint64).view(np.float64).item(),
    )

    # Convert sin(t) bits
    bstring = ''.join(['1' if bit else '0' for bit in sinb])
    sin = np.asarray(int(bstring, 2), dtype=np.uint32).view(np.float32).item()

    log.debug(
        'time: %s\tsin(t): %.6f',
        time.strftime('%H:%M:%S', localtime),
        sin,
    )


async def read_coils(protocol: ModbusClientProtocol, interval: float = 0.5):
    """Reads Modbus coils using client `protocol`.

    Args:
        protocol: Modbus protocol instance.
        interval: Interval in seconds between reads.
    """

    log.debug('Reading coils...')
    while True:
        try:
            # Read coils for time bits
            rrt = await protocol.read_coils(0, 64)
            time_bits = rrt.bits

            # Read coils for sin(t) bits
            rrs = await protocol.read_coils(64, 32)
            sin_bits = rrs.bits

            convert_bits(time_bits, sin_bits)
            await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            log.debug('Stopped reading coils')
            break


async def main():
    """Runs the asynchronous client."""

    loop = asyncio.get_running_loop()
    loop, client = AsyncModbusTCPClient(
        schedulers.ASYNC_IO,
        port=5020,
        loop=loop,
    )
    client = await client
    task = loop.create_task(read_coils(client.protocol))
    await task


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
