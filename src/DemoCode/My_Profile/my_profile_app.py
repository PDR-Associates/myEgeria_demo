"""
   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a set of report specification related functions for my_egeria.

"""

import datetime
import re

from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard
from pyegeria import load_app_config, settings, MyProfile, PyegeriaException, print_basic_exception, exec_report_spec, \
    AutomatedCuration, MetadataExpert, ActorManager
from textual import on
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import DataTable, OptionList, Header, Static, Footer, Tree

from CreateProfileScreen import CreateProfileScreen
from TechnologyTypesScreen import TechnologyTypesScreen
from TechnologyTypeOptionsScreen import TechnologyTypeOptionsScreen
from TechnologyTypeTemplatesScreen import TechnologyTypeTemplatesScreen
from TechnologyTypeProcessesScreen import TechnologyTypeProcessesScreen
from StatusScreen import StatusScreen
from ShopForDataScreen import ShopForDataScreen
from SelectionOverviewScreen import SelectionOverviewScreen
from MyTeam import MyTeam
from MainScreen import MainScreen


class MyProfileApp(App):
    """My Profile App.

    Retrieves a user's profile from Egeria and displays current work items.
    If no profile is found, offers a UI to create one.
    """

    BINDINGS = [("q", "quit", "Quit")]
    CSS_PATH = "my_profile.tcss"

    SCREENS = {
        "main": MainScreen,
        "_default": MainScreen,
        "create_profile": CreateProfileScreen,
        "tech_types": TechnologyTypesScreen,
        "tech_type_options": TechnologyTypeOptionsScreen,
        "tech_type_templates": TechnologyTypeTemplatesScreen,
        "tech_type_processes": TechnologyTypeProcessesScreen,
        "status": StatusScreen,
        "shop_4_data": ShopForDataScreen,
        "overview": SelectionOverviewScreen,
        "my_team": MyTeam
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.contribution_record = None
        self.heading = "My_Profile"
        self.subheading = "Egeria Profile for current user"
        self.description = "Display the user related items for the current user."
        load_app_config("config/config.json")
        app_config = settings.Environment
        app_user = settings.User_Profile
        # config_logging()
        print("Platform:", app_config.egeria_platform_url)
        print("View Server:", app_config.egeria_view_server)
        self.user_name = app_user.user_name or "garygeeke"
        self.user_password = app_user.user_pwd or "secret"
        self.view_server = app_config.egeria_view_server or "qs-view-server"
        self.platform_url = app_config.egeria_platform_url or "https://127.0.0.1:9443"

        # Ensure compose() is safe before data loads
        self.actor_profile: dict = {}
        self.projects = []
        self.communities = []
        self.roles = []
        self.actions = []
        self.teams = []
        self.other_function_list = []
        self.tech_type_json: str
        self.tech_type_response = None
        self.tech_type_list = []
        self.tech_type_guid = ""
        self.tech_type_name = ""
        self.tech_type_description = ""
        self.selected_t_node = None
        self.selected_t_node_label = None
        self.karma_points = 0
        self.tech_type_templates = [{}]
        self.tech_type_processes = [{}]
        self.full_template = None
        self.glossary_data_extract = None
        self.business_glossary_data_extract = None
        self.display_glossary_data_extract = None
        self.digital_glossary_data_extract = None
        self.team_members: list[list] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    async def on_mount(self) -> None:
        """Load profile; if missing, prompt to create it; then populate tables."""
        # DOMInfo.attach_to(self)
        # Initiate clipboard session
        clipboard = PyperclipClipboard()

        await self._load_or_create_profile()
        await self._populate_tables()


    async def _load_or_create_profile(self) -> None:
        try:
            #instantiate the class
            self.my_profile_inst = MyProfile(self.view_server, self.platform_url, self.user_name, self.user_password)
            self.my_profile_inst.create_egeria_bearer_token(self.user_name, self.user_password)
            #retrieve the profile
            self.my_profile_data = await self.my_profile_inst._async_get_my_profile(
                report_spec="My-User-MD",
                output_format="DICT",
                )
            self.log(f"retrieve profile result: {self.my_profile_data}")
        except (PyegeriaException) as e:
            self.log(f"Error retrieving profile: {e!s}")
            print_basic_exception(e)
            self.exit(402)
            return

        if self.my_profile_data == []:
            self.log(f"Error retrieving profile. Prompting to create one...")
            self.log(f"To create a profile you must have a valid userid in the system, please contact your system administrator to create one if needed")
            await self.push_screen(CreateProfileScreen(), callback = self.new_profile_return)
        else:
            self.new_profile_return(200)

    def new_profile_return(self, result: int) -> None:
        """ This function handles either the return from the create new profile screen or
            when the user already has a profile continue processing """
        self.log(f"Profile creation result: {result}")
        if not result or result != 200:
            self.log(f"Profile creation cancelled/failed; return: {result}, exiting.")
            self.exit(403)
            return

        self.result = result

        # Retry after creation if necessary
        try:
            self.user_profile_struct = self.my_profile_inst.get_my_profile(
                output_format="DICT",
                report_spec="My-User-MD",
            )
            self.log(f"Profile retrieved successfully: {self.user_profile_struct}")
            self.push_screen("main")
        except PyegeriaException as e2:
            self.log(f"Error retrieving user profile: {e2!s}")
            self.exit(412)
            return
        if self.user_profile_struct is []:
            self.log(f"Error retrieving user profile. Exiting.")
            self.exit(413)
            return

        # strip out the individual profile elements
        self.user_profile = self.user_profile_struct[0]
        self.contribution_record = self.user_profile.get("Contribution Record") or {}
        for c in self.contribution_record:
            self.karma_points = c.get("Karma Points") or 0
            break
        self.my_projects_data = self.user_profile.get("Projects") or []
        self.my_teams_data = self.user_profile.get("Teams") or []
        self.my_communities_data = self.user_profile.get("Communities") or []
        self.my_roles_data = self.user_profile.get("Roles") or []
        self.my_actions_data = self.user_profile.get("Actions") or []
        self.log(f"Contribution Record: {self.contribution_record}")
        self.log(f"Karma Points: {self.karma_points}")
        self.log(f"my_projects_data: {self.my_projects_data}")
        self.log(f"my_teams_data: {self.my_teams_data}")
        self.log(f"my_communities_data: {self.my_communities_data}")
        self.log(f"my_roles_data: {self.my_roles_data}")
        self.log(f"my_actions_data: {self.my_actions_data}")
        # User Identities
        try:
            self.user_identities = self.my_profile_inst.get_my_profile(
                report_spec="User-Identities",
                output_format="DICT",
            )
            self.log(f"User-Identities: {self.user_identities}, type: {type(self.user_identities)}")
        except PyegeriaException as e:
            self.log(f"Error retrieving User-Identities: {e!s}")
            self.user_identities = {}

        # Normalize expected keys
        self.full_name = self.user_profile.get("Full Name") or ""
        self.sub_title = f"{self.full_name} ({self.user_profile.get('User ID')}, Karma Points: {self.karma_points})"
        self.projects = self.my_projects_data or []
        self.communities = self.my_communities_data or []
        self.roles = self.my_roles_data or []
        self.actions = self.user_profile.get("actions") or []
        self.teams = self.my_teams_data or []
        if isinstance(self.user_identities, list):
            self.user_identity = self.user_identities
        else:
            self.user_identity = self.user_identities.get("User-Identities") or []

    async def _populate_tables(self) -> None:
        """Populates tables from normalized profile data"""
        main_screen = self.get_screen("main")
        self.projects_table = main_screen.query_one("#projects_table", DataTable)
        self.communities_table = main_screen.query_one("#communities_table", DataTable)
        self.roles_table = main_screen.query_one("#roles_table", DataTable)
        self.actions_table = main_screen.query_one("#actions_table", DataTable)
        self.user_identity_table = main_screen.query_one("#user_identity_table", DataTable)
        self.teams_table = main_screen.query_one("#teams_table", DataTable)

        assert self.projects_table is not None
        assert self.communities_table is not None
        assert self.roles_table is not None
        assert self.actions_table is not None
        assert self.user_identity_table is not None
        assert self.teams_table is not None

        self.projects_table.clear(columns=True)
        self.projects_table.add_columns("Project Name", "Description", "Qualified Name")

        self.communities_table.clear(columns=True)
        self.communities_table.add_columns("Assignment Type", "Community Name", "Description", "Qualified Name")

        self.roles_table.clear(columns=True)
        self.roles_table.add_columns("Role Name", "Description","GUID")
        self.roles_table.zebra = True
        self.roles_table.cursor_type = "row"

        self.teams_table.clear(columns=True)
        self.teams_table.add_columns("Assignment Type", "Team Name", "Description","GUID")

        self.actions_table.clear(columns=True)
        self.actions_table.add_columns("Action Name", "Status", "Description")

        self.user_identity_table.clear(columns=True)
        self.user_identity_table.add_columns("Display Name", "User ID", "Distinguished Name")

        # Populate rows
        for p in self.projects if isinstance(self.projects, list) else []:
            self.projects_table.add_row(
                str(p.get("Name", "")),
                str(p.get("Description", "")),
                str(p.get("Qualified Name", "")),
            )

        for c in self.communities if isinstance(self.communities, list) else []:
            self.communities_table.add_row(
                str(c.get("Assignment Type", "")),
                str(c.get("Display Name", "")),
                str(c.get("Description", "")),
                str(c.get("Qualified Name", ""))
            )

        for r in self.roles if isinstance(self.roles, list) else []:
            self.roles_table.add_row(
                str(r.get("Name", "")),
                str(r.get("Type", "")),
                str(r.get("GUID", "")),
            )

        for a in self.actions if isinstance(self.actions, list) else []:
            self.actions_table.add_row(
                str(a.get("Display Name", "")),
                str(a.get("Description", "")),
            )

        for t in self.teams if isinstance(self.teams, list) else []:
            self.teams_table.add_row(
                str(t.get("Assignment Type", "")),
                str(t.get("Name", "")),
                str(t.get("Description", "")),
                str(t.get("GUID", "")),
            )

    def action_quit(self) -> None:
        # quit selected by user, so exit app
        self.exit(200)

    @on(OptionList.OptionSelected, "#other_function_list")
    async def handle_option_selected(self, event: OptionList.OptionSelected):
        # option selected by user
        selected_option = event.option.prompt
        selected_option_id = event.option.id
        self.log(f"Selected option: {selected_option} ({selected_option_id})")
        if selected_option == "Technology Types":
            self.log("Fetching technology types...")
            await self.fetch_technology_types()
            self.log(f"Tech Type Response: {self.tech_type_response} | {self.tech_type_list}")
            if self.tech_type_response == []:
                self.log("No technology types found.")
                self.exit(200)
            elif len(self.tech_type_response) == 3 and int(self.tech_type_response) >= 400:
                self.log("Error fetching technology types.")
                self.exit(int(self.tech_type_response))
            self.log("Technology types fetched successfully.")
            self.log("Displaying technology types...")
            await self.push_screen(TechnologyTypesScreen(self.tech_type_list, self.user_name, self.user_password, self.karma_points), callback=self.tech_type_callback)
            self.log("Technology types displayed successfully.")
        elif selected_option == "User Identities":
            pass
        elif selected_option == "Catalogs/Shop for Data":
            """ Push new Screen, Show Glossaries, Digital Product Catalogs, Data Dictionaries and
                Business Domains, allow the user to select from one of the 4 categories and use that selection to
                display a list of available collections of the chosen type and allow the user to subscribe to them
                """

            # start by gathering the data using Pyegeria to access the Egeria backend servers

            # Glossaries
            glossary_table: DataTable = DataTable(id="glossary_table")
            glossary_table.add_columns("Glossary Name", "Description", "Qualified Name")
            glossary_table.cursor_type = "row"
            glossary_table.zebra_stripes = True
            try:
                self.glossary_data = exec_report_spec(format_set_name="Glossaries",
                                                       output_format="DICT",
                                                       params = {"search_string" : "*"},
                                                       view_server=self.view_server,
                                                       view_url=self.platform_url,
                                                       user=self.user_name,
                                                       user_pass=self.user_password)
            except PyegeriaException as e:
                print_basic_exception(e)
                self.log(f"Error retrieving glossary details: {e!s}")
                self.exit(420)
                return(420)
            self.log(f"Glossary data returned: {self.glossary_data}")
            self.glossary_data_extract = self.glossary_data.get("data") or []
            self.log(f"Glossary data extracted: {self.glossary_data_extract}")
            if self.glossary_data_extract == []:
                self.log(f"No glossary data found for search string: {self.selected_t_node}")
                glossary_table.add_row("No glossaries found", "No data returned from Egeria", "")
            else:
                for g in self.glossary_data_extract:
                    glossary_table.add_row(g.get("Display Name"), g.get("Description"), g.get("Qualified Name"))
                    continue

            # Digital Product Catalogs
            digital_product_catalog_table: DataTable = DataTable(id="digital_product_catalog_table")
            digital_product_catalog_table.add_columns("Digital Product Catalog Name", "Description", "Qualified Name")
            digital_product_catalog_table.cursor_type = "row"
            digital_product_catalog_table.zebra_stripes = True
            try:
                self.digital_product_catalog_data = exec_report_spec(format_set_name="Digital-Product-Catalog",
                                                                     output_format="DICT",
                                                                     params = {"search_string" : "*"},
                                                                     view_server=self.view_server,
                                                                     view_url=self.platform_url,
                                                                     user=self.user_name,
                                                                     user_pass=self.user_password)
            except PyegeriaException as e:
                self.log(f"Error retrieving digital product catalog details: {e!s}")
                self.exit(421)
                return(421)
            self.log(f"Digital Product Catalog data returned: {self.digital_product_catalog_data}")
            self.digital_product_catalog_data_extract = self.digital_product_catalog_data.get("data") or []
            self.log(f"Digital Product Catalog data extracted: {self.digital_product_catalog_data_extract}")
            if self.digital_product_catalog_data_extract == []:
                self.log(f"No digital product catalog data found for user: {self.user_name}")
                digital_product_catalog_table.add_row("No digital product catalogs found", "No data returned from Egeria", "")
            else:
                for catalog_item in self.digital_product_catalog_data_extract:
                    digital_product_catalog_table.add_row(catalog_item["Display Name"],
                                                          catalog_item["Description"],
                                                          catalog_item["Qualified Name"])
                    continue

            # Data Dictionaries
            data_dictionary_table: DataTable = DataTable(id="data_dictionary_table")
            data_dictionary_table.add_columns("Data Dictionary Name", "Description", "Qualified Name")
            data_dictionary_table.cursor_type = "row"
            data_dictionary_table.zebra_stripes = True
            try:
                self.data_dictionary_data = exec_report_spec(format_set_name="Data-Dictionaries",
                                                           output_format="DICT",
                                                           params = {"search_string" : "*"},
                                                           view_server=self.view_server,
                                                           view_url=self.platform_url,
                                                           user=self.user_name,
                                                           user_pass=self.user_password)
            except PyegeriaException as e:
                self.log(f"Error retrieving data dictionary details: {e!s}")
                self.exit(422)
                return(422)
            self.data_dictionary_data_extract = self.data_dictionary_data.get("data") or []
            if self.data_dictionary_data_extract == []:
                self.log(f"No data dictionary details found for user: {self.user_name}")
                data_dictionary_table.add_row("No data dictionaries found", "No data returned from Egeria", "")
            else:
                self.log(f"Found {self.data_dictionary_data_extract} data dictionaries for user {self.user_name}")
                data_dictionary_table.add_row("Display Name", "Description", "Qualified Name")
                for dictionary in self.data_dictionary_data_extract:
                    data_dictionary_table.add_row(dictionary.get("Display Name", ""),
                                                       dictionary.get("Description", ""),
                                                       dictionary.get("Qualified Name", ""))
                    continue

            # Business Domains
            business_domain_table: DataTable = DataTable(id="business_domain_table")
            business_domain_table.add_columns("Business Area Name", "Type Name", "GUID")
            business_domain_table.cursor_type = "row"
            business_domain_table.zebra_stripes = True
            try:
                self.business_domain_data = exec_report_spec(format_set_name="BusinessCapabilities",
                                                           output_format="DICT",
                                                           params = {"search_string" : "*"},
                                                           view_server=self.view_server,
                                                           view_url=self.platform_url,
                                                           user=self.user_name,
                                                           user_pass=self.user_password)
            except PyegeriaException as e:
                self.log(f"Error retrieving business domain details: {e!s}")
                self.exit(423)
                return(423)
            self.business_domain_data_extract = self.business_domain_data.get("data") or []
            if self.business_domain_data_extract == []:
                self.log(f"No business domains found for user {self.user_name}")
                business_domain_table.add_row("No business domains found", "No data returned from Egeria", "")
            else:
                self.log(f"Found {self.business_domain_data_extract} business domains for user {self.user_name}")
                # business_domain_table.add_row("Business Domain Name", "Description", "GUID")
                for domain in self.business_domain_data_extract:
                    business_domain_table.add_row(domain.get("Qualified Name", ""),
                                                       domain.get("Type Name", ""),
                                                       domain.get("GUID", ""))
                    continue

            # Data Specifications
            data_specification_table: DataTable = DataTable(id="data_specification_table")
            data_specification_table.add_columns("Display Name", "Description", "Qualified Name")
            data_specification_table.cursor_type = "row"
            data_specification_table.zebra_stripes = True
            try:
                self.data_specification_data = exec_report_spec(format_set_name="Data-Specifications",
                                                                 output_format="DICT",
                                                                 params = {"search_string": "*"},
                                                                 view_server=self.view_server,
                                                                 view_url=self.platform_url,
                                                                 user=self.user_name,
                                                                 user_pass=self.user_password)
            except PyegeriaException as e:
                self.log(f"Error retrieving data specification details: {e!s}")
                self.exit(423)
                return (423)

            if isinstance(self.data_specification_data, dict):
                self.data_specification_data_extract = self.data_specification_data.get("data")
            elif isinstance(self.data_specification_data, list):
                self.data_specification_data_extract = self.data_specification_data
            else:
                self.data_specification_data_extract = self.data_specification_data.get("Data-Specifications") or []

            if self.data_specification_data_extract == [] or self.data_specification_data_extract == {} or self.data_specification_data_extract == None:
                self.log(f"No data specifications found for user {self.user_name}")
                data_specification_table.add_row("No data specifications found", "No data returned from Egeria", "")
            else:
                self.log(f"Found {self.data_specification_data_extract} data specifications for user {self.user_name}")

                for spec in self.data_specification_data_extract:
                    data_specification_table.add_row(spec.get("Display Name", ""),
                                                  spec.get("Description", ""),
                                                  spec.get("Qualified Name", ""))
                    continue

            # hand the data to the Screen for displaying
            await self.push_screen(ShopForDataScreen(glossary_table, digital_product_catalog_table, data_dictionary_table, business_domain_table, data_specification_table ), callback = self.shop_for_data_callback)

        elif selected_option == "User Bookmarks":
            pass
        elif selected_option == "Subscriptions":
            pass
        else:
            pass

    async def tech_type_callback(self, result) -> int:
        """ Callback for Technology Types screen
             If the result is int (4xx) it indicates an error in the screen
             if the result is str it contains the GUID of the selected technology type
        """
        #clear local data fields
        tech_type_description = ""
        self.tech_type_data = {}
        self.tech_type_data_extracted = {}
        self.tech_type_templates = []
        self.tech_type_processes = []
        # check that we got a valid result from the screen
        if not result or isinstance(result, int) :
            self.log(f"Technology Types screen cancelled/failed; return: {result}, exiting.")
            self.exit(result)
            return (result)
        self.selected_t_node = str(result)
        self.log(f"Technology Types screen returned: {self.selected_t_node}")
        # Request details for selected tech type
        try:
            self.tech_type_data = exec_report_spec(format_set_name="Tech-Type-Details-MD",
                                                   output_format="DICT",
                                                   params={"search_string": self.selected_t_node, "filter_string": self.selected_t_node},
                                                   view_server=self.view_server,
                                                   view_url=self.platform_url,
                                                   user=self.user_name,
                                                   user_pass=self.user_password)
        except PyegeriaException as e:
            print_basic_exception(e)
            self.log(f"Error retrieving technology type details: {e!s}")
            self.exit(414)
            return (414)

        self.log(f"Technology Type Data: {self.tech_type_data}, type: {type(self.tech_type_data)}")

        if self.tech_type_data.get("kind") is not None:
            self.tech_type_data_extracted = self.tech_type_data.get("data")
        else:
            self.tech_type_data_extracted = {"Error": "No data found for this technology type."}

        self.log (f"Technology Type Data Extracted: {self.tech_type_data_extracted}")

        for dataset in self.tech_type_data_extracted:
            self.tech_type_guid = dataset.get("GUID")
            self.tech_type_name = dataset.get("Display Name")
            self.tech_type_templates = dataset.get("Catalog Templates")
            self.tech_type_processes = dataset.get("Governance Processes")
            self.tech_type_description = tech_type_description
            self.log(f"Technology Type GUID: {self.tech_type_guid}")
            self.log(f"Technology Type Name: {self.tech_type_name}")
            self.log(f"Technology Type Description: {self.tech_type_description}")
            self.log(f"Technology Type Templates: {self.tech_type_templates}" or [{"templates": "None"}])
            self.log(f"Technology Type Processes: {self.tech_type_processes}" or [{"processes": "None"}])

        await self.push_screen(TechnologyTypeOptionsScreen(self.tech_type_guid,
                                               self.tech_type_name,
                                               self.tech_type_description,
                                               self.user_name,
                                               self.user_password,
                                               self.karma_points,
                                               self.tech_type_templates,
                                               self.tech_type_processes), callback = self.tech_type_options_callback)
        return(200)

    async def tech_type_options_callback(self, result: list):
        self.log(f"Technology Type Options screen returned: {result}")
        if not result[0] or isinstance(result[0], int):
            if isinstance(result[0], int) and result[0] == 200:
                self.log("Technology Type Options screen returned successfully.")
                return(200)
            else:
                self.log(f"Technology Type Options screen cancelled/failed; return: {result}, exiting.")
                self.exit(415)
            self.log(f"Technology Type Options screen cancelled/failed; return: {result}, exiting.")
            self.exit(415)
            return

        self.selected_t_option = str(result[0])
        self.selected_t_option_selected = result[1]
        self.log(f"Technology Type Options screen returned: {self.selected_t_option} | {self.selected_t_option_selected}")

        # display the screen so the objects we need to mount to are created in the DOM
        # then we can build the display elements for the placeholder properties
        # and mount them in the appropriate containers on the screen
        if self.selected_t_option == "template":
            await self.push_screen(TechnologyTypeTemplatesScreen(self.user_name,
                                                             self.karma_points,
                                                             self.tech_type_name,
                                                             self.tech_type_description,
                                                             self.selected_t_option,
                                                             self.selected_t_option_selected,
                                                             self.tech_type_templates),
                                   callback=self.tech_type_templates_callback)
        elif self.selected_t_option == "process":
            await self.push_screen(TechnologyTypeProcessesScreen(self.user_name,
                                                             self.karma_points,
                                                             self.tech_type_name,
                                                             self.tech_type_description,
                                                             self.selected_t_option,
                                                             self.selected_t_option_selected,
                                                             self.tech_type_processes),
                                   callback=self.tech_type_processes_callback)
        else:
            self.log(f"Technology Type Options screen returned invalid option: {self.selected_t_option_selected}")
            self.exit(416)
        return(200)

    async def fetch_technology_types(self) -> int:
        self.tech_type_list: list = [{}]
        try:
            self.autoc = AutomatedCuration(self.view_server, self.platform_url, self.user_name, self.user_password)
            self.autoc.create_egeria_bearer_token(self.user_name, self.user_password)
            # retrieve the tech type data
            self.log(f"Fetching technology type hierarchy for tech_type='*'")
            self.tech_type_response = await self.autoc._async_get_tech_type_hierarchy(filter_string = "*" )
        except Exception as e:
            self.log(f"Exception in get_tech_type_hierarchy: {e}")
            self.log(print_basic_exception(e))
            self.tech_type_list = [{}]
            self.exit(416)
            return(416)

        self.log (f"tech_type_response: {self.tech_type_response}")
        # Copy the data into a working variable for the extraction routine
        self.tech_type_list = self.tech_type_response
        return(200)

    def unpack_egeria_data(self) -> int:
        """ Unpack the data returned from Egeria """
        output_data: list[dict] = [{}]
        output_data.clear()
        if isinstance(self.tech_type_data, dict):
            if "data" in self.tech_type_data:
                output_data = self.tech_type_data.get("data")
            else:
                output_data = [self.tech_type_data]
        elif isinstance(self.tech_type_data, list):
            for entry in self.tech_type_data:
                if isinstance(entry, dict):
                    output_data = entry.get("data")
                elif isinstance(entry, list):
                    for subentry in entry:
                        if isinstance(subentry, dict):
                            output_data = [subentry]
                        else:
                            self.log(f"error unknown data structure for Tech Type data")
                            return(417)
                else:
                    self.log(f"error unknown outer data structure for Tech Type data")
                    return (417)
        else:
            self.log(f"Tech Type data not dict or list")
            return(417)

        self.log(f"output_data: {output_data}, {type(output_data)}")
        # return the extracted data (dict)
        self.tech_type_list = output_data
        return (200)

    def tech_type_templates_callback(self, result):
        """ Callback for Technology Type Templates screen
            result contains up to 3 elements:
            [0] = return code or 'input', [1] input data, [2] full template"""
        # take the input data and use it in the form and
        # create from template
        self.log(f"Technology Type Templates screen returned: {result}")
        # Check for return code
        if isinstance(result, int):
            self.log(f"Technology Type Templates screen returned: {result}, exiting.")
            self.exit(result)
        # Check for unexpected return
        if not result or result[0] != "input":
            self.log(f"Technology Type Templates screen cancelled/failed; return: {result}, exiting.")
            self.exit(418)
            return

            # make the keys to the input data match the keys in the template structure
            # take each key and use the data value to replace the placeholder value in the template
            # then use the pyegeria create_metadata_element_from template to create the metadata element
            # finally display a status screen to confirm the creation of the metadata element

        # make a working version of the full template if it is returned
        if isinstance(result[2], dict):
            self.full_template = result[2]
        # create an empty dict for the returned data
        my_placeholderPropertyValues: dict = {}
        # load in the returned placeholder user data
        if isinstance(result[1], dict):
            self.placeholder_input = result[1]
        # clean up the keys of the user data to match the template keys
        if isinstance(self.placeholder_input, dict):
            # for each data input item in the dict
            for input_item, input_value in self.placeholder_input.items():
                self.log(f"input_item: {input_item}, input_value: {input_value}")
                input_fix1 = input_item.replace("_", " ")
                self.log(f"input_item after underscore removal: {input_fix1}")
                input_fix2 = input_fix1.replace(" placeholder input", "")
                self.log(f"input_item after placeholder removal: {input_fix2}")

                self.log(f"fixed input_item: {input_fix2}, {input_value}")
                # build the placeholderPropertyValues dict
                my_placeholderPropertyValues.update({input_fix2: input_value})
                continue
        else:
            self.log(f"placeholder_input is not a dict: {self.placeholder_input}")
            return(419)

        # create a dict structure that matches the template structure
        # we have the input data in my_placeholderPropertyValues and
        # the selected template in self.full_template
        # so we can use the pyegeria create_metadata_element_from template to create the metadata element
        # finally display a status screen to confirm the creation of the metadata element

        self.log(f"my_placeholderPropertyValues: {my_placeholderPropertyValues}")
        self.log(f"self.placeholder_input: {self.placeholder_input}")
        self.log(f"self.full_template: {self.full_template}")

        # copy the retrieved template into the request body
        request_body:dict = {
          "class" : "TemplateRequestBody",
          "externalSourceGUID" : self.full_template.get("externalSourceGUID") or "",
          "externalSourceName" : self.full_template.get("externalSourceName") or "",
          "typeName" : self.full_template.get("typeName") or "",
          "templateGUID" : self.full_template.get("Catalog Template GUID"),
          "anchorGUID" : self.full_template.get("anchorGUID"),
          "isOwnAnchor" : "false",
          "effectiveFrom" : "2026-01-01",
          "effectiveTo": "2030-12-31",
          "replacementProperties" : self.full_template.get("replacementProperties") or {},
          "placeholderPropertyValues" : {},
          "parentGUID" : None,
          "parentRelationshipTypeName" : None,
          "parentRelationshipProperties" : None,
          "parentAtEnd1" : self.full_template.get("parentAtEnd1") or True,
          "effectiveTime" : self.full_template.get("effectiveTime") or datetime.datetime.now().isoformat(),
        }
        self.log(f"request_body: {request_body}")
        # update the request body with the user provided input
        for key, value in my_placeholderPropertyValues.items():
            request_body["placeholderPropertyValues"].update({key: value})
            continue
        self.log(f"request_body after update: {request_body}")
        # now instantiate and call the function to create the element from the template
        try:
            tokendata = self.autoc.create_egeria_bearer_token(self.user_name, self.user_password)
            my_md_instance = MetadataExpert(self.view_server, self.platform_url, self.user_name, self.user_password, tokendata)
            # new_guid = my_md_instance.create_metadata_element_from_template(self.template_guid, body = request_body)
            new_guid = my_md_instance.create_metadata_element_from_template(body=request_body)
        except Exception as e:
            self.log(f"Exception in create_element_from_template: {e}")
            if isinstance(e, PyegeriaException):
                self.log(print_basic_exception(e))
            else:
                self.log(f"Exception in create_element_from_template: {e}")
            self.push_screen(StatusScreen(f"Error creating element from Template/n{print_basic_exception(e)}"), callback=self.status_callback)
            return(420)

        self.log(f"new_guid: {new_guid}")
        self.push_screen(StatusScreen(f"Element created from Template/Metadata element created with GUID: '{new_guid}'"), callback=self.status_callback)

    def status_callback(self, status_callback_rc) -> None:
        """ Callback routine from the status screen,
            this screen is typically displayed at the end of a process
            to indicate success or failure of the process."""

        self.log(f"Status screen returned: {status_callback_rc}")
        self.exit(status_callback_rc)

    def tech_type_processes_callback(self, result):
        """ Callback for Technology Type Processes screen"""
        # take the input data and use it to run the command/process
        pass

    def shop_for_data_callback(self, result):
        """ Callback for Shop For Data screen"""
        selection_type = result[0]
        selection_parm_1 = result[1]
        selection_parm_2 = result[2]

        if isinstance(selection_type, int):
            if selection_type == 200:
                return(200)
            else:
                self.log(f"Shop For Data screen returned: {selection_type}, exiting.")
                self.exit(selection_type)

        if selection_type == "dictionary":
            self.log(f"Selected dictionary with qualified name: {selection_parm_1}")
            self.build_dictionary_details(selection_parm_1, selection_parm_2)
        elif selection_type == "domain":
            self.log(f"Selected business domain with qualified name: {selection_parm_1}")
            self.build_domain_details(selection_parm_1, selection_parm_2)
        elif selection_type == "catalog":
            self.log(f"Selected catalog with qualified name: {selection_parm_1}")
            self.build_catalog_details(selection_parm_1, selection_parm_2)
        elif selection_type == "glossary":
            self.log(f"Selected glossary with qualified name: {selection_parm_2}")
            self.build_glossary_details(selection_parm_1, selection_parm_2)
        elif selection_type == "specification":
            self.log(f"Selected data specification with qualified name: {selection_parm_2}")
            self.build_data_specification_details(selection_parm_1, selection_parm_2)
        else:
            self.log(f"Unknown selection type: {selection_type}")
            self.exit(429)

    def build_dictionary_details(self, target_qualified_name, target_display_name):
        """ Build the details object for a dictionary details screen"""
        self.log(f"Building dictionary details for qualified name: {target_qualified_name}")
        self.dictionary_qualified_name = target_qualified_name
        self.dictionary_display_name = target_display_name
        build_structure = {}

        try:
            self.dictionary_details = exec_report_spec(format_set_name="Data-Dictionaries",
                                                  output_format="DICT",
                                                  params={"search_string": self.dictionary_qualified_name, "filter_string": self.dictionary_qualified_name},
                                                  view_server=self.view_server,
                                                  view_url=self.platform_url,
                                                  user=self.user_name,
                                                  user_pass=self.user_password)
        except PyegeriaException as e:
            print_basic_exception(e)
            self.log(f"Error retrieving dictionary details: {e!s}")
            self.exit(420)
            return (420)
        self.log(f"Dictionary Details: {self.dictionary_details}")
        if not self.dictionary_details or self.dictionary_details == None:
            error_category = "Dictionary Details"
            error_message = "No dictionary details found"
            self.log(f"Error retrieving dictionary details: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
        elif self.dictionary_details.get("kind") == "empty":
            dictionary_tree: Tree = Tree(label="Empty Dictionary", id="data_dictionary_tree")
            dictionary_tree.root.expand()
            dictionary_tree.root.content = "No dictionary terms found for this dictionary"
        else:
            dictionary_tree: Tree = Tree(label=self.dictionary_display_name, id="data_dictionary_tree")
            dictionary_tree.root.expand()
            dictionary_tree.auto_expand = True
            self.dictionary_details_data = self.dictionary_details.get("data")
            for term in self.dictionary_details_data:
                term_qualified_name = term.get("Qualified Name") or ""
                term_subject = term.get("Subject Area") or ""
                term_summary = term.get("Summary") or ""
                # create dict structure for loading the tree
                build_structure.update({term_subject: [{term_qualified_name: term_summary}]})
                continue
            # Once the structure is complete we can build the tree from it
            for term_subject in build_structure:
                dictionary_branch = dictionary_tree.root.add(term_subject, id=term_subject)
                for term_qualified_name, term_summary in build_structure[term_subject]:
                    dictionary_branch.add_leaf(term_summary, data=term_qualified_name)
                dictionary_tree.root.expand()
        self.push_screen(SelectionOverviewScreen("dictionary",
                                                 self.view_server,
                                                 self.platform_url,
                                                 self.user_name,
                                                 self.user_password,
                                                 data_tree=dictionary_tree), callback=self.overview_callback)

    def build_domain_details(self, target_qualified_name, target_type__name):
        """ Build the details object for a business domain details screen"""
        self.log(f"Building domain details for qualified name: {target_qualified_name}")
        self.domain_qualified_name = target_qualified_name
        self.domain_type__name = target_type__name
        build_structure = {}

        try:
            self.domain_details = exec_report_spec(format_set_name="BusinessCapabilities",
                                                  output_format="DICT",
                                                  params={"search_string": self.domain_qualified_name, "filter_string": self.domain_qualified_name},
                                                  view_server=self.view_server,
                                                  view_url=self.platform_url,
                                                  user=self.user_name,
                                                  user_pass=self.user_password)
        except PyegeriaException as e:
            print_basic_exception(e)
            self.log(f"Error retrieving business domain details: {e!s}")
            self.exit(420)
            return (420)
        self.log(f"domain_details: {self.domain_details}")
        if not self.domain_details or self.domain_details == None:
            error_category = "Business Domain Details"
            error_message = "No domain details found"
            self.log(f"Error retrieving business domain details: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
        elif self.domain_details.get("kind") == "empty":
            domain_tree: Tree = Tree(label="Empty Business Domain", id="business_domain_tree")
            domain_tree.root.expand()
            domain_tree.root.content = "No domain details found for this business domain"
        else:
            self.domain_details_data = self.domain_details.get("data")
            self.log(f"domain_details_data: {self.domain_details_data}")
            self.domain_display_name = self.domain_details_data.get("Qualified Name")
            domain_tree: Tree = Tree(label=self.domain_display_name, id="business_domain_tree")
            domain_tree.root.expand()
            domain_tree.auto_expand = True
            for term in self.domain_details_data:
                if term == None:
                    continue
                term_qualified_name = term.get("Qualified Name") or ""
                term_type = term.get("Type Name") or ""
                term_GUID = term.get("GUID") or ""
                term_members = term.get("Containing Members")
                term_memberof = term.get("Member Of")
                # create dict structure for loading the tree
                build_structure.update({term_qualified_name: [{"term_type": term_type}, {"term_GUID": term_GUID}, {"term_members": term_members},{"term_memberof": term_memberof}]})
                continue
            # Once the structure is complete we can build the tree from it
            for qualified_name in build_structure:
                domain_branch = domain_tree.root.add(qualified_name, id=qualified_name, data=[qualified_name.get("term_type"), qualified_name.get("term_GUID")])
                if build_structure[qualified_name]["term_members"] != None:
                    domain_branch_members = domain_branch.add("Containing Members")
                    for member in build_structure[qualified_name]["term_members"]:
                        domain_branch_members.add_leaf(member)
                if build_structure[qualified_name]["term_memberof"] != None:
                    for member in build_structure[qualified_name]["term_memberof"]:
                        domain_branch.add_leaf(member)
                domain_tree.root.expand()

        self.push_screen(SelectionOverviewScreen("domain",
                                                 self.view_server,
                                                 self.platform_url,
                                                 self.user_name,
                                                 self.user_password,
                                                 data_tree=domain_tree), callback=self.overview_callback)

    def build_catalog_details(self, target_qualified_name, target_display_name):
        """ Build the details object for a catalog details screen"""
        self.log(f"Building catalog details for qualified name: {target_qualified_name}")
        self.catalog_qualified_name = target_qualified_name
        self.catalog_display_name = target_display_name
        build_structure = {}

        try:
            self.catalog_details = exec_report_spec(format_set_name="Digital-Product-Catalog",
                                                  output_format="DICT",
                                                  params={"search_string": self.catalog_qualified_name, "filter_string": self.catalog_qualified_name},
                                                  view_server=self.view_server,
                                                  view_url=self.platform_url,
                                                  user=self.user_name,
                                                  user_pass=self.user_password)
        except PyegeriaException as e:
            print_basic_exception(e)
            self.log(f"Error retrieving catalog details: {e!s}")
            self.exit(420)
            return (420)
        self.log(f"catalog_details: {self.catalog_details}")
        if not self.catalog_details or self.catalog_details == None:
            error_category = "Catalog Details"
            error_message = "No catalog details found"
            self.log(f"Error retrieving catalog details: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
        elif self.catalog_details.get("kind") == "empty":
            catalog_tree: Tree = Tree(label="Empty Catalog", id="digital_product_catalog_tree")
            catalog_tree.root.expand()
            catalog_tree.root.content = "No catalog terms found for this catalog"
        else:
            catalog_tree: Tree = Tree(label=self.catalog_display_name, id="digital_product_catalog_tree")
            catalog_tree.root.expand()
            catalog_tree.auto_expand = True
            self.catalog_details_data = self.catalog_details.get("data")

            if not self.catalog_details_data or self.catalog_details_data == None:
                error_category = "Catalog Details"
                error_message = "No catalog details found or the data dict entry is missing"
                self.log(f"Error retrieving catalog details: {error_category}, {error_message}")
                self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
                return

            for term in self.catalog_details_data:
                term_qualified_name = term.get("Qualified Name") or ""
                term_subject = term.get("Subject Area") or ""
                term_summary = term.get("Summary") or ""
                # create dict structure for loading the tree
                build_structure.update({term_subject: [{term_qualified_name: term_summary}]})
                continue
            # Once the structure is complete we can build the tree from it
            for term_subject in build_structure:
                catalog_branch = catalog_tree.root.add(term_subject, id=term_subject)
                for term_qualified_name, term_summary in build_structure[term_subject]:
                    catalog_branch.add_leaf(term_summary, data=term_qualified_name)
                catalog_tree.root.expand()
        self.push_screen(SelectionOverviewScreen("catalog",
                                                 self.view_server,
                                                 self.platform_url,
                                                 self.user_name,
                                                 self.user_password,
                                                 data_tree=catalog_tree), callback=self.overview_callback)

    def build_glossary_details(self, target_qualified_name, target_display_name):
        """ Build the details object for a glossary details screen"""
        self.log(f"Building glossary details for qualified name: {target_qualified_name}")
        self.glossary_qualified_name = target_qualified_name
        self.glossary_display_name = target_display_name
        
        for glossary_instance in self.glossary_data_extract:
            if glossary_instance.get("Qualified Name") == target_qualified_name:
                self.glossary_folders = glossary_instance.get("Folders") or None
                self.log(f"glossary_folders: {self.glossary_folders}")
                category = "Uncategorised"
                if self.glossary_folders != None:
                    glossary_tree: Tree = Tree(label=self.glossary_display_name, id="glossary_details_tree")
                    glossary_tree.root.expand()
                    glossary_tree.auto_expand = True
                    
                    folder_entries = [f.strip() for f in self.glossary_folders.split(',')]
                    nodes = {(): glossary_tree.root}
                    prefixes = ["GlossaryCategory", "GlossaryTerm", "CollectionFolder"]

                    for entry in folder_entries:
                        parts = entry.split('::')
                        if len(parts) == 1:
                            parts = entry.split('/')
                        
                        is_leaf = False
                        path_parts = []
                        full_id = ""
                        if any(parts[0].startswith(p) for p in prefixes):
                            type_prefix = parts[0]
                            path_parts = parts[1:]
                            is_leaf = "Term" in type_prefix
                            if is_leaf:
                                full_id = path_parts[-1] 
                        else:
                            path_parts = parts
                            
                        current_path = ()
                        for i, part in enumerate(path_parts):
                            parent_path = current_path
                            current_path = current_path + (part,)
                            
                            if current_path not in nodes:
                                parent_node = nodes[parent_path]
                                if is_leaf and i == len(path_parts) - 1:
                                    nodes[current_path] = parent_node.add_leaf(part, data=full_id)
                                else:
                                    new_node = parent_node.add(part, data=part)
                                    new_node.expand()
                                    nodes[current_path] = new_node
                                    
                    glossary_tree.refresh()
                else:
                    self.log(f"No glossary folders found in the glossary data extract")
                    folder_category = "Empty Glossary"
                    category = glossary_tree.root.add(folder_category)
                    folder_term = "No glossary terms found for this glossary"
                    category.add_leaf(folder_term)

        self.push_screen(SelectionOverviewScreen("glossary",
                                                 self.view_server,
                                                 self.platform_url,
                                                 self.user_name,
                                                 self.user_password,
                                                 data_tree=glossary_tree), callback=self.overview_callback)

    def build_data_specification_details(self, target_qualified_name, target_display_name):
        """ Build the details object for a data specification details screen"""
        self.log(f"Building data specification details for qualified name: {target_qualified_name}")
        self.data_specification_qualified_name = target_qualified_name
        self.data_specification_display_name = target_display_name

        try:
            self.data_specification_details = exec_report_spec(format_set_name="Data-Specifications",
                                                  output_format="JSON",
                                                  params={"search_string": self.data_specification_qualified_name, "filter_string": self.data_specification_qualified_name},
                                                  view_server=self.view_server,
                                                               view_url=self.platform_url,
                                                               user=self.user_name,
                                                               user_pass=self.user_password)
        except Exception as e:
            self.log(f"Error retrieving data specification details: {e}")
            return
        self.log(f"data_specification_details: {self.data_specification_details}")
        if not self.data_specification_details or self.data_specification_details == None or self.data_specification_details.get("kind") == "empty":
            self.log(f"No data specification details found for qualified name: {self.data_specification_qualified_name}")
            error_category = "Data Specification Details"
            error_message = "No data specification details found"
            self.log(f"Error retrieving data specification details: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
            return

        self.log(f"Data specification details retrieved successfully for qualified name: {self.data_specification_qualified_name}")
        self.log(f"Data specification details: {self.data_specification_details}")

        data_spec_tree: Tree = Tree(label=self.data_specification_display_name, id="data_specification_tree")
        data_spec_tree.root.expand()
        data_spec_tree.auto_expand = True
        self.data_specification_details_data = self.data_specification_details.get("data")
        self.log(f"Data specification details data: {self.data_specification_details_data}")

        if not self.data_specification_details_data or self.data_specification_details_data == None:
            error_category = "Data Specification Details"
            error_message = "No data specification details found or the data dict entry is missing"
            self.log(f"Error retrieving data specification details: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
            return

        specified_id = 0
        for spec in self.data_specification_details_data:
            spec_qualified_name = spec.get("properties", {}).get("qualifiedName") or ""
            spec_type = spec.get("properties", {}).get("typeName") or ""
            spec_description = spec.get("properties", {}).get("description") or ""
            spec_url = spec.get("properties", {}).get("URL") or ""
            spec_display_name = spec.get("properties", {}).get("displayName") or ""
            spec_fixed_label = spec_display_name.replace(" ", "")
            spec_fixed_label = spec_fixed_label.replace(":", "")
            self.log(f"Creating tree node for spec: {spec_fixed_label}, with id: {"id"+str(specified_id)}")
            spec_branch = data_spec_tree.root.add(spec_fixed_label, id="id"+str(specified_id), data=[(spec_display_name, spec_qualified_name, spec_type, spec_description, spec_url)])
            spec_branch.expand()
            data_spec_tree.root.expand()
            specified_id +=1
        self.push_screen(SelectionOverviewScreen("specification",
                                                 self.view_server,
                                                 self.platform_url,
                                                 self.user_name,
                                                 self.user_password,
                                                 data_tree=data_spec_tree), callback=self.overview_callback)

    def overview_callback(self, r_code):
        """Callback function for handling overview screen actions."""
        if r_code == 410:
            error_category = "Collection Category"
            error_message = "Unknown collection category returned"
            self.log(f"Error in selection overview processing: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
        elif r_code == 411:
            error_category = "Glossary"
            error_message = "query_one no matches found for glossary tree"
            self.log(f"Error in selection overview processing: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
        elif r_code == 412:
            error_category = "Digital Product Catalog"
            error_message = "query_one no matches found for digital product catalog tree"
            self.log(f"Error in selection overview processing: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
        elif r_code == 413:
            error_category = "Data Dictionary"
            error_message = "query_one no matches found for data dictionary tree"
            self.log(f"Error in selection overview processing: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
        elif r_code == 414:
            error_category = "Business Domain"
            error_message = "query_one no matches fround for business domain tree"
            self.log(f"Error in selection overview processing: {error_category}, {error_message}")
        elif r_code == 415:
            error_category = "Data Specification"
            error_message = "query_one no matches found for data specification tree"
            self.log(f"Error in selection overview processing: {error_category}, {error_message}")
        else:
            # good return from overview screen
            self.log (f"Overview screen callback, return code : {r_code}")
            # add more code here
            pass

    def extract_glossary_terms(self, text):
        """
        Extracts GlossaryTerm items from a string structure.
        Pattern: Starts with 'GlossaryTerm::', ends at the next ','.
        """
        # Pattern explanation:
        # GlossaryTerm::  - Matches the literal prefix
        # ([^,\']+)       - Captures one or more characters that are NOT a comma or a single quote
        pattern = r"GlossaryTerm::([^,\']+)"

        # Find all matches in the text
        matches = re.findall(pattern, text)

        self.log(f"Extracted {len(matches)} GlossaryTerm items from text")

        # Clean up whitespace and return as a list
        return [match.strip() for match in matches]

    def display_glossary_term_details(self, term):
        """ Displays the details of a GlossaryTerm item"""
        self.target_term = term
        try:
            self.term_details = exec_report_spec(format_set_name="Glossary-Terms",
                                                  output_format="JSON",
                                                  params={"search_string": self.target_term, "filter_string": self.target_term},
                                                  view_server=self.view_server,
                                                  view_url=self.platform_url,
                                                  user=self.user_name,
                                                  user_pass=self.user_password)
        except PyegeriaException as e:
            print_basic_exception(e)
            self.log(f"Error retrieving term details: {e!s}")
            self.exit(440)
            return (440)

        self.log(f"term_details: {self.term_details}")
        if not self.term_details or self.term_details == None:
            error_category = "Glossary Term Details"
            error_message = "No glossary term details found"
            self.log(f"Error retrieving glossary term details: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
        elif self.term_details.get("kind") == "empty":
            self.log(f"No glossary term details found for qualified name: {self.target_term}")
            error_category = "Glossary Term Details"
            error_message = "No glossary term details found"
            self.log(f"Error retrieving glossary term details: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)

        self.term_details_data = self.term_details.get("data")

        if not self.term_details_data or self.term_details_data == None:
            error_category = "Glossary Term Details"
            error_message = "No glossary term details found or the data dict entry is missing"
            self.log(f"Error retrieving glossary term details: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
        else:
            self.term_details_container: ScrollableContainer = self.screen.query_one(DataTable)
            self.term_details_container.mount()
            for data_item_key, data_item_value in self.term_details_data.items():
                Static(f"Field: {data_item_key}, Value: {data_item_value}").mount(self.term_details_container)
                continue
        # Once all the fields are complete we can leave it to the screen processing to handle the rest
        return (200)

    @on(DataTable.RowSelected, "#roles_table")
    def handle_roles_table_row_selection(self, event):
        role_table = event.data_table
        selected_row_key = event.row_key
        selected_row_data = role_table.get_row(selected_row_key)
        selected_role_guid = selected_row_data[2]
        selected_role_name = selected_row_data[0]
        selected_role_type = selected_row_data[1]
        self.log(f"Selected role: {selected_row_data}")
        team_members_list: list = []
        self.team_members = []

        # provide list of team members for team leader
        if "TeamLeader" in selected_role_name or "TeamLeader" in selected_role_type:
            self.log(f"Selected role is a TeamLeader: {selected_role_name}")
            team_members_list, team_display_name, team_qualified_name, team_category, team_description = self.find_team_members(selected_role_name)
        elif "TeamMembers" in selected_role_name or "TeamMembers" in selected_role_type:
            self.log(f"Selected role is a TeamMember: {selected_role_name}")
            team_members_list, team_display_name, team_qualified_name, team_category, team_description = self.find_team_members(selected_role_name)
        else:
            self.log(f"Selected role is not a TeamLeader or TeamMember: {selected_role_name}")
            return (201)

        self.log(f"team_members_list: {team_members_list}")
        # Process team data for display on screen
        team_member_properties: list = []
        team_properties: list = []
        team_properties.append(team_display_name)
        team_properties.append(team_qualified_name)
        team_properties.append(team_category)
        team_properties.append(team_description)
        self.log(f"team_properties: {team_properties}")
        # Process team member data for display on screen
        for team_member in team_members_list:
            if isinstance(team_member, list) and "Selection Error" in team_member[0]:
                self.log(f"Team member details contain 'Selection Error': {team_member}")
                self.team_members.append(team_member)
                break
            else:
                self.log(f"Processing team member properties: {team_member}")
                team_member_properties = []
                team_member_properties.append(team_member.get("Individual"))
                team_member_properties.append(team_member.get("Assignment Type"))
                team_member_properties.append(team_member.get("Individual GUID"))
                self.log(f"team_member_properties: {team_member_properties}")
                self.team_members.append(team_member_properties)
                self.log(f"team_members: {self.team_members}")
                continue
        self.log(f"team_members: {self.team_members}")
        self.log(f"team_properties: {team_properties}")
        self.log(f"User name: {self.user_name}")
        self.push_screen(MyTeam(self.team_members, team_properties, self.user_name), callback=self.my_team_callback)

    def find_team_members(self, role_name):
        # common routine for finding team members given a role name
        # extract the Department::nnn from the name to use as the search key
        selected_role_name = role_name
        team_members_list: list = []
        self.team_members = []

        search_key_parts = selected_role_name.split("::")
        role_search_key = '::'.join(search_key_parts[1:])
        self.log(f"Role search key: {role_search_key}")
        # get the team member details for that department
        team_member_data: dict = exec_report_spec(format_set_name="Team-Members",
                                                  output_format="DICT",
                                                  params={"search_string": role_search_key},
                                                  view_server=self.view_server,
                                                  view_url=self.platform_url,
                                                  user=self.user_name,
                                                  user_pass=self.user_password)
        self.log(f"team_member_data: {team_member_data}")
        # team members?
        if team_member_data.get("kind") != "empty":
            team_members_data_struct: list[dict] = team_member_data.get("data")
            self.log(f"team members data extracted: {team_members_data_struct}")
        else:
            self.log(f"No team members found for role: {role_search_key}")
            error_category = "Team Members"
            error_message = "No team members found"
            self.log(f"Error retrieving team members: {error_category}, {error_message}")
            self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
            return
        team_members_list.clear()
        for team_member in team_members_data_struct:
            # get team details
            team_display_name: str = team_member.get("Display Name", None)
            team_qualified_name: str = team_member.get("Qualified Name", None)
            team_category: str = team_member.get("Category", None)
            team_description: str = team_member.get("Description", None)
            # extract the team member entries
            team_member_structure: list[dict] = team_member.get("Members", None)

            if team_member_structure != None:
                for entry in team_member_structure:
                    team_members_list.append(entry)

                    # if this is for a team leader then:
                    # get team members profile for contact information and contribution record (karma points)

                    # if "TeamLeader" in selected_role_name:
                    #     member_guid = entry.get("Individual GUID", None)
                    #

                    continue
                return(team_members_list, team_display_name, team_qualified_name, team_category, team_description)
            else:
                error_category = "Team Member Details"
                error_message = "No team member details found"
                self.log(f"Error retrieving team member details: {error_category}, {error_message}")
                self.push_screen(StatusScreen(f"{error_category}: {error_message}"), callback=self.status_callback)
                return (430)

    def my_team_callback(self, status) -> None:
        self.log(f"Callback received with status: {status}")
        if status == 200:
            self.log("MyTeam screen completed successfully")
        else:
            self.log(f"Error in MyTeam screen: {status}")
        self.push_screen("main")


if __name__ == "__main__":
    app = MyProfileApp()
    app.run()