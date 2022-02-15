from enum import Enum
from fastapi import FastAPI, HTTPException, Depends
from starlette.requests import Request
from starlette.responses import Response

import mape
from mape.loop import Loop
from mape.base_elements import Element


class Port(str, Enum):
    p_in = 'in'
    p_out = 'out'


class Notification(str, Enum):
    next = 'next'
    error = 'error'
    completed = 'completed'


element_notify_path = '/loops/{loop_uid}/elements/{element_uid}'


def api_setup(fastapi_app: FastAPI, mape_app: mape.App):
    def common_loop(loop_uid: str) -> Loop:
        if loop_uid not in mape_app.loops:
            raise HTTPException(status_code=400, detail=f"Loop '{loop_uid}' does not exist")

        return mape_app.loops[loop_uid]

    def common_element(element_uid: str, loop: Loop = Depends(common_loop)) -> Element:
        if element_uid not in mape_app.loops[loop.uid]:
            raise HTTPException(status_code=400, detail=f"Element '{element_uid}' does not exist")

        return mape_app.loops[loop.uid][element_uid]

    @fastapi_app.get('/loops', tags=['loops'],
                     summary='Create an item', response_description='The created item')
    async def get_loops():
        return list(mape_app.loops.keys())

    @fastapi_app.get('/loops/{loop_uid}/elements',
                     tags=['elements'], summary='Create an item', response_description='The created item')
    async def get_elements(loop: common_loop = Depends()):
        return list(loop.elements.keys())

    @fastapi_app.get('/levels',
                     tags=['levels'], summary='Create an item', response_description='The created item')
    async def get_levels():
        return list(mape_app.levels.keys())

    @fastapi_app.post(element_notify_path,
                      tags=['elements'],
                      summary='Create an item',
                      response_description='The created item')
    async def element_notify(request: Request,
                             element: common_element = Depends(),
                             port: Port = Port.p_in,
                             notification: Notification = Notification.next):
        """
        Create an item with all the information:

        - **name**: each item must have a name
        - **description**: a long description
        - **price**: required
        - **tax**: if the item doesn't have tax, you can omit this
        - **tags**: a set of unique tag strings for this item
        """
        port = element.port_in if port is Port.p_in else element.port_out

        payload = await request.body()
        # TODO: deserialize
        from mape.redis_remote import _deserializer
        payload = _deserializer(payload)

        if notification is Notification.next:
            port.on_next(payload)
        elif notification is Notification.error:
            port.on_error(payload)
        elif notification is Notification.completed:
            port.on_completed()
