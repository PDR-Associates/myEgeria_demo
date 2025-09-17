""" python

   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a utility function for my_egeria.


"""
import json

from textual import on, log
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Static, Button, DataTable, Header, Footer
from pyegeria import CollectionManager


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

    class QuitRequested(Message):
        """ Message to terminate application gracefully """
        def __init__(self):
            super().__init__()

    # class TableCreated(Message):
    #     def __init__(self, table: DataTable):
    #         super().__init__()
    #         self.table = table

    class EgeriaDataReceived(Message):
        def __init__(self, data: list):
            super().__init__()
            self.data = data

    def __init__(self):
        self.Egeria_config = ["https://127.0.0.1:9443", "qs-view-server", "erinoverview", "secret"]
        self.collections: list = []
        super().__init__()

    async def on_mount(self) -> None:
        """on_mount, this function is called when the widget is mounted to the DOM
            """
        # self.create_data_table()
        # collection_list: DataTable = DataTable(id="collection_list")
        # collection_list = self.query_one("collection_list", DataTable)
        self.collection_list: DataTable = self.query_one(DataTable)
        self.collection_list.id = "collection_list"
        #     # Add columns to the DataTable
        self.collection_list.add_columns(*DataProductScreen.ROWS[0])
        self.collection_list.cursor_type="row"
        self.collection_list.zebra_stripes=True
        self.log(f"Collection List Created: {self.collection_list}")
        self.log(f"Collection List: {self.collection_list.columns}")
        target = self.query_one("#before_static", Static)
        await self.mount(self.collection_list, after=target)
        self.log(
            f"Collection List mounted: {self.collection_list}"
        )
        await self.Collection_Datatable(self.collection_list)
        self.log("Collection List mounted, but code returned after Collection_DataTable")
        return

    async def Collection_Datatable(self, collection_list: DataTable) -> Widget:
        """Collection_Datatable, this function creates the data table for the collections
            """

        # Create a list containing the Egeria configuration settings
        self.collection_list: DataTable = collection_list
        try:
            self.log(f"Collection List, type: {type(collection_list)}")
            self.log(f"self.collection_list type: {type(self.collection_list)}")
            self.collections = await self.get_collections_from_egeria(
                Egeria_config=self.Egeria_config,
                Search_str="*"
            )
            self.log(f"Collections retrieved from Egeria: {self.collections}")
            if self.collections is None:
                self.collections = [{ "GUID": "Egeria Error", "displayName": "Egeria Error", "qualifiedName": "Egeria Error", "description": "Egeria Error"}]
                self.log("Collections from Egeria is None")
                # return collection_list
            # self.collections.append({"GUID":"meow","displayName":"meow","qualifiedName":"meow","description":"meow"})
            self.log(f"Collections: {json.dumps(self.collections[0])}")
            self.log(f"{type(collection_list)}, {collection_list is None}")
            try:
                collection_list.clear(columns=False)
                for entry in self.collections:
                    collection_list.add_row(
                            entry.get("GUID"),
                            entry.get("displayName"),
                            entry.get("qualifiedName"),
                            entry.get("description"),
                    )
            except Exception as e:
                collection_list.add_row("Error", str(e))
                log(f"Error updating collection list: {str(e)}")
                collection_list.add_row("Error updating collection list", str(e))
            # await self.update_collection_list(collections)
        except Exception as e:
            self.log(f"Error fetching collections: {str(e)}")
            collection_list.add_row("Error fetching collections", str(e))
        return collection_list

    # def create_data_table(self):
    #     # Create a textual DataTable to hold the data received from Egeria
    #     self.collection_list: DataTable = DataTable(id="collection_list")
    #     # Add columns to the DataTable
    #     self.collection_list.add_columns("GUID", "Display Name", "Qualified Name", "Description")
    #     self.collection_list.cursor_type(row=True)
    #     self.collection_list.zebra_stripes=True
    #     # return self.collection_list

    async def get_collections_from_egeria(self, Egeria_config: list, Search_str: str) -> list:
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
            c_client = CollectionManager(self.view_server, self.platform_url, user_id=self.user,)
            c_client.create_egeria_bearer_token(self.user, self.password)
            response = c_client.find_collections(search=Search_str, output_format="DICT")
            # Close the Egeria Client to save resources
            c_client.close_session()
            for entry in response:
                qualified_name = entry.get("qualifiedName", "")
                # if "DigProdCatalog" in qualified_name:
                self.collections.append(entry)
        except Exception as e:
            self.log(f"Error connecting to Egeria: {str(e)}")
            self.collections.append(f"Egeria Error: {str(e)}")
        # self.post_message(self.EgeriaDataReceived(self.collections))
        return self.collections

    async def update_collection_list(self, collections: list):
        collection_list = self.query_one("#collection_list", DataTable)
        try:
            self.collections = collections
            collection_list.clear(columns=False)
            for entry in collections:
                collection_list.add_row(
                     entry.get("GUID"),
                     entry.get("displayName"),
                     entry.get("qualifiedName"),
                     entry.get("description"),
                )
        except Exception as e:
            collection_list.add_row("Error in update_collection_list", str(e))
            log(f"Error updating collection list: {str(e)}")
        finally:
            return collection_list

    def compose(self) -> ComposeResult:
        try:
            self.collection_list = self.query_one("#collection_list", DataTable)
            self.log(f"Collection List: {self.collection_list} in compose")
        except Exception as e:
            self.collection_list: DataTable = DataTable(id="collection_list")
            self.collection_list.add_columns("GUID", "Display Name", "Qualified Name", "Description")
            self.collection_list.add_row("Data Table not created")
            self.log(f"Collection List: {self.collection_list} dummied in compose")
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
                DataTable(),
                # DataTable(id="collection_list", name="collection_list"),
                Static("End of DataTable", id="after_static"),
                # self.Collection_Datatable(),
            ),
            id="main_content")
        self.log("Yielded a DataTable")
        yield Container(
            Button("Quit", id="quit"),
            Footer(),
            id="action_row",
        )
        # yield Footer()
        self.log("done yielding")

    async def on_collection_list_row_selected(self, event: DataTable.RowSelected):
        self.collection_list = self.query_one("#collection_list", DataTable)
        self_row_selected = self.collection_list.get_row(event.row_key)
        self.selected_guid = self_row_selected[0] or ""
        self.selected_name = self_row_selected[1] or ""
        self.selected_qname = self_row_selected[2] or ""
        self.selected_desc = self_row_selected[3] or ""
        self.log(f"Selected Data Product: {self.selected_name}")
        self.coll =  await self.get_collections_from_egeria(Egeria_config=self.Egeria_config, Search_str = self.selected_guid)
        self.collections=self.coll
        await self.update_collection_list()

    def on_egeria_data_received(self, event: EgeriaDataReceived):
        self.collections = event.data
        self.update_collection_list(self.collections)

    # def on_table_created(self, event: TableCreated):
    #     self.collection_list = event.table
    #     return self.collection_list

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

