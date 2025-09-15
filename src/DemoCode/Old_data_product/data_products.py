""" python

   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a utility function for my_egeria.


"""
import os

from textual.app import App

from splash_screen import SplashScreen
from login_screen import LoginScreen
from base_screen import BaseScreen
from data_product_screen import DataProductScreen
from demo_service import DemoService
from typing import Optional

class DataProducts(App):

    SCREENS = {
        "Base": BaseScreen,
        "splash": SplashScreen,
        "login": LoginScreen,
        "main_menu": DataProductScreen,
    }

    def __init__(self):
        super().__init__()

    def on_mount(self):
        self.title = "MyEgeria"
        self.subtitle = "Data Products"
        # display the splash screen
        self.push_screen("splash")

    def on_splash_screen_splash_continue(self):
        # display the login screen
        self.switch_screen("login")

    def on_login_screen_login_success(self):
        # login was successful, so display the main menu
        self.switch_screen("main_menu")

    def on_login_screen_quit_requested(self, login_return_code:Optional[int]):
        """ Quit the application gracefully with a "good" return code (200) """
        self.login_return_code = login_return_code
        DemoService.close_egeria_connection(self)
        self.exit(self.login_return_code)

    def on_data_product_screen_quit_requested(self) -> None:
        """ Quit the application gracefully with a "good" return code (200) """
        DemoService.close_egeria_connection()
        self.exit(200)


if __name__ == "__main__":
    os.environ.setdefault("EGERIA_PLATFORM_URL", "https://localhost:9443")
    os.environ.setdefault("EGERIA_VIEW_SERVER", "qs-view-server")
    os.environ.setdefault("EGERIA_USER", "erinoverview")
    os.environ.setdefault("EGERIA_USER_PASSWORD", "secret")
    DataProducts().run()