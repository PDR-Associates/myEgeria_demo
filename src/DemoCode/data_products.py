""" python

   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a utility function for my_egeria.


"""
import os

from pyegeria import CollectionManager
from textual import on
from textual.app import App
from textual.message import Message
from splash_screen import SplashScreen
from data_product_screen import DataProductScreen


class DataProducts(App):

    SCREENS = {
        "splash": SplashScreen,
        "main_menu": DataProductScreen
    }

    class EgeriaDataReceived(Message):
        def __init__(self, data: list):
            super().__init__()
            self.data = data

    def __init__(self):
        self.Egeria_config = ["https://127.0.0.1:9443", "qs-view-server", "erinoverview", "secret"]
        self.collections: list = []
        super().__init__()

    def on_mount(self):
        self.title = "MyEgeria"
        self.subtitle = "Data Products"
        # display the splash screen
        self.log(f"Pushing Splash Screen")
        self.push_screen("splash")

    @on(SplashScreen.SplashContinue)
    def handle_splash_screen_splash_continue(self):
        """ Continue received from the Splash Screen"""
        self.log(f"Continue received from Splash Screen, pushing Data Product Screen")
        # run the function to retrieve collections data from Egeria
        self.log(f"Retrieving Data Products from Egeria - get_collections_from_egeria")
        self.collections = self.get_collections_from_egeria(Egeria_config=self.Egeria_config, Search_str = "*")
        # Create an instance of the Data Products Screen and pass it the data retrieved from Egeria
        main_screen_instance = DataProductScreen(self.collections)
        # Push the Data Products Screen instance to the screen stack to display
        self.push_screen(main_screen_instance)

    def on_data_product_screen_quit_requested(self) -> None:
        """ Quit the application gracefully with a "good" return code (200) """
        self.log(f"Quit requested from Data Product Screen")
        self.exit(200)

    def get_collections_from_egeria(self, Egeria_config: list, Search_str: str) -> list:
        self.log(f"Creating client and Connecting to Egeria using: , {Egeria_config}")
        self.platform_url = Egeria_config[0]
        self.view_server = Egeria_config[1]
        self.user = Egeria_config[2]
        self.password = Egeria_config[3]
        self.log(f"Connecting to Egeria using: , {self.platform_url}")
        self.log(f"Connecting to Egeria using: , {self.view_server}")
        self.log(f"Connecting to Egeria using: , {self.user}")
        self.log(f"Connecting to Egeria using: , {self.password}")
        try:
            c_client = CollectionManager(self.view_server, self.platform_url, user_id=self.user, )
            c_client.create_egeria_bearer_token(self.user, self.password)
            response = c_client.find_collections(search=Search_str, output_format="DICT")
            # response = c_client._async_find_collections(search=Search_str, output_format="DICT")
            # Close the Egeria Client to save resources
            c_client.close_session()
            for entry in response:
                qualified_name = entry.get("qualifiedName", "")
                # if typeName = "DigProdCatalog" or whatever
                self.collections.append(entry)
        except Exception as e:
            self.log(f"Error connecting to Egeria: {str(e)}")
            self.collections.append(f"Egeria Error: {str(e)}")

        return self.collections

if __name__ == "__main__":
    os.environ.setdefault("EGERIA_PLATFORM_URL", "https://127.0.0.1:9443")
    os.environ.setdefault("EGERIA_VIEW_SERVER", "qs-view-server")
    os.environ.setdefault("EGERIA_USER", "erinoverview")
    os.environ.setdefault("EGERIA_USER_PASSWORD", "secret")
    DataProducts().run()