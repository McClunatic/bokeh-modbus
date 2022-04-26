"""Simple server app that visualizes Modbus data."""

import asyncio
import time

from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from typing import Any, cast

from bokeh.document.locking import F, NoLockCallback
from bokeh.models import ColumnDataSource
from bokeh.plotting import curdoc, figure


def without_document_lock(func: F) -> NoLockCallback[F]:
    """Wraps a callback function to execute without obtaining a document lock.

    Args:
        func (callable) : The function to wrap

    Returns:
        callable : a function wrapped to execute without a |Document| lock.

    While inside an unlocked callback, it is completely *unsafe* to modify
    ``curdoc()``. The value of ``curdoc()`` inside the callback will be a
    specially wrapped version of |Document| that only allows safe operations,
    which are:

    * :func:`~bokeh.document.Document.add_next_tick_callback`
    * :func:`~bokeh.document.Document.remove_next_tick_callback`

    Only these may be used safely without taking the document lock. To make
    other changes to the document, you must add a next tick callback and make
    your changes to ``curdoc()`` from that second callback.

    Attempts to otherwise access or change the Document will result in an
    exception being raised.

    """
    @wraps(func)
    async def _wrapper(*args: Any, **kw: Any) -> None:
        await func(*args, **kw)
    wrapper = cast(NoLockCallback[F], _wrapper)
    wrapper.nolock = True
    return wrapper


source = ColumnDataSource(data=dict(x=[0], y=[0], color=["blue"]))

i = 0

doc = curdoc()

executor = ThreadPoolExecutor(max_workers=2)


def blocking_task(i):
    time.sleep(1)
    return i


# the unlocked callback uses this locked callback to safely update
async def locked_update(i):
    source.stream(dict(x=[source.data['x'][-1]+1], y=[i], color=["blue"]))


# this unlocked callback will not prevent other session callbacks from
# executing while it is running
@without_document_lock
async def unlocked_task():
    global i
    i += 1
    res = await asyncio.wrap_future(
        executor.submit(blocking_task, i),
        loop=None,
    )

    # Global doc becomes undefined when exiting after KeyboardInterrupt
    if doc:
        doc.add_next_tick_callback(partial(locked_update, i=res))


async def update():
    source.stream(dict(x=[source.data['x'][-1]+1], y=[i], color=["red"]))


p = figure(x_range=[0, 100], y_range=[0, 20])
p.circle(x='x', y='y', color='color', source=source)

doc.add_periodic_callback(unlocked_task, 1000)
doc.add_periodic_callback(update, 200)
doc.add_root(p)
