"""
   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a set of report specification related functions for my_egeria.

"""

from typing import Any

from pyegeria import exec_report_spec, PyegeriaException, print_basic_exception
from textual import app, on
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.widgets import Tree, Header, Static, Placeholder, Footer, TextArea

from StatusScreen import StatusScreen


class SelectionOverviewScreen(Screen):
    """Screen to display the selection of the user's data sources."""
    BINDINGS = [("q", "quit", "Quit"),
                ("b", "back", "Go back")]

    CSS_PATH = "my_profile.tcss"

    def __init__(self, category, view_server, url, user, pwd, data_tree=None):
        self.category = category
        self.view_server = view_server
        self.platform_url = url
        self.user_name = user
        self.user_password = pwd
        self.data_tree = data_tree
        self.glossary_term_var_list: list = []

        if self.data_tree is None:
            if self.category == "glossary":
                try:
                    self.data_tree: Tree = self.app.query_one("#glossary_details_tree", Tree)
                except NoMatches:
                    self.dismiss(411)
                    return
            elif self.category == "catalog":
                try:
                    self.data_tree: Tree = self.app.query_one("#digital_product_catalog_tree", Tree)
                except NoMatches:
                    self.dismiss(412)
                    return
            elif self.category == "dictionary":
                try:
                    self.data_tree: Tree = self.app.query_one("#data_dictionary_tree", Tree)
                except NoMatches:
                    self.dismiss(413)
                    return
            elif self.category == "domain":
                try:
                    self.data_tree: Tree = self.app.query_one("#business_domain_tree", Tree)
                except NoMatches:
                    self.dismiss(414)
                    return
            elif self.category == "specification":
                try:
                    self.data_tree: Tree = self.app.query_one("#data_specification_tree", Tree)
                except NoMatches:
                    self.dismiss(415)
                    return
            else:
                # unknown category
                self.dismiss(410)
        super().__init__()

    def compose(self) -> ComposeResult:
        """ Compose the UI components for the SelectionOverviewScreen screen."""
        self.title = f"Shopping for Data, Data Selection:"
        self.sub_title = f"Category: {self.category}"
        yield Header(show_clock=True)
        yield Static("Please select an item from the tree [blink]:[/]", id="instruction_static")
        yield ScrollableContainer(
                                    self.data_tree,
                                    id="data_tree_container"
                                    )
        yield ScrollableContainer(
                                Placeholder(id="data_details_placeholder"),
                                id="data_details_placeholder_container"
                                    )
        yield Footer()

    def action_quit(self) -> None:
        """ The quit option in the footer has been selected. Dismiss the screen."""
        self.dismiss(210)

    def action_back(self) -> None:
        """ The back option in the footer has been selected. Dismiss the screen."""
        self.dismiss(200)

    @on(Tree.NodeSelected)
    def handle_tree_node_selected(self, event: Tree.NodeSelected):
        # Modify to handle for each tree?
        self.node_selected = event.node
        self.log(f"Node selected: {self.node_selected}")
        self.node_label = self.node_selected.label
        self.node_data = self.node_selected.data
        # the provided id can be either a GUID or a qualified name!
        # the variable is labeled guid but it could contain a qualified name, both guid and qualified name are strings.
        self.node_GUID = self.node_selected.data
        self.log(f"Node label: {self.node_label}, GUID: {self.node_GUID}")
        if self.category == "glossary":
            self.display_selected_term_details(self.node_GUID)
        elif self.category == "catalog":
            self.display_selected_digital_product(self.node_GUID)
        elif self.category == "dictionary":
            self.display_selected_data_dictionary(self.node_GUID)
        elif self.category == "domain":
            self.display_selected_business_domain(self.node_GUID)
        elif self.category == "specification":
            self.display_selected_data_specification(self.node_GUID)

    def display_selected_term_details(self, term_GUID) -> Any:
        """ The user has selected a glossary term, build a display of the term details,
             and show along side the glossary tree """
        self.term_GUID = term_GUID
        self.log(f"Selected glossary term GUID: {self.term_GUID}")
        try:
            self.glossary_term_data = exec_report_spec(format_set_name="Glossary-Terms",
                                                  output_format="DICT",
                                                  params={"search_string": self.term_GUID, "filter_string": self.term_GUID},
                                                  view_server=self.view_server,
                                                  view_url=self.platform_url,
                                                  user=self.user_name,
                                                  user_pass=self.user_password)
        except PyegeriaException as e:
            # print_basic_exception(e)
            self.log(f"Error retrieving glossary details: {e!s}")
            # self.dismiss(421)
            # return (421)
            self.glossary_term_data = []

        container = self.query_one("#data_details_placeholder_container")
        container.remove_children()

        if not self.glossary_term_data or self.glossary_term_data == [] or self.glossary_term_data == None or self.glossary_term_data.get("kind") == "empty":
            self.log(f"No glossary term data returned for GUID: {self.term_GUID}")
            container.mount(Static(f"No glossary term data returned for GUID: {self.term_GUID}"))
        else:
            self.log(f"Glossary term data returned for term: {self.term_GUID}, content: {self.glossary_term_data} \n")
            text_area = TextArea(f"Glossary term data returned for term: {self.term_GUID}", id="glossary_term_details_text_area", read_only=True)
            container.mount(text_area)
            glossary_term_vars = self.glossary_term_data.get("data", "No data available")
            self.log(f"Glossary term data: {glossary_term_vars}")
            if isinstance(glossary_term_vars, list):
                glossary_term_vars = glossary_term_vars[0]
            self.glossary_term_var_list: list = []
            for glossary_term_var_key, glossary_term_var_content in glossary_term_vars.items():
                self.log(f"Glossary term variable: {glossary_term_var_key}, content: {glossary_term_var_content}")
                self.glossary_term_var_list.append(str(glossary_term_var_key)+ " " +str(glossary_term_var_content) + "\n")
            
            text_area.text = "".join(self.glossary_term_var_list)

    def display_selected_digital_product(self, digital_product_GUID) -> Any:
        """ The user has selected a glossary term, build a display of the term details,
                    and show along side the glossary tree """
        self.digital_product_GUID = digital_product_GUID
        self.log(f"Selected digital product GUID: {self.digital_product_GUID}")
        try:
            self.digital_product_data = exec_report_spec(format_set_name="Digital-Products",
                                                       output_format="DICT",
                                                       params={"search_string": self.digital_product_GUID,
                                                               "filter_string": self.digital_product_GUID},
                                                       view_server=self.view_server,
                                                       view_url=self.platform_url,
                                                       user=self.user_name,
                                                       user_pass=self.user_password)
        except PyegeriaException as e:
            # print_basic_exception(e)
            self.log(f"Error retrieving digital product details: {e!s}")
            # self.dismiss(421)
            # return (421)
            self.digital_product_data = []

        container = self.query_one("#data_details_placeholder_container")
        container.remove_children()

        if not self.digital_product_data or self.digital_product_data == []:
            self.log(f"No digital product data returned for GUID: {self.digital_product_GUID}")
            container.mount(Static(f"No digital product data returned for GUID: {self.digital_product_GUID}"))
        else:
            self.log(f"Digital product data returned for GUID: {self.digital_product_GUID}")
            text_area = TextArea(f"Digital product data returned for GUID: {self.digital_product_GUID}", id="digital_product_details_text_area",
                     read_only=True)
            container.mount(text_area)
            text_area.text = str(self.digital_product_data)

    def display_selected_data_dictionary(self, data_dictionary_GUID) -> Any:
        """ The user has selected a data dictionary, build a display of the dictionary details,
                            and show along side the dictionary tree """
        self.data_dictionary_GUID = data_dictionary_GUID
        self.log(f"Selected data dictionary GUID: {self.data_dictionary_GUID}")
        try:
            self.data_dictionary_data = exec_report_spec(format_set_name="Data-Dictionaries",
                                                         output_format="DICT",
                                                         params={"search_string": self.data_dictionary_GUID,
                                                                 "filter_string": self.data_dictionary_GUID},
                                                         view_server=self.view_server,
                                                         view_url=self.platform_url,
                                                         user=self.user_name,
                                                         user_pass=self.user_password)
        except PyegeriaException as e:
            # print_basic_exception(e)
            self.log(f"Error retrieving data dictionary details: {e!s}")
            # self.dismiss(421)
            # return (421)
            self.data_dictionary_data = []

        container = self.query_one("#data_details_placeholder_container")
        container.remove_children()

        if not self.data_dictionary_data or self.data_dictionary_data == []:
            self.log(f"No data dictionary data returned for GUID: {self.data_dictionary_GUID}")
            container.mount(Static(f"No data dictionary data returned for GUID: {self.data_dictionary_GUID}"))
        else:
            self.log(f"Data dictionary data returned for GUID: {self.data_dictionary_GUID}")
            text_area = TextArea(f"Data dictionary data returned for GUID: {self.data_dictionary_GUID}",
                     id="data_dictionary_details_text_area",
                     read_only=True)
            container.mount(text_area)
            text_area.text = str(self.data_dictionary_data)

    def display_selected_business_domain(self, business_domain_GUID) -> int:
        """ The user has selected a business domain, build a display of the domain details,
                            and show along side the glossary tree """
        self.business_domain_GUID = business_domain_GUID
        self.log(f"Selected business domain GUID: {self.business_domain_GUID}")
        try:
            self.business_domain_data = exec_report_spec(format_set_name="BusinessCapabilities",
                                                         output_format="DICT",
                                                         params={"search_string": self.business_domain_GUID,
                                                                 "filter_string": self.business_domain_GUID},
                                                         view_server=self.view_server,
                                                         view_url=self.platform_url,
                                                         user=self.user_name,
                                                         user_pass=self.user_password)
        except PyegeriaException as e:
            # print_basic_exception(e)
            self.log(f"Error retrieving business domain details: {e!s}")
            # self.dismiss(421)
            # return (421)
            self.business_domain_data = []

        container = self.query_one("#data_details_placeholder_container")
        container.remove_children()

        if not self.business_domain_data or self.business_domain_data == []:
            self.log(f"No business domain data returned for GUID: {self.business_domain_GUID}")
            container.mount(Static(f"No business domain data returned for GUID: {self.business_domain_GUID}"))
        else:
            self.log(f"Business domain data returned for GUID: {self.business_domain_GUID}")
            text_area = TextArea(f"Business domain data returned for GUID: {self.business_domain_GUID}",
                     id="business_domain_details_text_area",
                     read_only=True)
            container.mount(text_area)
            text_area.text = str(self.business_domain_data)

    def display_selected_data_specification(self, data_specification_GUID) -> int:
        """ The user has selected a data specification, build a display of the specification details
            and show alongside data specifications tree """

        self.data_specification_qualified_name = data_specification_GUID
        self.log(f"Data specification selected: {self.data_specification_qualified_name}")
        try:
            self_data_specification_data = exec_report_spec(format_set_name="Data-Specification",
                                                            output_format="DICT",
                                                            params={"search_string": self.data_specification_qualified_name,
                                                                    "filter_string": self.data_specification_qualified_name},
                                                            view_server=self.view_server,
                                                            view_url=self.platform_url,
                                                            user=self.user_name,
                                                            user_pass=self.user_password)
        except PyegeriaException as e:
            # print_basic_exception(e)
            self.log(f"Error retrieving data specification details: {e!s}")
            # self.dismiss(431)
            # return (431)
            self.data_specification_data = []

        container = self.query_one("#data_details_placeholder_container")
        container.remove_children()

        if not self.data_specification_data or self.data_specification_data == []:
            self.log(f"No data specification data returned for qualified name: {self.data_specification_qualified_name}")
            container.mount(Static(f"No data specification data returned for qualified name: {self.data_specification_qualified_name}"))
        else:
            self.log(f"Data specification data returned for qualified name: {self.data_specification_qualified_name}")
            text_area = TextArea(f"Data specification data returned for qualified name: {self.data_specification_qualified_name}",
                     id="data_specification_details_text_area",
                     read_only=True)
            container.mount(text_area)
            text_area.text = str(self_data_specification_data)
