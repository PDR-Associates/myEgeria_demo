""" python

   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a utility function for my_egeria.


"""
from typing import Type
from xml.etree.ElementTree import QName

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Static, Button, DataTable, Header, Footer
from demo_service import get_config


class MembersScreen(Screen):
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


    class MemberSelected(Message):
        def __init__(self, selected_data: dict):
            super().__init__()
            self.selected_data = selected_data


    def __init__(self, members: list[dict] = None):
        super().__init__()
        self.members = members
        self.log(f"Data Product Screen init started with data: {members}")
        self.member_datatable: DataTable = DataTable()
        # confire the DataTable - member_datatable
        self.member_datatable.id = "member_datatable"
        # Add columns to the DataTable
        self.member_datatable.add_columns(*MembersScreen.ROWS[0])
        # set the cursor to row instead of cell
        self.member_datatable.cursor_type = "row"
        # give the DataTable zebra stripes so it is easier to follow across rows on the screen
        self.member_datatable.zebra_stripes = True
        # log the results of configuring the DataTable
        self.log(f"Collection DataTable Created:")
        self.log(f"Collection DataTable: {self.member_datatable.columns}")
        # Check that we have at least one Data Product Catalogue
        if self.members is None:
            # No Data Product Catalogues found
            self.log("No Data Product Catalogues found")
            self.member_datatable.add_row("Error", "No Data Product Catalogues found")
        else:
            # Load data into the DataTable
            try:
                for entry in self.members:
                    self.member_datatable.add_row(
                        # entry.get("GUID", "None"),
                        entry.get("Display Name", "None"),
                        entry.get("Qualified Name", "None"),
                        entry.get("Type Name", "None"),
                        entry.get("Description", "None"),
                    )
                    self.log(f"DataTable row added with: {entry.get('Display Name', '')}, {entry.get('=Qualified Name', '')}, {entry.get('Type Name', '')}, {entry.get('Description', '')}")
            except Exception as e:
                self.member_datatable.add_row("Error", "Error updating collection list", str(e))
                self.log(f"Error updating collection list: {str(e)}")
        cfg = get_config()
        self.view_server = cfg[1]
        self.platform_url = cfg[0]
        self.user = cfg[2]
        self.password = cfg[3]
        self.log(f"Refreshing DataTable")
        self.member_datatable.refresh(layout=True, recompose=True)
        self.log(f"DataTable Refreshed")

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
                self.member_datatable,
                Static("\n\nEnd of DataTable", id="after_static"),
            ),
            id="main_content")
        yield Container(
            Button("Quit", id="quit"),
            id="action_row",
        )
        yield Footer()
        self.log("done yielding, now waiting for user input")

    async def on_member_datatable_row_selected(self, event: DataTable.RowSelected):
        self.log(f"Row Selected, Processing selection")
        self.member_datatable = self.query_one("#member_datatable", DataTable)
        self_row_selected = self.member_datatable.get_row(event.row_key)
        self.selected_guid = self_row_selected[0] or ""
        self.selected_name = self_row_selected[1] or ""
        self.selected_qname = self_row_selected[2] or ""
        self.selected_type = self_row_selected[3] or ""
        self.selected_desc = self_row_selected[4] or ""
        self.log(f"Selected Data Product: {self.selected_name}")
        self.selected_data = {"GUID":self.selected_guid,
                              "Name":self.selected_name,
                              "QName":self.selected_qname,
                              "Type":self.selected_type,
                              "Desc":self.selected_desc}
        self.log(f"Posting Row Selected Message for App, Data: {self.selected_data}")
        self.post_message(self.MemberSelected(self.selected_data))

    @on(Button.Pressed, "#quit")
    async def quit(self) -> None:
        """Signal the application to Quit gracefully """
        self.post_message(self.QuitRequested())

    def action_quit(self):
        """Signal the application to Quit gracefully """
        self.post_message(self.QuitRequested())


