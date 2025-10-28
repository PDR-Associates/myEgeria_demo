"""
   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a set of report specification related functions for my_egeria.

"""
import ast
import os

from textual import on
from textual.app import ComposeResult, App
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Static, ListView, ListItem, Label, Button, Footer, Header, TextArea


class SplashScreen(ModalScreen):
    """ Egeria Exemplar UI Splash screen """

    class SplashContinue(Message):
        """ Message to indicate user is ready to continue to application"""
        def __init__(self):
            super().__init__()


    def __init__(self) -> None:
        super().__init__()
        self.app_title = "My Egeria"
        self.app_version = "6.0.0"
        self.app_build_date = "2025-09-08"
        self.app_build_time = "00:00"
        self.app_build_author = "Peter Coldicott"
        self.app_build_commit = "00000000000000000"
        self.app_build_branch = "main"
        self.app_build_platform = "MacOS"
        self.welcome_text = (
            "\n\n"
            "This is example UI code package that leverages the Textual/Rich open source UI Frameworks,\n"
            "and the pyegeria package which is part of the Egeria Project.\n\n"
            "The UI is written in Python and is certainly not meant to demonstrate best coding practices!\n\n"
            "Textual/Rich frameworks originally authored by Will McGugan (Textualize).\n\n"
            "My_Egeria SPDX-License-Identifier: Apache-2.0, "
            "Copyright Contributors to the ODPi Egeria project.\n"
        )

    def compose(self) -> ComposeResult:
        top = Container(
            Label(
                f"Welcome to {self.app_title} v{self.app_version} "
                f"({self.app_build_date} {self.app_build_time})",
                id="splash_title",
            ),
            TextArea(self.welcome_text, id="splash_text"),
            Label(
                f"Build Author: {self.app_build_author} | "
                f"Commit: {self.app_build_commit} | "
                f"Branch: {self.app_build_branch} | "
                f"Platform: {self.app_build_platform}",
                id="splash_meta",
            ),
            id="splash_top"
        )
        yield Header(show_clock=True)
        yield Static("Welcome to the Egeria Exemplar UI!")
        yield top
        yield Button("Continue", variant="primary", id="continue_splash")
        yield Footer()

    @on(Button.Pressed, "#continue_splash")
    def handle_continue_splash(self, event: Button.Pressed) -> None:
        self.post_message(self.SplashContinue())
        return
