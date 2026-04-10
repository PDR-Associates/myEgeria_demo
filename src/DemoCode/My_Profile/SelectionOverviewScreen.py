from pyegeria import exec_report_spec, PyegeriaException, print_basic_exception
from textual import app, on
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widgets import Tree, Header, Static, Placeholder, Footer, TextArea

from StatusScreen import StatusScreen


class SelectionOverviewScreen(Screen):
    """Screen to display the selection of the user's data sources."""
    BINDINGS = [("q", "quit", "Quit"),
                ("b", "back", "Go back")]

    CSS_PATH = "my_profile.tcss"

    def __init__(self, category, view_server, url, user, pwd):
        self.category = category
        self.view_server = view_server
        self.platform_url = url
        self.user_name = user
        self.user_password = pwd
        if self.category == "glossary":
            self.data_tree: Tree = app.query_one("#glossary_details_tree", Tree)
        elif self.category == "catalog":
            self.data_tree: Tree = app.query_one("#digital_product_catalog_tree", Tree)
        elif self.category == "dictionary":
            self.data_tree: Tree = app.query_one("#data_dictionary_tree", Tree)
        elif self.category == "domain":
            self.data_tree: Tree = app.query_one("#business_domain_tree", Tree)
        elif self.category == "specification":
            self.data_tree: Tree = app.query_one("#data_specification_tree", Tree)
        else:
            # unknown category
            # push status screen, logic error in code.
            error_category = "Collection Category"
            error_message = "Unknown collection category returned"
            self.log(f"Error in selection overview processing: {error_category}, {error_message}")
            app.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=app.status_callback)
        super().__init__()

    def compose(self) -> ComposeResult:
        """ Compose the UI components for the SelectionOverviewScreen screen."""
        self.title = f"Shopping for Data, Data Selection:"
        self.sub_title = f"Category: {self.category}"
        yield Header(show_clock=True)
        yield Static("Please select an item from the tree [blink]:[/]")
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

    @on(Tree.NodeSelected, "#data_tree")
    def handle_tree_node_selected(self, event: Tree.NodeSelected):
        # Modify to handle for each tree?
        self.node_selected = event.node
        self.log(f"Node selected: {self.node_selected}")
        self.node_label = self.node_selected.label
        # the provided id can be either a GUID or a qualified name!
        # the variable is labeled guid but it could contain a qualified name, both guid and qualified name are strings.
        self.node_GUID = self.node_selected.data
        self.log(f"Node label: {self.node_label}, GUID: {self.node_GUID}")
        if self.node_label == "glossary":
            self.display_selected_term_details(self.node_GUID)
        elif self.node_label == "digital_product_catalog":
            self.display_selected_digital_product(self.node_GUID)
        elif self.node_label == "data_dictionary":
            self.display_selected_data_dictionary(self.node_GUID)
        elif self.node_label == "business_domain":
            self.display_selected_business_domain(self.node_GUID)
        elif self.node_label == "data_specification":
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
            print_basic_exception(e)
            self.log(f"Error retrieving glossary details: {e!s}")
            self.dismiss(421)
            return (421)
        if not self.glossary_term_data or self.glossary_term_data == []:
            self.log(f"No glossary term data returned for GUID: {self.term_GUID}")
            Static(f"No glossary term data returned for GUID: {self.term_GUID}").mount(self.query_one("#glossary_term_details_container"))
        else:
            self.log(f"Glossary term data returned for GUID: {self.term_GUID}")
            TextArea(f"Glossary term data returned for GUID: {self.term_GUID}", id="glossary_term_details_text_area", read_only=True).mount(self.query_one("#glossary_term_details_container"))
            TextArea.data = self.glossary_term_data

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
            print_basic_exception(e)
            self.log(f"Error retrieving digital product details: {e!s}")
            self.dismiss(421)
            return (421)
        if not self.digital_product_data or self.digital_product_data == []:
            self.log(f"No digital product data returned for GUID: {self.digital_product_GUID}")
            Static(f"No digital product data returned for GUID: {self.digital_product_GUID}").mount(
                self.query_one("#digital_product_details_container"))
        else:
            self.log(f"Digital product data returned for GUID: {self.digital_product_GUID}")
            TextArea(f"Digital product data returned for GUID: {self.digital_product_GUID}", id="digital_product_details_text_area",
                     read_only=True).mount(self.query_one("#digital_product_details_container"))
            TextArea.data = self.digital_product_data

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
            print_basic_exception(e)
            self.log(f"Error retrieving data dictionary details: {e!s}")
            self.dismiss(421)
            return (421)
        if not self.data_dictionary_data or self.data_dictionary_data == []:
            self.log(f"No data dictionary data returned for GUID: {self.data_dictionary_GUID}")
            Static(f"No data dictionary data returned for GUID: {self.data_dictionary_GUID}").mount(
                self.query_one("#data_dictionary_details_container"))
        else:
            self.log(f"Data dictionary data returned for GUID: {self.data_dictionary_GUID}")
            TextArea(f"Data dictionary data returned for GUID: {self.data_dictionary_GUID}",
                     id="data_dictionary_details_text_area",
                     read_only=True).mount(self.query_one("#data_dictionary_details_container"))
            TextArea.data = self.data_dictionary_data

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
            print_basic_exception(e)
            self.log(f"Error retrieving business domain details: {e!s}")
            self.dismiss(421)
            return (421)
        if not self.business_domain_data or self.business_domain_data == []:
            self.log(f"No business domain data returned for GUID: {self.business_domain_GUID}")
            Static(f"No business domain data returned for GUID: {self.business_domain_GUID}").mount(
                self.query_one("#business_domain_details_container"))
        else:
            self.log(f"Business domain data returned for GUID: {self.business_domain_GUID}")
            TextArea(f"Business domain data returned for GUID: {self.business_domain_GUID}",
                     id="business_domain_details_text_area",
                     read_only=True).mount(self.query_one("#business_domain_details_container"))
            TextArea.data = self.business_domain_data

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
            print_basic_exception(e)
            self.log(f"Error retrieving data specification details: {e!s}")
            self.dismiss(431)
            return (431)
        if not self_data_specification_data or self_data_specification_data == []:
            self.log(f"No data specification data returned for qualified name: {self.data_specification_qualified_name}")
            Static(f"No data specification data returned for qualified name: {self.data_specification_qualified_name}").mount(
                self.query_one("#data_specification_details_container"))
        else:
            self.log(f"Data specification data returned for qualified name: {self.data_specification_qualified_name}")
            TextArea(f"Data specification data returned for qualified name: {self.data_specification_qualified_name}",
                     id="data_specification_details_text_area",
                     read_only=True).mount(self.query_one("#data_specification_details_container"))
            TextArea.data = self_data_specification_data
