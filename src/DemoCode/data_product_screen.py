""" python

   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a utility function for my_egeria.


"""
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Static, Button, DataTable

from utils.config import EgeriaConfig
from demo_service import DemoService


class DataProductScreen(Screen):
    """Main menu for the Data Product functions of my_egeria"""

    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("q", "back", "Back"),
        ("escape", "back", "Back"),
    ]

    class QuitRequested(Message):
        """ Message to terminate application gracefully """
        def __init__(self):
            super().__init__()

    def __init__(self, config: EgeriaConfig):
        super().__init__()
        self.config = config

    def on_mount(self) -> None:
        """ Call find collections service to create Data Product table"""
        self.dataproductlist: dict = DemoService()._find_collections()
        self.collection_list: DataTable = DataTable(id = "collection_list")
        self.collection_list.add_columns("Data Product Name", "GUID", "Type Name")
        if not self.dataproductlist:
            self.collection_list.add_row("No Data Products Found", "", "")
            return
        else:
            for entry in self.dataproductlist:
                self.collection_list.add_row(entry.get("name"), entry.get("guid"), entry.get("typeName"))
                return


    def compose(self) -> ComposeResult:
        yield Container(
            Static("MyEgeria", id="title"),
            Static("Data Products", id="main_menu"),
            id = "title_row",
        )
        yield ScrollableContainer(
            Static(f"AvailableData Product Marketplaces:"),
            DataTable(id="#collection_list"),
            id="main_content")
        yield Container(
            Button("Quit", id="quit"),
            id="action_row",
        )

    def on_collection_list_row_selected(self, event: DataTable.RowSelected):
        self_row_selected = self.collection_list.get_row(event.row_key)
        self.selected_guid = self_row_selected[1] or ""
        self.selected_name = self_row_selected[0] or ""
        self.selected_type = self_row_selected[2] or ""

    @on(Button.Pressed, "#quit")
    async def quit(self) -> None:
        """Signal the application to Quit gracefully """
        self.post_message(self.QuitRequested())