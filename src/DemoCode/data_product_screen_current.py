""" python

   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a utility function for my_egeria.


"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Static, Button, DataTable, Header, Footer
from demo_service import get_config


class DataProductScreen(Screen):
    """Main menu for the Data Product functions of my_egeria"""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
        ]

    CSS_PATH = ["data_products_css.tcss"]

    ROWS = [
        ("GUID", "Display Name", "Qualified Name", "Type Name", "Description"),
        ]

    app = "DataProducts"

    class QuitRequested(Message):
        """ Message to terminate application gracefully """
        def __init__(self):
            super().__init__()


    class CatalogSelected(Message):
        def __init__(self, selected_data: dict):
            super().__init__()
            self.selected_data = selected_data


    def __init__(self, collections, **kwargs):
        super().__init__(**kwargs)
        self.collections = collections
        # self.log(f"Data Product Screen init started with data: {collections}")
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
        cfg = get_config()
        self.view_server = cfg[1]
        self.platform_url = cfg[0]
        self.user = cfg[2]
        self.password = cfg[3]
        self.collection_datatable.refresh(layout=True, recompose=True)

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
                self.collection_datatable,
                Static("\n\nEnd of DataTable", id="after_static"),
            ),
            id="main_content")
        yield Container(
            Button("Quit", id="quit"),
            id="action_row",
        )
        yield Footer()
        self.log("done yielding, now waiting for user input")

    async def on_data_table_row_selected(self, event: DataTable.RowSelected):
        self.log(f"Row Selected, Processing selection")
        self.collection_datatable = self.query_one("#collection_datatable", DataTable)
        self_row_selected = self.collection_datatable.get_row(event.row_key)
        self.selected_name = self_row_selected[0] or ""
        self.selected_qname = self_row_selected[1] or ""
        self.selected_type = self_row_selected[2] or ""
        self.selected_desc = self_row_selected[3] or ""
        qname = self.selected_qname.split(']')[0].strip('[')
        self.selected_qname = qname

        self.log(f"Selected Data Product: {self.selected_name}, qname: {self.selected_qname}, type: {self.selected_type}, desc: {self.selected_desc}")
        self.selected_data = {
                              "Name":self.selected_name,
                              "QName":self.selected_qname,
                              "Type":self.selected_type,
                              "Desc":self.selected_desc}
        self.log(f"Posting Row Selected Message for App, Data: {self.selected_data}")
        self.post_message(self.CatalogSelected(self.selected_data))

    @on(Button.Pressed, "#quit")
    async def quit(self) -> None:
        """Signal the application to Quit gracefully """
        self.post_message(self.QuitRequested())

    def action_quit(self):
        """Signal the application to Quit gracefully """
        self.post_message(self.QuitRequested())


