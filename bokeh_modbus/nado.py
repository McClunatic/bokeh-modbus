import asyncio

import numpy as np

from bokeh.document import Document
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.server.server import Server


def bkapp(doc: Document):
    x = np.linspace(0, 2 * np.pi)
    y = np.sin(x)
    source = ColumnDataSource(dict(x=x, y=y))

    p = figure(sizing_mode='stretch_both')
    p.circle(x='x', y='y', source=source)

    doc.add_root(p)


async def main():
    bokeh_server = Server({'/': bkapp})
    bokeh_server.start()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
