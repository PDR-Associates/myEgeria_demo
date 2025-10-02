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
from textual.widget import Widget
from textual.widgets import Static, Button, DataTable, Header, Footer


class DataProductScreen(Screen):
    """Main menu for the Data Product functions of my_egeria"""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
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
        ("GUID", "Display Name", "Qualified Name", "Type Name", "Description"),
        ]


    class QuitRequested(Message):
        """ Message to terminate application gracefully """
        def __init__(self):
            super().__init__()


    def __init__(self, collections: list[dict]):
        super().__init__()
        self.collections = collections
        # self.CollectionTable = self.app.CollectionTable(self.collections)
        """A DataTable to display the list of Data Product Catalogs """
        app: "DataProducts"
        self.collection_datatable: DataTable = DataTable()
        """Configure the DataTable and load data into it"""
        # confire the DataTable - collection_datatable
        self.collection_datatable.id = "collection_datatable"
        # Add columns to the DataTable
        self.collection_datatable.add_columns(*DataProductScreen.ROWS[0])
        # set the cursor to row instead of cell
        self.collection_datatable.cursor_type = "row"
        # give the DataTable zebra stripes so it is easier to follow across rows on the screen
        self.collection_datatable.zebra_stripes = True
        # log the results of configuring the DataTable
        self.log(f"Collection List Created:")
        self.log(f"Collection List: {self.collection_datatable.columns}")
        # Load data into the DataTable
        try:
            for entry in self.collections:
                self.collection_datatable.add_row(
                    entry.get("GUID"),
                    entry.get("displayName"),
                    entry.get("qualifiedName"),
                    entry.get("description"),
                )
        except Exception as e:
            self.collection_datatable.add_row("Error", str(e))
            self.log(f"Error updating collection list: {str(e)}")
            self.collection_datatable.add_row("Error updating collection list", str(e))
        self.Egeria_config = ["https://127.0.0.1:9443", "qs-view-server", "erinoverview", "secret"]

    def compose(self) -> ComposeResult:

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
                DataTable(id="collection_datatable"),
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

    async def on_collection_datatable_row_selected(self, event: DataTable.RowSelected):
        self.collection_datatable = self.query_one("#collection_datatable", DataTable)
        self_row_selected = self.collection_datatable.get_row(event.row_key)
        self.selected_guid = self_row_selected[0] or ""
        self.selected_name = self_row_selected[1] or ""
        self.selected_qname = self_row_selected[2] or ""
        self.selected_desc = self_row_selected[3] or ""
        self.log(f"Selected Data Product: {self.selected_name}")

    @on(Button.Pressed, "#quit")
    async def quit(self) -> None:
        """Signal the application to Quit gracefully """
        self.post_message(self.QuitRequested())

    def action_quit(self):
        """Signal the application to Quit gracefully """
        self.post_message(self.QuitRequested())


