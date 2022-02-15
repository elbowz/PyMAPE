from __future__ import annotations

import purse

from mape.remote.de_serializer import obj_from_raw, list_from_raw, obj_to_raw


def purse_monkey_patch():
    purse.collections._obj_from_raw = obj_from_raw
    purse.collections._list_from_raw = list_from_raw
    purse.collections._obj_to_raw = obj_to_raw
