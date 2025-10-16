"""
   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a set of Data Product functions for my_egeria.

"""
import ast
import os

from textual.css.query import NoMatches
from textual.screen import Screen, ModalScreen
from textual import on
from textual.app import App, ComposeResult
from textual.message import Message
from textual.containers import Container, ScrollableContainer, Vertical
from textual.widgets import Label, Button, TextArea, Header, Static, Footer, DataTable
from demo_service import get_config
from pyegeria._output_formats import select_output_format_set
from pyegeria.format_set_executor import exec_format_set
from src.DemoCode.data_product_screen_current import DataProductScreen
from src.DemoCode.members_screen_current import MembersScreen
from src.DemoCode.member_details_screen_current import MemberDetailsScreen

CSS_PATH = ["data_products_css.tcss"]

class SplashScreen(ModalScreen):
    """Splash screen with inline styles (no TCSS)."""

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
        """ Continue button pressed, issue continue message to app """
        self.log(f"Continue button pressed, app is: {self.app}")
        self.post_message(SplashScreen.SplashContinue())


class DataProducts(App):

    SCREENS = {
        "splash": SplashScreen
    }

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "back", "Back"),
    ]

    CSS_PATH = ["data_products_css.tcss"]

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

    def compose(self) -> ComposeResult:
        """Create the layout of the screen."""
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
            id = "title_row",
        )
        yield ScrollableContainer(
            Vertical(
                Static(f"Available Data Product Marketplaces:\n\n", id="before_static"),
                Static("\n\nEnd of DataTable", id="after_static"),
            ),
            id="main_content")
        yield Container(
            Button("Quit", id="quit"),
            id="action_row",
        )
        yield Footer()
        self.log("done yielding, now waiting for user input")

    def on_splash_screen_splash_continue(self):
        """ Continue received from the Splash Screen"""
        self.log(f"Continue received from Splash Screen, so remove splash screen")
        self.pop_screen()
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
            self.collections = payload
            self.log(f"collections after extraction: {type(self.collections)} len={len(self.collections)}")
        except Exception as e:
            self.log(f"Error connecting to Egeria: {str(e)}")
            self.collections = [{"Egeria Error": str(e)}]
        self.log(f"Collections: type: {type(self.collections)}, {len(self.collections)}")
        # Create an instance of the Data Products Screen and pass it the data retrieved from Egeria
        # and push it to the top of screen stack to display
        ROWS = [
            ("GUID", "Display Name", "Qualified Name", "Type Name", "Description"),
        ]
        # dpinstance: DataProductScreen = DataProductScreen(self.collections)
        # self.push_screen(dpinstance)
        self.collection_datatable: DataTable = DataTable()
        # confire the DataTable - collection_datatable
        self.collection_datatable.id = "collection_datatable"
        # Add columns to the DataTable
        self.collection_datatable.add_columns(*DataProductScreen.ROWS[0])
        # set the cursor to row instead of cell
        self.collection_datatable.cursor_type = "row"
        # give the DataTable zebra stripes so it is easier to follow across rows on the screen
        self.collection_datatable.zebra_stripes = True
        # log the results of configuring the DataTable
        # self.log(f"Collection DataTable Created:")
        # self.log(f"Collection DataTable: {self.collection_datatable.columns}")
        # Check that we have at least one Data Product Catalogue
        if self.collections is None:
            # No Data Product Catalogues found
            # self.log("No Data Product Catalogues found")
            self.collection_datatable.add_row("Error", "No Data Product Catalogues found")
        else:
            # Load data into the DataTable
            if type(self.collections) == list:
                try:
                    for entry in self.collections:
                        self.collection_datatable.add_row(
                            entry.get("Display Name", "None"),
                            entry.get("Qualified Name", "None"),
                            entry.get("Type Name", "None"),
                            entry.get("Description", "None"),
                        )
                except Exception as e:
                    self.collection_datatable.add_row("Error", "Error updating collection list", str(e))

            elif type(self.collections) == dict:
                try:
                    self.collection_datatable.add_row(
                        self.collections.get("Display Name", "None"),
                        self.collections.get("Qualified Name", "None"),
                        self.collections.get("Type Name", "None"),
                        self.collections.get("Description", "None")
                    )
                except Exception as e:
                    self.collection_datatable.add_row("Error", "Error unpacking collection dict", str(e))
            else:
                self.collection_datatable.add_row("Error", "Unknown data shape detected", str(type(self.collections)))

        try:
            catalog_mounted =self.query_one("#collection_datatable")
            if not catalog_mounted:
                self.mount(self.collection_datatable, after="#before_static")
            else:
                self.collection_datatable.refresh(layout=True, recompose=True)
        except (NoMatches):
            self.mount(self.collection_datatable, after="#before_static")

    def handle_splash_screen_splash_continue(self):
        """Allow direct calls from SplashScreen to continue the app flow."""
        # Delegate to the standard event handler so logic stays in one place
        self.on_splash_screen_splash_continue()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "quit":
            """ Quit the application gracefully with a "good" return code (200) """
            self.log(f"Quit button clicked")
            self.exit(200)
            return
        else:
            self.log(f"Button pressed: {event.button.id}")
            self.log(f"Unknown button id: {event.button.id}")
            return

    @on(DataTable.RowSelected, "#collection_datatable")
    def handle_catalog_table_row_selected(self, message: DataTable.RowSelected):
        self.log(f"Row Selected, Processing selection")
        self.row_selected = message.row_key
        self.row_selected_data = self.collection_datatable.get_row(message.row_key)
        self.selected_name = self.row_selected_data[0] or ""
        self.selected_qname = self.row_selected_data[1] or ""
        self.selected_type = self.row_selected_data[2] or ""
        self.selected_desc = self.row_selected_data[3] or ""
        # qname = self.selected_qname.split(']')[1].strip('[')
        # self.selected_qname = qname
        self.members_list: list = []
        self.log(f"qname: {self.selected_qname}<====")
        response = exec_format_set(
            format_set_name="Digital-Products-MyE",
            params = {"search_string" : str(self.selected_qname)},
            output_format="DICT",
            view_server=self.view_server,
            view_url=self.platform_url,
            user=self.user,
            user_pass=self.password,
        )
        self.log(f"type: {type(response)}, length: {len(response)}")
        self.log(f"response: {response}")

        # Robustly extract data payload from response["data"]. Then populate self.members.
        payload = None
        # if isinstance(response, dict) and "data" in response:
        if isinstance(response, dict):
            self.log(f"Response from Egeria is a dict")
            value = response.get("data")
            self.log(f"value: {value}")
        elif isinstance(response, list):
            self.log(f"Response from Egeria is a list")
            value = response[0].get("data")
            self.log(f"value: {value}")
        else:
            self.log(f"Unexpected response format: {type(response)}")
            value = response

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
            except Exception as e:
                self.log(f"Exception in Egeria response processing: {str(e)}")
                payload = None

        self.log(f"payload: {type(payload)}")

        if payload is None:
            self.log("No parsable data found in response['data']")
            self.members = None
        else:
            # Ensure self.members becomes a list of dicts for downstream UI
            if isinstance(payload, list):
                self.members = payload
                self.log(f"members after extraction: {type(self.members)} len={len(self.members)}")
            elif isinstance(payload, dict):
                # If the dict wraps the actual list of members under a known key, unwrap it
                inner = payload.get("members") if "members" in payload else None
                self.log(f"inner: {inner}")
                if isinstance(inner, list):
                    self.members = inner
                    self.log(f"members after extraction: {type(self.members)} len={len(self.members)}")
                else:
                    self.members = [payload]
                    self.log(f"Members after extraction: {type(self.members)} len={len(self.members)}")
            else:
                # Unknown shape; keep default empty element and log
                self.log(f"Unexpected payload type: {type(payload)}")
        if self.members is not None:
            self.log(f"payload: {payload}, type: {type(payload)}, length: {len(payload)}")
            self.members = payload
        else:
            self.members = ["There are no members for this collection"]
        self.log(f"Members after extraction: {type(self.members)} len={len(self.members)}")
        self.log(f"Members: type: {type(self.members)}, {len(self.members)}")

        # set up the data table

        ROWS = [
            ("Qualified Name"),
        ]

        self.member_datatable: DataTable = DataTable()
        # Configure the DataTable - member_datatable
        self.member_datatable.id = "member_datatable"
        # Add columns to the DataTable
        self.member_datatable.add_columns(*MembersScreen.ROWS[0])
        # set the cursor to row instead of cell
        self.member_datatable.cursor_type = "row"
        # give the DataTable zebra stripes so it is easier to follow across rows on the screen
        self.member_datatable.zebra_stripes = True
        # Check that we have at least one Data Product Catalogue
        if self.members is None or "There are no members for this collection" in self.members:
            # No Data Product Catalogues found
            # self.log("No Data Product Catalogues found")
            self.member_datatable.add_row("Error, No Data Product Catalogues found")
        elif type(self.members) is list and "There are no members for this collection" in self.members:
            # No members found for the collection
            self.member_datatable.add_row("Error, No members found for this collection")
        else:
            # Load data into the DataTable
            try:
                for entry in self.members:
                    qualified_name = entry.get("Qualified Name", "None")
                    self.member_datatable.add_row(
                        # entry.get("Qualified Name", "None"),
                        # entry["Qualified Name"],
                        qualified_name,
                    )
                    # self.log(f"DataTable row added with: {entry['Qualified Name']}")
            except Exception as e:
                self.member_datatable.add_row("Error", "Error updating member list", str(e))
                # self.log(f"Error updating member list: {str(e)}")

        # self.log(f"Refreshing DataTable")
        try:
            collection_mounted = self.query_one("#collection_datatable")
            if collection_mounted:
                self.collection_datatable.remove()
            widget_to_mount = self.query_one("#member_datatable")
            if not widget_to_mount:
                self.mount(self.member_datatable, after="after_static")
            self.member_datatable.refresh(layout=True, recompose=True)
        except (NoMatches):
            self.mount(self.member_datatable, after="#after_static")
        # self.log(f"DataTable Refreshed")

    @on(DataTable.RowSelected, "#member_datatable")
    def handle_member_table_row_selected(self, message: DataTable.RowSelected):
        """ Retrieve members of a collection """
        self.selected_row = message.row_key
        self.selected_data = self.member_datatable.get_row(message.row_key)
        self.selected_name = self.row_selected_data[0] or ""
        self.selected_qname = self.row_selected_data[1] or ""
        self.selected_type = self.row_selected_data[2] or ""
        self.selected_desc = self.row_selected_data[3] or ""
        # qname = self.selected_qname.split(']')[1].strip('[')
        # self.selected_qualified_name = qname

        # Retrieve selected Member
        response = exec_format_set(
            format_set_name="Digital-Products-MyE",
            params={"search_string": self.selected_qname},
            output_format="DICT",
            view_server=self.view_server,
            view_url=self.platform_url,
            user=self.user,
            user_pass=self.password,
        )
        self.log(f"response: {response}")

        # Robustly extract data payload from response["data"]. Then populate self.members.
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
            self.log(f"No parsable data found in response from Egeria{response['data']}")
        else:
            # Ensure self.members becomes a list of dicts for downstream UI
            if isinstance(payload, list):
                self.members = payload
                self.log(f"members after extraction: {type(self.members)} len={len(self.members)}")
            elif isinstance(payload, dict):
                # If the dict wraps the actual list of members under a known key, unwrap it
                inner = payload.get("members") if "members" in payload else None
                self.log(f"inner: {inner}")
                if isinstance(inner, list):
                    self.members = inner
                    self.log(f"members after extraction: {type(self.members)} len={len(self.members)}")
                else:
                    self.members = [payload]
                    self.log(f"collections after extraction: {type(self.members)} len={len(self.members)}")
            else:
                # Unknown shape; keep default empty element and log
                self.log(f"Unexpected payload type: {type(payload)}")
        self.members = payload
        self.log(f"Members after extraction: {type(self.members)} len={len(self.members)}")
        # If the member has members carry on drilling down to leaf level -
        # Create an instance of the Members Screen and pass it the data retrieved from Egeria
        # and push it to the top of screen stack to display
        if self.members is not None:
            self.process_members()
        #     ms_instance = MembersScreen(self.members)
        #     self.push_screen(ms_instance)
        else:
            self.display_member_details(self.selected_row)

    def display_member_details(self, selected_row):
        """ Request to display the details for a selected record """
            # gather details returned from egeria
        self.selected_row = selected_row
        member_details = self.get_member_details(self.selected_row)

        inner_dn = inner_qn = inner_c = inner_d = inner_s = inner_tn = ""
        inner_cm = ""
        if member_details is None:
            # no input provided, set to empty list
            member_details = []
        elif isinstance(member_details, list):
            # input is list
            self.log(f"Member Details input is a list: {member_details}")
        elif isinstance(member_details, dict):
            # input is dict
            self.log(f"Member Details input is a dict: {member_details}")
            inner_dn = member_details.get("Display Name") if "Display Name" in member_details else None
            inner_qn = member_details.get("Qualified Name") if "Qualified Name" in member_details else None
            inner_c = member_details.get("Categories") if "Categories" in member_details else None
            inner_d = member_details.get("Description") if "Description" in member_details else None
            inner_s = member_details.get("Status") if "Status" in member_details else None
            inner_tn = member_details.get("Type Name") if "Type Name" in member_details else None
            inner_cm = member_details.get("Containing Members") if "Containing Members" in member_details else None
            if isinstance(inner_cm, list):
                self.containing_members = inner_cm
                self.log(
                    f"members after extraction: {type(self.containing_members)} len={len(self.containing_members)}")
            else:
                self.containing_members = None
        else:
            # Unknown shape of input to member details screen, setting to emply list
            self.log(f"Member Details input is not a list or dict: {member_details}")
            member_details = []
        # self.log(f"Member Details Screen init started with data: {member_details}")
        self.member_details_datatable: DataTable = DataTable()
        # confire the DataTable - member_datatable
        self.member_details_datatable.id = "member_datatable"
        # Add columns to the DataTable
        self.member_details_datatable.add_columns(*MemberDetailsScreen.ROWS[0])
        # set the cursor to row instead of cell
        self.member_details_datatable.cursor_type = "row"
        # give the DataTable zebra stripes so it is easier to follow across rows on the screen
        self.member_details_datatable.zebra_stripes = True
        # log the results of configuring the DataTable
        # self.log(f"Member Details DataTable Created:")
        # self.log(f"Member Details DataTable: {self.member_details_datatable.columns}")
        # Check that we have at least one Data Product Catalogue
        if member_details is None:
            # No Data Product Catalogues found
            # self.log("No Data Product Catalogues found")
            self.member_details_datatable.add_row("Error, No Data Product Catalogues found")
        elif type(member_details) is list and len(member_details) == 0:
            self.member_details_datatable.add_row("Error, No Data Product Catalogues found")
        else:
            # Load data into the DataTable
            try:
                for entry in member_details:
                    self.member_details_datatable.add_row(
                        inner_dn,
                        inner_qn,
                        inner_c,
                        inner_d,
                        inner_s,
                        inner_tn,
                        self.containing_members
                    )
            except Exception as e:
                self.member_details_datatable.add_row("Error", "Error updating member list", str(e))

        self.member_details_datatable.refresh(layout=True, recompose=True)


    def process_members(self):
        """ Process the members of a collection """
        self.log(f"Processing members of collection: {self.selected_name}")
        self.log(f"Selected qualified name: {self.selected_qualified_name}")
        try:
            self.member_datatable = self.query_one("#member_datatable").remove()
            self.member_datatable: DataTable = DataTable()
        except(NoMatches):
            self.log(f"No DataTable found")
            self.member_datatable: DataTable = DataTable()
        # Configure the DataTable - member_datatable
        self.member_datatable.id = "member_datatable"
        # Add columns to the DataTable
        self.member_datatable.add_columns(*MembersScreen.ROWS[0])
        # set the cursor to row instead of cell
        self.member_datatable.cursor_type = "row"
        # give the DataTable zebra stripes so it is easier to follow across rows on the screen
        self.member_datatable.zebra_stripes = True
        # Check that we have at least one Data Product Catalogue
        if self.members is None or "There are no members for this collection" in self.members:
            # No Data Product Catalogues found
            # self.log("No Data Product Catalogues found")
            self.member_datatable.add_row("Error, No Data Product Catalogues found")
        elif type(self.members) is list and "There are no members for this collection" in self.members:
            # No members found for the collection
            self.member_datatable.add_row("Error, No members found for this collection")
        else:
            # Load data into the DataTable
            try:
                for entry in self.members:
                    self.member_datatable.add_row(
                        # entry.get("Qualified Name", "None"),
                        entry["Qualified Name"],
                    )
                    # self.log(f"DataTable row added with: {entry['Qualified Name']}")
            except Exception as e:
                self.member_datatable.add_row("Error", "Error updating member list", str(e))
                # self.log(f"Error updating member list: {str(e)}")
        try:
            collection_mounted = self.query_one("#collection_datatable")
            if collection_mounted:
                self.collection_datatable.remove()
            widget_to_mount = self.query_one("#member_datatable")
            if not widget_to_mount:
                self.mount(self.member_datatable, after="#after_static")
            self.member_datatable.refresh(layout=True, recompose=True)
        except (NoMatches):
            self.mount(self.member_datatable, after="#after_static")

    def get_member_details(self, selected_row) -> list:
        """ Retrieve members of a collection """
        self.selected_row = selected_row
        self.selected_qualified_name = self.selected_row.get("QName")

        # Retrieve selected Member
        response = exec_format_set(
            format_set_name="Digital-Products-MyE",
            params={"search_string": self.selected_qualified_name},
            output_format="DICT",
            view_server=self.view_server,
            view_url=self.platform_url,
            user=self.user,
            user_pass=self.password,
        )
        self.log(f"response: {response}")

        # Robustly extract data payload from response["data"]. Then populate self.members.
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
            self.log(f"No parsable data found in response from Egeria{response['data']}")

        return payload

    async def action_back(self) -> None:
    #     """ Return to the Display Available Catalogs display """
        self.log(f"Back requested")
        self.on_splash_screen_splash_continue()


if __name__ == "__main__":
    app = DataProducts()
    os.environ.setdefault("EGERIA_PLATFORM_URL", "https://127.0.0.1:9443")
    os.environ.setdefault("EGERIA_VIEW_SERVER", "qs-view-server")
    os.environ.setdefault("EGERIA_USER", "erinoverview")
    os.environ.setdefault("EGERIA_USER_PASSWORD", "secret")
    app.run()