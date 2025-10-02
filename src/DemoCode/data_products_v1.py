""" python

   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a utility function for my_egeria.


"""
import os

from pyegeria import EgeriaTech
from textual.app import App

from splash_screen import SplashScreen
from data_product_screen import DataProductScreen
from demo_service import close_egeria_connection
from typing import Optional

class DataProducts(App):

    SCREENS = {
        "splash": SplashScreen,
        "main_menu": DataProductScreen,
    }

    def __init__(self):
        super().__init__()

    def on_mount(self):
        self.title = "MyEgeria"
        self.subtitle = "Data Products"
        # display the splash screen
        self.log(f"Pushing Splash Screen")
        self.push_screen("splash")

    def on_splash_screen_splash_continue(self):
        self.log(f"Continue received from SAplash Screen, pushing Data Product Screen")
        # display the login screen
        self.push_screen("main_menu")

    def on_data_product_screen_quit_requested(self) -> None:
        """ Quit the application gracefully with a "good" return code (200) """
        self.log(f"Quit requested from Data Product Screen")
        self.exit(200)

if __name__ == "__main__":
    os.environ.setdefault("EGERIA_PLATFORM_URL", "https://127.0.0.1:9443")
    os.environ.setdefault("EGERIA_VIEW_SERVER", "qs-view-server")
    os.environ.setdefault("EGERIA_USER", "erinoverview")
    os.environ.setdefault("EGERIA_USER_PASSWORD", "secret")
    DataProducts().run()