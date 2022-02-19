import asyncio

from typing import Dict, Callable

from prompt_toolkit.keys import Keys
from prompt_toolkit.input import create_input
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.key_binding import KeyBindings


""" https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html#prompt-in-an-asyncio-application """


async def handle_single_key_press(callbacks: Dict[str, Callable]):
    done = asyncio.Event()
    input = create_input()

    def keys_ready():
        for key_press in input.read_keys():
            if key_press.key in callbacks:
                callbacks[key_press.key](key_press.key)
            elif key_press.key == Keys.ControlC:
                done.set()

    with input.raw_mode():
        with input.attach(keys_ready):
            await done.wait()


async def handle_prompt(
        prompt_handler: Callable[[str], None],
        key_bindings_handlers: Dict[str, Callable] = None,
        prompt=''):
    """
    :param prompt_handler:
    :param key_bindings_handlers: eg. {'c-t': Callable, 'c-q, 'f1': Callable}
    (https://python-prompt-toolkit.readthedocs.io/en/master/pages/advanced_topics/key_bindings.html?highlight=control%20alt#list-of-special-keys)
    :param prompt:
    :return:
    """
    session = PromptSession()
    bindings = KeyBindings()

    def _handler(event):
        key = event.key_sequence[0].key
        key_bindings_handlers[key](key)

    for key, handler in key_bindings_handlers.items():
        bindings.add(key)(_handler)

    while True:
        with patch_stdout():
            result = await session.prompt_async(prompt, key_bindings=bindings)
            prompt_handler(result)

