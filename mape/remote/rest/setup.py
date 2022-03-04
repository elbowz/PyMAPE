from __future__ import annotations

from fastapi import FastAPI
from textwrap import dedent

import mape
from .api import api_setup

fastapi: FastAPI | None = None

description = dedent('''
        MAPE framework RESTfull API interface
       
        ## Levels
        
        You can **read items**.
        
        ## Loops
        
        You can **read items**.
        
        ## Elements
        
        You will be able to:
        
        * **Levels** (_not implemented_).
        * **Post** (_not implemented_).''')

tags_metadata = [
    {
        'name': 'levels',
        'description': 'Operation with levels',
    },
    {
        'name': 'loops',
        'description': 'Operations with loops',
    },
    {
        'name': 'elements',
        'description': 'Operations with Elements',
    },
]


def setup(mape_app: mape.App, version):
    global fastapi

    if not fastapi:
        fastapi = FastAPI(
            title='MAPE framework',
            description=description,
            version=version,
            terms_of_service='http://example.com/terms/',
            contact={
                'name': 'Emanuele Palombo',
                'url': 'https://github.com/elbowz',
                # 'email': 'ask@x-force.example.com',
            },
            license_info={
                'name': 'GPL-3.0 License',
                'url': 'https://www.gnu.org/licenses/gpl-3.0.en.html',
            },
            openapi_tags=tags_metadata
        )

        api_setup(fastapi, mape_app)

    return fastapi
