#!/usr/bin/env python3

from aws_cdk import core

from waqqastech.waqqastech_stack import WaqqastechStack

app = core.App()
WaqqastechStack(
    app, "waqqastech",
    env={"region": "us-east-1", "account": "147218828400"},
)

app.synth()
