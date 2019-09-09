#!/usr/bin/env python3

from aws_cdk import core

from waqqastech.waqqastech_stack import WaqqastechStack


app = core.App()
WaqqastechStack(app, "waqqastech")

app.synth()
