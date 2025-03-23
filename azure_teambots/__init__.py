#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Azure Teams Bot.

Azure Teams Bot is a Facility for deploying MS Teams Bots.
"""

## more information
from .version import __version__

# Azure Service:
from .service import AzureBots

__all__ = ('AzureBots',)
