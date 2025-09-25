""" python

   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a utility function for my_egeria.


"""
from textual import on, log
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.message import Message
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Static, Button, DataTable, Header, Footer
from pyegeria import EgeriaTech, CollectionManager


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

    class QuitRequested(Message):
        """ Message to terminate application gracefully """
        from textual import log
        def __init__(self):
            super().__init__()
            self.log(f"Quit Requested, message class")
            self.collection_list = DataTable(id="collection_list")



    class TableCreated(Message):
        from textual import log
        def __init__(self, table: DataTable):
            super().__init__()
            self.log(f"Table Created Message Class")
            self.table = table

    class EgeriaDataReceived(Message):
        from textual import log
        def __init__(self, data: list):
            super().__init__()
            self.log(f"Egeria Data Received Message Class")
            self.data = data

    def __init__(self):
        self.Egeria_config = ["https://127.0.0.1:9443", "qs-view-server", "erinoverview", "secret"]
        self.collections: list = []
        super().__init__()

    async def on_mount(self) -> None:
        """on_mount, this function is called when the widget is mounted to the DOM
            """
    #     self.Collection_Datatable()
    #
    # def Collection_Datatable(self) -> None:
    #     """Collection_Datatable, this function creates the data table for the collections
    #         """
        platform_url= "https://127.0.0.1:9443"
        view_server = "qs-view-server"
        user = "erinoverview"
        password = "secret"
        # Create a list containing the Egeria configuration settings
        Egeria_config: list = [platform_url,
                               view_server,
                               user,
                               password,
                               ]
        # Create a textual DataTable to hold the data received from Egeria
        self.collection_list: DataTable = DataTable(id="collection_list")
        # Add columns to the DataTable
        self.collection_list.add_columns("GUID", "Display Name", "Qualified Name", "Description")
        # Set up the Egeria Client
        self.log(f"Connecting to Egeria using: , {Egeria_config}")
        self.collection_list.add_row("meow", "meow", "meow", "meow")
        self.collection_list.add_row("woof", "woof", "woof", "woof")
        self.log(f"Collection List Created: {self.collection_list}")
        self.log(f"Collection List: {self.collection_list.columns}")
        self.post_message(self.TableCreated(self.collection_list))
        # self.get_collections_from_egeria(Egeria_config=Egeria_config, Search_str = "*")
        # self.log(f"Update the DataTable")
        # self.post_message(self.TableCreated(self.collection_list, collections))

    # async def get_collections_from_egeria(self, Egeria_config: list, Search_str: str) -> None:
    #     self.log(f"Creating client and Connecting to Egeria using: , {Egeria_config}")
    #     self.platform_url = Egeria_config[0]
    #     self.view_server = Egeria_config[1]
    #     self.user = Egeria_config[2]
    #     self.password = Egeria_config[3]
    #     self.log(f"Connecting to Egeria using: , {self.platform_url}")
    #     self.log(f"Connecting to Egeria using: , {self.view_server}")
    #     self.log(f"Connecting to Egeria using: , {self.user}")
    #     self.log(f"Connecting to Egeria using: , {self.password}")
    #     try:
    #         c_client = CollectionManager(self.view_server, self.platform_url, user_id=self.user,)
    #         c_client.create_egeria_bearer_token(self.user, self.password)
    #         response: list = await c_client._async_find_collections(search=Search_str, output_format="DICT")
    #         # Close the Egeria Client to save resources
    #         c_client.close_session()
    #         self.collections: list = [{"":""},]
    #         for entry in response:
    #             # if "DigProdCatalog" in entry["properties"]["qualifiedName"]:
    #             self.collections[entry] = entry
    #             # else:
    #             #     continue
    #     except Exception as e:
    #         self.log(f"Error connecting to Egeria: {str(e)}")
    #         self.collections:list = [{"Egeria Error": str(e)}]
    #     self.post_message(self.EgeriaDataReceived(self.collections))

    def update_collection_list(self, collections: list):
        collection_list: DataTable = DataTable(id="collection_list")
        try:
            self.collections = collections
            collection_list.clear(columns=False)
            for entry in self.collections:
                collection_list.add_row(
                    (
                     entry.get("GUID"),
                     entry.get("displayName"),
                     entry.get("qualifiedName"),
                     entry.get("description"),
                    )
                )
                self.log(f"In update_collection_list added row with values: {entry.get('GUID')} | {entry.get('displayName')} | {entry.get('qualifiedName')} | {entry.get('description')}")
        except Exception as e:
            collection_list.add_row("Error", str(e))
            log(f"Error updating collection list: {str(e)}")
        return collection_list

    def compose(self) -> ComposeResult:

        self.view_server = "qs-view-server"
        self.platform_url = "https://127.0.0.1:9443"
        self.user = "erinoverview"
        self.log(f"Displaying content using: , {self.platform_url}")

        yield Header(show_clock=True)
        yield Container(
            Static(
                f"Server: {self.view_server} | Platform: {self.platform_url} | User: {self.user}",
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
            Static(f"Available Data Product Marketplaces:"),
            # DataTable(id="collection_list"),
            # self.Collection_Datatable(),
            id="main_content")
        self.log("Yielded a DataTable")
        yield Container(
            Button("Quit", id="quit"),

            id="action_row"
        )
        yield Footer()
        self.log("done yielding")

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        self.collection_list = self.query_one("#collection_list", DataTable)
        self_row_selected = self.collection_list.get_row(event.row_key)
        self.selected_guid = self_row_selected[0] or ""
        self.selected_name = self_row_selected[1] or ""
        self.selected_qname = self_row_selected[2] or ""
        self.selected_desc = self_row_selected[3] or ""
        self.log(f"Selected Data Product: {self.selected_name}")
        # self.get_collections_from_egeria(Egeria_config=self.Egeria_config, Search_str = self.selected_guid)

    def on_egeria_data_received(self, event: EgeriaDataReceived):
        self.collections = event.data
        self.update_collection_list(self.collections)

    def on_table_created(self, event: TableCreated, collections: list):
        self.collections = collections
        self.update_collection_list(self.collections)
        self.collection_list = event.table
        # return self.collection_list
        return self.collection_list

    @on(Button.Pressed, "#quit")
    def quit(self) -> None:
        """Signal the application to Quit gracefully """
        self.post_message(self.QuitRequested())

    def action_quit(self):
        """Signal the application to Quit gracefully """
        self.post_message(self.QuitRequested())

    def action_refresh(self):
        """Signal the application to refresh the screen """
        self.post_message(self.EgeriaDataReceived(self.collections))

