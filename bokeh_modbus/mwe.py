"""A simple asynchronous client."""

import asyncio
import datetime
import math
import sys
import time

from bokeh.document import Document
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.server.server import Server


def bkapp(doc: Document):

    x = time.time()
    source = ColumnDataSource(dict(
        x=[datetime.datetime.fromtimestamp(x)],
        y=[math.sin(x)],
    ))

    p = figure(sizing_mode='stretch_both', x_axis_type='datetime')
    p.circle(x='x', y='y', source=source)
    p.x_range.follow = 'end'
    p.x_range.follow_interval = datetime.timedelta(seconds=15)

    def callback():
        x = time.time()
        source.stream(dict(
            x=[datetime.datetime.fromtimestamp(x)],
            y=[math.sin(x)],
        ))

    doc.add_periodic_callback(callback, 200)
    doc.add_root(p)


async def main():
    """Runs the asynchronous client."""

    bokeh_server = Server(bkapp, port=8888)
    bokeh_server.start()
    bokeh_server.show('/')
    await asyncio.Event().wait()


if __name__ == '__main__':
    try:
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
