"""
   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a set of report specification related functions for my_egeria.

"""
import os

from pydantic import ValidationError
from textual import on
from textual.app import ComposeResult, App
from textual.containers import Container, Horizontal, Grid, Vertical
from textual.widgets import Static, ListView, ListItem, Button, Footer, Header, DataTable

from pyegeria.base_report_formats import *
from pyegeria.format_set_executor import exec_report_spec

from tech_type_splash_screen import SplashScreen
from tech_type_details import TechTypeDetails

CSS_PATH = ["report_specs.tcss"]

class ReportSpec(App):

    SCREENS = {
        "splash": SplashScreen,
        "tech_type_details": "tech_type_details"
    }

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "back", "Back"),
    ]

    # CSS_PATH = ["tech_type.tcss"]

    class GridChildrenApp(App):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        def compose(self):
            self.query_one("#spec_grid", Grid).mount()
            return

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.Egeria_config = ["https://127.0.0.1:9443", "qs-view-server", "erinoverview", "secret"]
        self.platform_url = self.Egeria_config[0]
        self.view_server = self.Egeria_config[1]
        self.user = self.Egeria_config[2]
        self.password = self.Egeria_config[3]
        self.selected_tech_type: str = ""
        self.items: list = []

    def compose(self) -> ComposeResult:
        self.heading = "Report Specs"
        self.subheading = "Select a report spec to execute:"
        self.description = "Select a report spec to execute."
        self.tech_type_list = "Tech-Type-Details"

        self.tech_type_datatable: DataTable = DataTable()
        self.tech_type_datatable.id = "tech_type_datatable"
        self.tech_type_datatable.add_columns("Display Name", "Description", "Qualified Name")
        self.tech_type_datatable.zebra_stripes = True
        self.tech_type_datatable.border = True
        self.tech_type_datatable.show_header = True
        self.tech_type_datatable.cursor_type= "row"
        self.tech_type_list = self.get_tech_type_list()
        self.log(f"tech_type_list: {self.tech_type_list}, type: {type(self.tech_type_list)}")
        if isinstance(self.tech_type_list, dict):
            for item in self.tech_type_list:
                dname=item.get("Display Name")
                desc = item.get("Description")
                qname = item.get("Qualified Name")
                self.tech_type_datatable.add_row(dname, desc, qname)
                continue
        else:
            for item in self.tech_type_list:
                if isinstance(item, dict):
                    for entry in item:
                        dname = entry.get("Display Name")
                        desc = entry.get("Description")
                        qname = entry.get("Qualified Name")
                        self.tech_type_datatable.add_row(dname, desc, qname)
                        continue
                else:
                    self.log(f"Unknown shape in tech_type_list: {item}, type: {type(item)}")
                    self.tech_type_datatable.add_row("Error", "Unknown shape in tech_type_list", item)
        yield Header(show_clock=True)
        yield Vertical(
            Static(f"{self.subheading},   {self.description}"),
            Static(f"Server: {self.view_server} | Platform: {self.platform_url} | User: {self.user}"),
            id="connection_info")
        yield Container(
            Static(f"Start of Technology Type List:", id="report_start"),
            DataTable(id="tech_types_datatable"),
            Static(f"End of Technology Type List:", id = "report_end"),
            id = "tech_type_data_container",
            )
        yield Horizontal(
            Button("Quit", id="quit"),
            Button("Back", id="back"),
            id="action_row"
            )
        yield Footer()

    def on_mount(self) -> None:
        # Apply heights after DOM is built
        self.query_one("#connection_info", Vertical).styles.height = "10%"
        self.query_one("#tech_type_data_container", Container).styles.height = "80%"
        self.query_one("#action_row", Horizontal).styles.height = "10%"
        self.push_screen("splash")

    def on_splash_screen_splash_continue(self, Message) -> None:
        # continue button pressed on the splash screen, pop the splash screen
        self.pop_screen()

    @on(DataTable.RowSelected, "#tech_type_datatable")
    def handle_datatable_row_selected(self, message: DataTable.RowSelected) -> None:
        """ Handle ListView selection event """
        selected_row = message.row_key
        selected_item = self.tech_type_datatable.get_row(selected_row)
        self.log(f"Selected item: {selected_item} type: {type(selected_item)}")
        selected_item_name = str(selected_item[0] or "")
        selected_item_desc = str(selected_item[1] or "")
        selected_item_qname = str(selected_item[2] or "")
        self.selected_tech_type = selected_item_qname
        self.log(f"Selected tech type: {self.selected_tech_type}")
        self.query_selected_tech_type()

    @on(Button.Pressed, "#quit")
    def handle_button_pressed(self, event: Button.Pressed) -> None:
        """ Quit the application gracefully with a "good" return code (200) """
        self.log(f"Quit button clicked")
        self.exit(200)
        return

    @on(Button.Pressed, "#back")
    def handle_back_button_pressed(self, event: Button.Pressed) -> None:
        """ Return to the main menu screen """
        self.log(f"Back button clicked")
        self.tech_type_list = ""
        self.selected_tech_type = ""
        self.items.clear()
        self.switch_screen("splash")

    def get_tech_type_list(self):
        """ Get the list of tech types """
        self.tech_type_list: list = [{}]
        self.list_unpack: dict = {}
        self.tech_type_dict: dict = {}
        try:
            self.tech_type_response = exec_report_spec(format_set_name="Tech-Types",
                                                    output_format="DICT",
                                                    view_server=self.view_server,
                                                    view_url=self.platform_url,
                                                    user=self.user,
                                                    user_pass=self.password)
            self.tech_type_list = self.tech_type_response.get("data")
            self.tech_type_separated = self.unpack_egeria_data(self.tech_type_response)
            self.log(f"tech_type_separated: {self.tech_type_separated}")
            if isinstance(self.tech_type_separated, list):
                for entry in self.tech_type_separated:
                    if isinstance(entry, dict):
                        ename=entry.get("Display Name")
                        eqname = entry.get("Qualified Name")
                        edesc = entry.get("Description")
                        entry_item = f"{ename}, {edesc}, {edesc}"
                        self.tech_type_dict.update({ename: entry_item})
                        continue
                    elif isinstance(entry, list):
                        for list_item in entry:
                            self.log(f"list_item: {list_item}")
                            self.tech_type_dict.update(list_item)
                            self.list_unpack.update(list_item)
                            continue
                    else:
                        self.tech_type_dict = {"Error": "Unrecognized data shape in self.tech_type_list"}
                        continue
                    continue
                self.log(f"tech_type_dict: {self.tech_type_dict}")
        except Exception as e:
            self.log(f"Exception in get_tech_type_list: {e}")
            self.tech_type_dict = {"Error": f"get_tech_type_list - {e}"}
        except ValidationError as e:
            self.log(f"ValidationError in get_tech_type_list: {e}")
            self.tech_type_dict = {"ValidationError": f"get_tech_type_list - {e}"}
        return self.tech_type_dict

    def query_selected_tech_type(self):
        # query the selected tech type
        self.log(f"Executing tech type query: {self.selected_tech_type}")
        try:
            response = exec_report_spec(format_set_name="Tech-Types",
                                       output_format="DICT",
                                       view_server=self.view_server,
                                       view_url=self.platform_url,
                                       user=self.user,
                                       user_pass=self.password)
            self.log(f"Return from tech type query:")
            self.log(f"reponse: {response}")
        except (ValidationError) as e:
            self.log(f"ValidationError: {e}")
            response = {"error": f"ValidationError: {e}"}
        except Exception as e:
            self.log(f"Exception: {e}")
            response = {"error": f"Exception: {e}"}
        if response is None:
            response:dict = {"NoData": "No data returned from Egeria for tech types, notify admin"}
        return response

    def unpack_egeria_data(self, data) -> dict:
        """ Unpack the data returned from Egeria """
        output_data: dict = {}
        output_data.clear()
        if isinstance(data, dict):
            if "data" in data:
                output_data = data.get("data")
        elif isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    output_data = entry.get("data")
                elif isinstance(entry, list):
                    for subentry in entry:
                        if isinstance(subentry, dict):
                            output_data = subentry.get("data")
                        else:
                            output_data = {"error": "unknown data structure"}
                else:
                    output_data = {"error": "unknown outer data structure"}
        else:
            output_data = {"error": "not dict or list", "shape": "data to unpack is not a recognized shape"}
        return(output_data)

    # def on_report_spec_report_details_back(self, Message) -> None:
    #     """ Return to the main menu screen """
    #     self.pop_screen()
    #
    # def on_report_spec_report_details_quit(self, Message) -> None:
    #     """ Quit the application gracefully with a "good" return code (200) """
    #     self.exit(200)
    #
    # def on_report_spec_report_details_continue(self, Message) -> None:
    #     """ Return to the main menu screen """
    #     self.pop_screen()

if __name__ == "__main__":
    try:
        import pydevd_pycharm
        pydevd_pycharm.settrace(
            "127.0.0.1",  # Ensure it's localhost since your app runs on the same machine as PyCharm
            port=5679,  # Choose an available port
            stdout_to_server=True,
            stderr_to_server=True,
            suspend=False  # Set to False to let the application continue running after starting
        )
    except ImportError:
        print("pydevd-pycharm not installed or setup failed. Debugger won't be active.")
    except Exception as e:
        pass

    app = ReportSpec()
    os.environ.setdefault("EGERIA_PLATFORM_URL", "https://127.0.0.1:9443")
    os.environ.setdefault("EGERIA_VIEW_SERVER", "qs-view-server")
    os.environ.setdefault("EGERIA_USER", "erinoverview")
    os.environ.setdefault("EGERIA_USER_PASSWORD", "secret")
    app.run()
