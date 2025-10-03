"""
   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a set of Data Product functions for my_egeria.

"""
import ast
import json
import os

from textual.reactive import reactive
from textual.screen import Screen
from textual import on, work
from textual.app import App
from textual.message import Message
from textual.containers import Container
from textual.widgets import Label, Button, TextArea, Header, Static, Footer
from data_product_screen_current import DataProductScreen
from demo_service import get_config
from pyegeria._output_formats import select_output_format_set
from pyegeria.format_set_executor import exec_format_set


class SplashScreen(Screen):
    """Splash screen with inline styles (no TCSS)."""
    app: "DataProducts"

    class SplashContinue(Message):
        """Message to continue to the login screen."""
        pass

    def __init__(self) -> None:
        super().__init__()
        self.app_title = "My Egeria"
        self.subtitle = "Data Products"
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

    def compose(self):
        cfg = get_config()
        self.view_server = cfg[1]
        self.platform_url = cfg[0]
        self.user = cfg[2]
        self.password = cfg[3]

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
        yield Container(
            Static(
                f"Server: {self.view_server} | Platform: {self.platform_url} | User: {self.user}",
                id="connection_info",
            )
        )
        yield Container(
            Static("MyEgeria", id="title"),
            Static("Data Products", id="main_menu"),
            id="title_row",
        )
        yield top
        yield Button("Continue", variant="primary", id="continue")
        yield Footer()

    async def on_mount(self):
        # Place content in top half, center horizontally
        top = self.query_one("#splash_top", Container)

        top.styles.dock = "top"
        top.styles.height = "50%"
        top.styles.width = "100%"
        top.styles.padding = (1, 2)
        top.styles.align_horizontal = "center"
        top.styles.align_vertical = "top"
        top.styles.gap = 1

        title = self.query_one("#splash_title", Label)
        title.styles.text_align = "center"
        title.styles.text_style = "bold"

        # Fixed visible rows for vertical centering math
        VISIBLE_ROWS = 12

        ta = self.query_one("#splash_text", TextArea)
        ta.styles.width = "90%"
        ta.styles.height = VISIBLE_ROWS  # fixed rows to make vertical centering predictable
        ta.styles.border = ("solid", "white")  # solid white border
        ta.styles.text_style = "bold"
        ta.styles.padding = 1
        ta.styles.text_align = "center"  # horizontal centering of text

        # Vertically center the content by adding top padding lines
        raw_text = self.welcome_text.strip("\n")
        content_lines = raw_text.splitlines() or [raw_text]
        content_rows = len(content_lines)

        # Compute usable rows considering numeric padding
        pad_top = int(getattr(ta.styles.padding, "top", 0) or 0)
        pad_bottom = int(getattr(ta.styles.padding, "bottom", 0) or 0)
        usable_rows = max(VISIBLE_ROWS - (pad_top + pad_bottom), 1)
        top_pad = max((usable_rows - content_rows) // 2, 0)

        ta.value = ("\n" * top_pad) + raw_text

        meta = self.query_one("#splash_meta", Label)
        meta.styles.text_align = "center"

        btn = self.query_one("#continue", Button)
        btn.styles.margin = (1, 0, 0, 0)

    @on(Button.Pressed, "#continue")
    async def continue_to_app(self) -> None:
        """ Quit button pressed, isssue continue message to app """
        self.log(f"Continue button pressed, app is: {self.app}")
        self.post_message(SplashScreen.SplashContinue())


class DataProducts(App):

    SCREENS = {
        "splash": SplashScreen,
        "main_menu": DataProductScreen,
        "_default": DataProductScreen
    }

    DEFAULT_CSS = """
    Screen {
        background: $surface;
        border: solid $primary;
        padding: 1;
        height: auto;
        }
    """

    def __init__(self):
        super().__init__()
        self.Egeria_config = ["https://127.0.0.1:9443", "qs-view-server", "erinoverview", "secret"]
        self.log(f"In Data Products App, init")
        self.platform_url = self.Egeria_config[0]
        self.view_server = self.Egeria_config[1]
        self.user = self.Egeria_config[2]
        self.password = self.Egeria_config[3]
        self.token: str

        """ Access Egeria API using bearer token """
        self.log(f"Accessing Egeria API")
        try:
            self.log(f"initializing egeria client with: , {self.platform_url} , {self.view_server} , {self.user} , {self.password}")
            # Retrieve needed format sets from Egeria
            catalog_set = select_output_format_set("Digital-Product-Catalog-MyE", "DICT")
            if catalog_set:
                self.log("Successfully retrieved format set by name!")
                self.log(f"Heading: {catalog_set['heading']}")
                self.log(f"Description: {catalog_set['description']}")
            else:
                self.log("Failed to retrieve DataProductsCatalogMyE format set by name.")
                self.log("Program Error, please report issue to maintainer.")
                self.exit(400)
            product_set = select_output_format_set("Digital-Products-MyE", "DICT")
            if product_set:
                self.log("Successfully retrieved format set by name!")
                self.log(f"Heading: {product_set['heading']}")
                self.log(f"Description: {product_set['description']}")
            else:
                self.log("Failed to retrieve DataProductsMyE format set by name.")
                self.log("Program Error, please report issue to maintainer.")
                self.exit(400)
        except Exception as e:
            self.log(f"Error connecting to PyEgeria: {str(e)}")
            self.exit(400)

    def on_mount(self):
        self.log(f"on_mount event triggered")
        self.log(f"Getting default screen: SplashScreen")
        self.push_screen("splash")

    @on(SplashScreen.SplashContinue)
    def on_splash_screen_splash_continue(self):
        """ Continue received from the Splash Screen"""
        self.log(f"Continue received from Splash Screen, pushing Data Product Screen")
        # run the function to retrieve collections data from Egeria
        self.log(f"Retrieving Data Products from Egeria - get_collections_from_egeria")
        # self.get_collections_from_egeria(Egeria_config=self.Egeria_config, Search_str = "*")
        try:
            self.collections = [{}]
            response = exec_format_set(
                format_set_name="Digital-Product-Catalog-MyE",
                output_format="DICT",
                view_server=self.view_server,
                view_url=self.platform_url,
                user=self.user,
                user_pass=self.password,
            )
            self.log(f"response: {response}")

            # Robustly extract data payload from response["data"]. Then populate self.collections.
            payload = None
            if isinstance(response, dict) and "data" in response:
                value = response["data"]
                self.log(f"value: {value}")
                if isinstance(value, (dict, list)):
                    payload = value
                    self.log(f"payload: {payload}")
                elif isinstance(value, str):
                    text = value.strip()
                    self.log(f"text: {text}")
                    # Decode text (ast)
                    try:
                        payload = ast.literal_eval(text)
                        self.log(f"payload: {payload}")
                    except Exception:
                        payload = None

            if payload is None:
                self.log("No parsable data found in response['data']")
            else:
                # Ensure self.collections becomes a list of dicts for downstream UI
                if isinstance(payload, list):
                    self.collections = payload
                    self.log(f"collections after extraction: {type(self.collections)} len={len(self.collections)}")
                elif isinstance(payload, dict):
                    # If the dict wraps the actual list of collections under a known key, unwrap it
                    inner = payload.get("collections") if "collections" in payload else None
                    self.log(f"inner: {inner}")
                    if isinstance(inner, list):
                        self.collections = inner
                        self.log(f"collections after extraction: {type(self.collections)} len={len(self.collections)}")
                    else:
                        self.collections = [payload]
                        self.log(f"collections after extraction: {type(self.collections)} len={len(self.collections)}")
                else:
                    # Unknown shape; keep default empty element and log
                    self.log(f"Unexpected payload type: {type(payload)}")

            self.log(f"collections after extraction: {type(self.collections)} len={len(self.collections)}")

            # Normalize keys and values from various response shapes to what the UI expects
            normalized = []
            for item in self.collections:
                if not isinstance(item, dict):
                    continue
                n = {}
                # Map GUID
                n["GUID"] = item.get("GUID") or ""
                # Map display name
                n["displayName"] = item.get("Display Name") or ""
                # Map type name
                n["typeName"] = item.get("Type Name") or ""
                # Map description
                n["description"] = item.get("Description") or ""
                # Map qualified name
                n["qualifiedName"] = item.get("Qualified Name") or ""
                # Members / relationships (optional)
                n["members"] = item.get("Containing Members") or []
                n["memberOf"] = item.get("Member Of") or None
                # Map status
                n["status"] = item.get("Status") or None
                normalized.append(n)
            if normalized:
                self.log(f" Normalized : {normalized}")
                self.collections = normalized
                self.log(f"collections: {type(self.collections)} len={len(self.collections)}")
        except Exception as e:
            self.log(f"Error connecting to Egeria: {str(e)}")
            self.collections = [{"Egeria Error": str(e)}]
        self.log(f"Collections: type: {type(self.collections)}, {len(self.collections)}")
        # Create an instance of the Data Products Screen and pass it the data retrieved from Egeria
        # and push it to the top of screen stack to display
        self.push_screen(DataProductScreen(self.collections))

    def handle_splash_screen_splash_continue(self):
        """Allow direct calls from SplashScreen to continue the app flow."""
        # Delegate to the standard event handler so logic stays in one place
        self.on_splash_screen_splash_continue()

    def on_data_product_screen_quit_requested(self) -> None:
        """ Quit the application gracefully with a "good" return code (200) """
        self.log(f"Quit requested from Data Product Screen")
        self.exit(200)

    def on_data_product_screen_get_members(self, selected_qname):
        """ Retrieve members of a collection """
        self.selected_qualified_name = selected_qname
        try:
            for collection in self.collections:
                if collection.get("qualifiedName") == self.selected_qualified_name:
                    members: list = collection.get("members", [])
                    for member in members:
                        self.collections.append(member)
                        continue
                else:
                    continue
        except Exception as e:
            self.log(f"Error retrieving members of collection {self.selected_qualified_name}: {str(e)}")
            self.collections = [{"Error retrieving members": str(e)}]
        #call Data Product Screen with new collection (Error Notification or members)
        self.push_screen(DataProductScreen(self.collections))

if __name__ == "__main__":
    os.environ.setdefault("EGERIA_PLATFORM_URL", "https://127.0.0.1:9443")
    os.environ.setdefault("EGERIA_VIEW_SERVER", "qs-view-server")
    os.environ.setdefault("EGERIA_USER", "erinoverview")
    os.environ.setdefault("EGERIA_USER_PASSWORD", "secret")
    DataProducts().run()