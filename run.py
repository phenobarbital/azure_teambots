#!/usr/bin/env python3
import asyncio
import time
from functools import partial
from aiohttp import web
from navigator import Application
from app import Main

# Start NAV Application with Jinja2 Support
app = Application(Main, enable_jinja2=True)


if __name__ == '__main__':
    try:
        app.run()
    except KeyboardInterrupt:
        print(
            "Closing Azure Bot Service ..."
        )
