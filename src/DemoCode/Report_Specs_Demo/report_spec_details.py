"""
   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a set of report specification related functions for my_egeria.

"""

from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Container
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Static, ListView, Button, Footer, Header

from textual.widgets._data_table import DataTable

CSS_PATH = ["report_specs.tcss"]

class ReportSpecDetails(ModalScreen):
    """Screen to display report specification details."""

    class ReportDetailsContinue(Message):
        """Message to reeturn to the previous screen."""
        pass

    class ReportDetailsQuit(Message):
        """Message to terminate application gracefully."""
        def __init__(self, return_code:Optional[int]=200):
            super().__init__()
            self.return_code = return_code

    class ReportDetailsBack(Message):
        """Message to return to the previous screen."""
        pass

    def __init__(self, response,**kwargs):
        super().__init__(**kwargs)
        self.response = response
        self.Egeria_config = ["https://127.0.0.1:9443", "qs-view-server", "erinoverview", "secret"]
        self.platform_url = self.Egeria_config[0]
        self.view_server = self.Egeria_config[1]
        self.user = self.Egeria_config[2]
        self.password = self.Egeria_config[3]

        """create  a DataTable of key/value pairs"""
        self.spec_datatable: DataTable = DataTable()
        self.spec_datatable.id = "spec_data_table"
        self.spec_datatable.border = True
        self.spec_datatable.zebra_stripes = True
        self.spec_datatable.add_columns("Key", "Value")
       
    def compose(self) -> ComposeResult:
        # Process response data into the DataTable and mount it on the screen
        self.display_response(self.response)
        # Now build the screen content
        self.heading = "Report Spec Details"
        self.subheading = "Details from executing selected report spec."
        yield Header(show_clock=True)
        yield Static(f"{self.subheading}")
        Static(
            f"Server: {self.view_server} | Platform: {self.platform_url} | User: {self.user}",
            id="connection_info",
        )
        yield Container(
            Static(f"Start of Report Specification List:", id="report_start"),
            self.spec_datatable,
            Static(f"End of Report Specification List:", id="report_end")
            )
        yield Horizontal(
            Button("Quit", id="quit"),
            Button("Back", id="back"),
            Button("continue", id="continue"),
            id="action_row"
        )
        yield Footer()

    def display_response(self, response):
        """process reesponse data into a DataTable for display"""
        self.response = response
        response_data: list[dict] = response.get("data")
        self.log(f"response_data: {response_data}")
        if not response_data or response_data == None or response_data == "":
            response_data = [{"NoData": "No data found for selected item"}]
        if isinstance(response_data, list):
            response_data: dict = response_data[0]
        if isinstance(response_data, dict):
            for key, value in response_data.items():
                self.log(f"key: {key}, value: {value}")
                if isinstance(value, dict):
                    for vkey, vvalue in value.items():
                        self.spec_datatable.add_row(vkey, vvalue)
                        continue
                elif isinstance(value, list):
                    for v in value:
                        self.spec_datatable.add_row(key, v)
                        continue
                elif key == "kind" and value == "empty":
                    key_str = "No Data"
                    value_str = "For That Asset Type in this repository"
                    self.spec_datatable.add_row(key_str, value_str)
                    continue
                else:
                    self.spec_datatable.add_row(key, value)
                    continue
        return

    @on(Button.Pressed, "#continue")
    def handle_continue(self, event: Button.Pressed) -> None:
        """ handler for continue button"""
        self.post_message(self.ReportDetailsContinue())

    @on(Button.Pressed, "#quit")
    def handle_quit(self, event: Button.Pressed) -> None:
        """ handler for quit button"""
        self.post_message(self.ReportDetailsQuit())

    @on(Button.Pressed, "#back")
    def handle_back(self, event: Button.Pressed) -> None:
        """ handler for back button"""
        self.post_message(self.ReportDetailsBack())