"""
   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a set of report specification related functions for my_egeria.

"""
import ast
import os

from textual import on
from textual.app import ComposeResult, App
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, ListView, ListItem, Label, Button, Footer, Header, TextArea

from pyegeria.base_report_formats import select_report_spec, report_spec_list
from pyegeria.format_set_executor import exec_report_spec

from report_spec_splash_screen import SplashScreen

CSS_PATH = ["report_specs.tcss"]

class ReportSpec(App):

    SCREENS = {
        "splash": SplashScreen,
    }

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "back", "Back"),
    ]

    CSS_PATH = ["report_specs.tcss"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.Egeria_config = ["https://127.0.0.1:9443", "qs-view-server", "erinoverview", "secret"]
        self.platform_url = self.Egeria_config[0]
        self.view_server = self.Egeria_config[1]
        self.user = self.Egeria_config[2]
        self.password = self.Egeria_config[3]
        self.selected_report_spec: str = ""
        self.items: list = []

    def compose(self) -> ComposeResult:
        self.heading = "Report Specs"
        self.subheading = "Select a report spec to execute:"
        self.description = "Select a report spec to execute."
        self.report_spec_list = report_spec_list()
        self.log(f"report_spec_list: {self.report_spec_list}, type: {type(self.report_spec_list)}")
        # Split the report spec string into individual report spec names and insert into ListView
        self.report_specs_listview: ListView = ListView()
        self.report_specs_listview.id = "report_specs_listview"
        for item in self.report_spec_list:
            self.items.append(ListItem(Static(f"{item}")))

        yield Header(show_clock=True)
        yield Static(f"{self.subheading},   {self.description}")
        Static(
            f"Server: {self.view_server} | Platform: {self.platform_url} | User: {self.user}",
            id="connection_info",
        )
        yield Container(
            Static(f"Start of Report Specification List:", id="report_start"),
            ListView(*self.items, id="report_specs_listview"),
            Static(f"End of Report Specification List:", id = "report_end"),
            id = "report_specs_listview_container"
            )
        yield Horizontal(
            Button("Quit", id="quit"),
            Button("Back", id="back"),
            id="action_row"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.push_screen("splash")


    def on_splash_screen_splash_continue(self, Message) -> None:
        # continue button pressed on the splash screen, pop the splash screen
        self.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected):
        """ Handle ListView selection event """
        selected_item = event.item.query_one(Static).content
        self.log(f"Selected item: {selected_item} type: {type(selected_item)}")
        # selected_item_label = selected_item.query_one(Label).renderable
        selected_item_text = selected_item
        # selected_item_text = selected_item_label.renderable
        self.log(f"Selected item text: {selected_item_text}, type: {type(selected_item_text)}")
        self.selected_report_spec = selected_item_text
        self.log(f"Selected report spec: {self.selected_report_spec}")
        self.access_report_specs()

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
        self.report_spec_list = ""
        self.selected_report_spec = ""
        self.items.clear()
        self.switch_screen("splash")

    def access_report_specs(self):
        """ Access pyegeria report specifications """
        self.log(f"Accessing report specs")
        try:
            # Retrieve needed format sets from pyegeria
            catalog_set = select_report_spec(self.selected_report_spec, "DICT")
            if catalog_set:
                self.log("Successfully retrieved format set by name!")
                self.log(f"Heading: {catalog_set['heading']}")
                self.log(f"Description: {catalog_set['description']}")
            else:
                self.log(f"Failed to retrieve {self.selected_report_spec} format set by name.")
                self.log("Program Error, please report issue to maintainer.")
                self.exit(400)
        except Exception as e:
            self.log(f"Error connecting to PyEgeria: {str(e)}")
            self.exit(401)
        self.execute_selected_report_spec()

    def execute_selected_report_spec(self):
        # execute the selected report spec
        self.log(f"Executing report spec: {self.selected_report_spec}")
        reponse = exec_report_spec(format_set_name=self.selected_report_spec,
                                   output_format="DICT",
                                   view_server=self.view_server,
                                   view_url=self.platform_url,
                                   user=self.user,
                                   user_pass=self.password)
        self.log(f"Return from exec_report_spec:")
        self.log(f"reponse: {reponse}")
        self.display_response(reponse)

    def display_response(self, response):
        top = self.query_one("#report_specs_listview", ListView)
        top.remove()
        self.response = response
        response_data: list[dict] = response.get("data")
        self.log(f"response_data: {response_data}")
        if not response_data or response_data == None or response_data == "":
            response_data = [{"NoData": "No data found for selected item"}]
        if isinstance(response_data, list):
            response_data: dict = response_data[0]
        if isinstance(response_data, dict):
            i = 0
            for key, value in response_data.items():
                self.log(f"key: {key}, value: {value}")
                if isinstance(value, dict):
                    for vkey, vvalue in value.items():
                        key_widget = Static(f"{vkey}", id="response_key")
                        value_widget = Static(f"{vvalue}", id = 'response_value')
                        self.query_one("#report_specs_listview_container").mount(key_widget, before="#report_end")
                        self.query_one("#report_specs_listview_container").mount(value_widget, before="#report_end")
                        continue
                elif isinstance(value, list):
                    for v in value:
                        key_widget = Static(f"{v}", id="vresponse_key"+f"{i}")
                        value_widget = Static(f"{v}", id = "vresponse_value"+f"{i}")
                        self.query_one("#report_specs_listview_container").mount(key_widget, before="#report_end")
                        self.query_one("#report_specs_listview_container").mount(value_widget, before="#report_end")
                        i += 1
                        continue
                elif key == "kind" and value == "empty":
                    key_widget = Static(f"No Data", id="eresponse_key")
                    value_widget = Static(f"For That Asset Type in this repository", id='eresponse_value')
                    self.query_one("#report_specs_listview_container").mount(key_widget, before="#report_end")
                    self.query_one("#report_specs_listview_container").mount(value_widget, before="#report_end")
                    continue
                else:
                    key_widget = Static(f"{key}", id="response_key"+f"{i}")
                    value_widget = Static(f"{value}", id = "response_value"+f"{i}")
                    self.query_one("#report_specs_listview_container").mount(key_widget, before="#report_end")
                    self.query_one("#report_specs_listview_container").mount(value_widget, before="#report_end")
                    i += 1
                    continue
        # Once the data is loaded to the display area, add the Continue button
        continue_button = Button("Continue", variant="primary", id="continue_report")
        self.query_one("#action_row").mount(continue_button,after="#back",)

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
