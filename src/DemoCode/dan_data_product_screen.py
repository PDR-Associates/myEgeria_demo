""" python

   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a utility function for my_egeria.


"""
import json

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Static, Button, DataTable, Header, Footer

class DataProductScreen(Screen):
    """Main menu for the Data Product functions of my_egeria"""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ]

    CSS = """
    .connection_info {
        background: $panel;
        color: $text;
        border: round $primary;
        height: 1fr;
        width: 1fr;
    }
    .title_row {
        background: $panel;
        color: $text;
        border: round $primary;
        height: 1fr;
        width: 1fr;
        align: center middle;
    }
    .main_content {
        background: $panel;
        color: $text;
        border: round $primary;
        height: 10fr;
        width: 1fr;
    }
    .action_row {
        background: $panel;
        color: $text;
        border: round $primary;
        height: 2fr;
        width: 1fr;
    }
    #title {
        align: center middle;
    }
    #main_menu {
        align: center middle;
    }       
    """

    ROWS = [
        ("GUID", "Display Name", "Qualified Name", "Description"),
        ]
    app = "DataProducts"


    class CollectionTable(Widget):


        def __init__(self, collection: list):
            self.collections = collection
            super().__init__()

        def on_mount(self):
            # set up the DataTable to display the collections from Egeria
            try:
                # exists already so clear it
                # self.collection_list.clear()
                self.collection_list
            except AttributeError:
                # doesnt exist already so create the DataTable
                self.collection_list: DataTable = DataTable(id="collection_list")


            # configure the DataTable - collection_list
            # self.collection_list.id = "collection_list"
            # Add columns to the DataTable
            self.collection_list.add_columns(*DataProductScreen.ROWS[0])
            # set the cursor to row instead of cell
            self.collection_list.cursor_type = "row"
            # give the DataTable zebra stripes so it is easier to follow across rows on the screen
            self.collection_list.zebra_stripes = True
            # log the results of configuring the DataTable
            self.log(f"Collection List Created: {self.collection_list}")
            self.log(f"Collection List: {self.collection_list.columns}")
            # Load data into the DataTable
            try:
                for entry in self.collections:
                    self.collection_list.add_row(
                        entry.get("GUID"),
                        entry.get("displayName"),
                        entry.get("qualifiedName"),
                        entry.get("description"),
                    )
            except Exception as e:
                self.collection_list.add_row("Error", str(e))
                self.log(f"Error updating collection list: {str(e)}")
                self.collection_list.add_row("Error updating collection list", str(e))

        # def render(self):
        #     content = self.query_one("#main_content")
        #     return content

        def load_data(self):
            """ Load the data from Egeria """
            # Access Egeria and Create list of dicts to pass to Screen
            try:
                self.log(f"Collection List, type: {type(self.collection_list)}")
                self.log(f"self.collection_list type: {type(self.collection_list)}")

                if self.collections is None:
                    self.collections = [
                        {"GUID": "Egeria Error", "displayName": "Egeria Error", "qualifiedName": "Egeria Error",
                         "description": "Egeria Error"}]
                    self.log("Collections from Egeria is None")
                self.log(f"Collections: {json.dumps(self.collections[0])}")
                self.log(f"{type(self.collection_list)}, {self.collection_list is None}")
                return self.collections
            except Exception as e:
                self.log(f"Error fetching collections: {str(e)}")
                self.collections = [{"Error fetching collections": str(e)}]
            return self.collections
            

    class QuitRequested(Message):
        """ Message to terminate application gracefully """
        def __init__(self):
            super().__init__()

    class EgeriaDataReceived(Message):
        def __init__(self, data: list):
            super().__init__()
            self.data = data

    class GetMembers(Message):
        def __init__(self, qname: str):
            super().__init__()
            self.qname = qname

    def __init__(self, message: list = None):
        self.Egeria_config = ["https://127.0.0.1:9443", "qs-view-server", "erinoverview", "secret"]
        self.collections: list = message
        super().__init__()

    def compose(self) -> ComposeResult:
        # collection_list: reactive = reactive(DataTable())
        # collection_list.id = "collection_list"
        # self.collection_list = self.query_one("#collection_list", DataTable)
        yield Header(show_clock=True)
        yield Container(
            Static(
                f"Server: {self.Egeria_config[1]} | Platform: {self.Egeria_config[0]} | User: {self.Egeria_config[2]}",
                id="connection_info",
            )
        )
        self.log("Yielded a message")
        yield Container(
            Static("MyEgeria", id="title"),
            Static("Data Products", id="main_menu"),
            id = "title_row",
        )
        self.log("Yielded another message")
        yield ScrollableContainer(
            Vertical(
                Static(f"Available Data Product Marketplaces:", id="before_static"),
                self.CollectionTable(self.collections),
                Static("End of DataTable", id="after_static"),
            ),
            id="main_content")
        self.log("Yielded a DataTable")
        yield Container(
            Button("Quit", id="quit"),
            # Footer(),
            id="action_row",
        )
        yield Footer()
        self.log("done yielding")

    async def on_collection_list_row_selected(self, event: DataTable.RowSelected):
        self.collection_list = self.query_one("#collection_list", DataTable)
        self_row_selected = self.collection_list.get_row(event.row_key)
        self.selected_guid = self_row_selected[0] or ""
        self.selected_name = self_row_selected[1] or ""
        self.selected_qname = self_row_selected[2] or ""
        self.selected_desc = self_row_selected[3] or ""
        self.log(f"Selected Data Product: {self.selected_name}")
        self.post_message(self.GetMembers(self.selected_qname))

    @on(Button.Pressed, "#quit")
    async def quit(self) -> None:
        """Signal the application to Quit gracefully """
        self.post_message(self.QuitRequested())

    def action_quit(self):
        """Signal the application to Quit gracefully """
        self.post_message(self.QuitRequested())

    def action_refresh(self):
        """Signal the application to refresh the screen """
        self.post_message(self.EgeriaDataReceived(self.collections))

