import asyncio

from typing import Callable

import numpy as np
import tornado.httpserver
import tornado.ioloop

from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.document import Document
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado


def bkapp(doc: Document):
    x = np.linspace(0, 2 * np.pi)
    y = np.sin(x)
    source = ColumnDataSource(dict(x=x, y=y))

    p = figure(sizing_mode='stretch_both')
    p.circle(x='x', y='y', source=source)

    doc.add_root(p)


def make_bkapp(app: Callable[[Document], None]) -> Application:
    return Application(FunctionHandler(app))


async def bkmain():
    io_loop = tornado.ioloop.IOLoop.current()
    tornado_app = BokehTornado(
        make_bkapp(bkapp),
        extra_websocket_origins=['localhost:8888'],
    )
    http_server = tornado.httpserver.HTTPServer(tornado_app)
    http_server.listen(8888)
    bokeh_server = BaseServer(
        io_loop,
        tornado_app,
        http_server,
    )
    bokeh_server.start()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(bkmain())
