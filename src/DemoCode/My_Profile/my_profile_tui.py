"""
   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a set of report specification related functions for my_egeria.

"""
from __future__ import annotations

import json
import os
from typing import Any

from pyegeria import PyegeriaException, print_basic_exception, AutomatedCuration
from pyegeria.omvs.my_profile import MyProfile
from pyegeria.view.format_set_executor import exec_report_spec
from pyegeria import AutomatedCuration as autocuration
from pyegeria import load_app_config, settings, config_logging

from textual.widgets._tree import TreeNode
from textual import on
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Container
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Static, Tree, OptionList,
)
from textual.widgets._option_list import Option

class TechnologyTypeOptions(ModalScreen[int]):
    """ Modal screen to display a technology type's templates and processes."""
    BINDINGS = [("q", "dismiss(200)", "Quit"),
                ("ctl+s", "Select", "tech_type_option_select")]

    CSS_PATH = "my_profile.tcss"

    def __init__(self, tech_type_guid: str, tech_type_name: str, tech_type_description: str, tech_type_templates: list[dict], tech_type_processes: list[dict]):
        """Initialize the TechnologyTypeOptions screen with a technology type's templates and processes."""
        super().__init__()
        self.tech_type_guid = tech_type_guid
        self.tech_type_name = tech_type_name
        self.tech_type_description = tech_type_description
        self.tech_type_templates = tech_type_templates
        self.tech_type_processes = tech_type_processes
        self.selected_template_guid = None
        self.selected_process_guid = None
        self.option_type_selected = None
        load_app_config("config/config.json")
        app_config = settings.Environment
        app_user = settings.User_Profile
        # config_logging()
        # print("Platform:", app_config.egeria_platform_url)
        # print("View Server:", app_config.egeria_view_server)
        self.user_name = app_user.user_name or "garygeeke"
        self.user_password = app_user.user_pwd or "secret"

    def compose(self) -> ComposeResult:
        """ Create OptionLists for any templates or processes provided"""
        if self.tech_type_templates:
            for t in self.tech_type_templates:
                try:
                    self.log(f"Template: {t}")
                    self.query_one("#template_options", OptionList).add_option(Option(t.get("Display Name"), data=t.get("GUID")))
                except Exception as e:
                    self.log(f"Error creating template option list: {e}")
                    continue
        elif self.tech_type_processes:
            for p in self.tech_type_processes:
                try:
                    self.log(f"Process: {p}")
                    self.query_one("#process_options", OptionList).add_option(Option(p.get("Display Name"), data=p.get("GUID")))
                except Exception as e:
                    self.log(f"Error creating process option list: {e}")
                    continue
        """ Compose the UI components for the TechnologyTypeOptions screen."""
        yield Header()
        yield Footer()
        yield ScrollableContainer(
            Static(f"Technology Type: {self.tech_type_name}"),
            Static(f"Description: {self.tech_type_description}"),
            id="tech_type_details")
        yield ScrollableContainer(
            Static(f"Templates: {len(self.tech_type_templates)}"),
            Static(f"Processes: {len(self.tech_type_processes)}"),
            Container(
                Static("Select a template or process to continue.")),
                ScrollableContainer(
                    OptionList(id="template_options"),
                    id="template_options_container"),
                ScrollableContainer(
                    OptionList(id="process_options"),
                    id="process_options_container"))

    def on_mount(self) -> None:
        """Mount the TechnologyTypeOptions screen."""
        self.title =  f"User: {self.user_name}, Karma Points: {self.user_karma_points}"
        self.subtitle = f"Technology Type: {self.tech_type_name}, Description: {self.tech_type_description}"
        self.log(f"Technology Type: {self.tech_type_name}, Description: {self.tech_type_description}")

    def action_tech_type_option_select(self) -> None:
        """Handle the selection of a template or process from the template or process option lists."""
        if self.option_type_selected == "template_options":
            pass
        elif self.option_type_selected == "process_options":
            pass
        else:
            self.log(f"Unknown option list: {self.option_type_selected}")
            pass
        return

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle the selection of an option from the template or process option lists."""
        self.log(f"Option selected: {event.option}")
        self.option_type_selected = event.option.id
        if event.option.id == "template_options":
            self.selected_template_guid = event.option.data
        elif event.option.id == "process_options":
            self.selected_process_guid = event.option.data
        else:
            self.log(f"Unknown option list: {event.option.id}")
            pass
        return

class TechnologyTypes(ModalScreen[Any]):
    """Modal screen to display technology types in Egeria."""
    BINDINGS = [("q", "dismiss(200)", "Quit"),
                ("ctl+e", "expand", "Toggle Twisties")]

    CSS_PATH = "my_profile.tcss"

    def __init__(self, ttlist: list[dict]):
        """Initialize the TechnologyTypes screen with a list of technology types."""
        super().__init__()
        self.tech_type_list = ttlist
        self.tech_type_tree: Tree[str] = Tree(label="Technology Types", id="technology_types_tree")
        self.tech_type_tree.root.expand()
        self.tech_type_tree.auto_expand = True
        self.selected_t_node = None
        self.selected_t_node_label = None
        self.node_id = None
        self.node_status = "expanded"
        load_app_config()
        app_config = settings.Environment
        app_user = settings.User_Profile
        # config_logging()
        self.user_name = app_user.user_name or "garygeeke"
        self.user_password = app_user.user_pwd or "secret"

    def on_mount(self) -> None:
        self.title = f"User: {self.user_name}"
        self.subtitle = "Select a technology type"

    def compose(self) -> ComposeResult:
        """ Compose and display the technology type screen"""
        self.tech_type_tree.refresh()
        if self.tech_type_list:
            self.log(f"Technology types: {self.tech_type_list}, type: {type(self.tech_type_list)}")
            self.render_tech_type_hierarchy_to_tree(self.tech_type_list, self.tech_type_tree)
        else:
            self.tech_type_tree.root.add("No technology types found", expand=True)
        self.tech_type_tree.refresh()
        self.log(f"Technology types tree: {self.tech_type_tree}")

        yield Header()
        yield ScrollableContainer(
            Static("Display technology types in Egeria"),
            self.tech_type_tree,
            Button("Select", id="select_tech_type_btn"),
            id="technology_types_table"
        )
        yield Footer()

    def action_quit(self) -> None:
        """ The quit option in the footer has been selected. Dismiss the screen."""
        self.dismiss("200")

    @on(Button.Pressed, "#select_tech_type_btn")
    def handle_select_tech_type(self, event: Button.Pressed) -> str|None:
        """ The select button on the screen has been pressed."""
        self.log(f"Select button pressed, button: {event.button}")
        if self.selected_t_node:
            self.log(f"Selected node: {self.selected_t_node}, label: {self.selected_t_node.label}")
            self.dismiss(str(self.selected_t_node.label))
        else:
            return "No technology type selected"

    @on(Tree.NodeSelected)
    def handle_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """ The user has selected a node in the tree. """
        self.log(f"Tree node selected, node: {event.node}")
        self.selected_t_node = event.node
        self.selected_t_node_label = event.node.label
        return

    @on(Tree.NodeCollapsed)
    def handle_tree_node_collapsed(self, event: Tree.NodeCollapsed) -> None:
        # handle the twisty to close a node in the tree
        # logger.debug(f"TreeNodeCollapsed: {event.node.id}")
        self.node_id = str(event.node.id)
        self.node_status = "collapsed"

    @on(Tree.NodeExpanded)
    def handle_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        # handle the twisty to open a node in the tree
        # logger.debug(f"TreeNodeExpanded: {event.node.id}")
        self.node_id = str(event.node.id)
        self.node_status = "expanded"

    def action_expand(self):
        # handle the hot key to expand/collapse all nodes in the tree (see bindings)
        self.tech_type_tree = self.query_one("#technology_types_tree", Tree)
        if self.node_status == "collapsed":
            self.tech_type_tree.root.expand_all()
        else:
            self.tech_type_tree.root.collapse_all()
        return

    def render_tech_type_hierarchy_to_tree(self,
            data: dict | list[dict],
            tree_or_node: Tree[str] | TreeNode[str],
            label_attr: str = "displayName",
            guid_attr: str = "guid",
            children_attr: str = "children"
    ) -> None:
        """Recursively render a JSON hierarchy into a Textual Tree.

        Args:
            data: The JSON structure from pyegeria.get_tech_type_hierarchy.
            tree_or_node: The Tree object or a TreeNode to add children to.
            label_attr: The attribute in the JSON for the node label.
            guid_attr: The attribute in the JSON for the node data (GUID).
            children_attr: The attribute in the JSON containing the list of children.
        """
        if isinstance(data, list):
            for item in data:
                self.render_tech_type_hierarchy_to_tree(item, tree_or_node, label_attr, guid_attr, children_attr)
            return

        if not isinstance(data, dict):
            return

        label = str(data.get(label_attr) or data.get("Display Name") or "Unknown")
        guid = str(data.get(guid_attr) or data.get("GUID") or "")

        # If it's a Tree, we add to root. If it's a TreeNode, we add to it.
        if isinstance(tree_or_node, Tree):
            node = tree_or_node.root.add(label, data=guid, expand=True)
        else:
            node = tree_or_node.add(label, data=guid, expand=True)

        children = data.get(children_attr)
        if children and isinstance(children, list):
            for child in children:
                self.render_tech_type_hierarchy_to_tree(child, node, label_attr, guid_attr, children_attr)



class CreateProfileScreen(ModalScreen[int]):
    """Modal screen to create a new user profile in Egeria.

    Dismisses with:
      200 on success
      400 on failure
    """

    BINDINGS = [("q", "dismiss(200)", "Quit")]
    CSS_PATH = "my_profile.tcss"

    def __init__(self):
        super().__init__()
        self.view_server = os.getenv("EGERIA_VIEW_SERVER", "qs-view-server")
        self.user_name = os.getenv("EGERIA_USER", "garygeeke")
        self.user_password = os.getenv("EGERIA_PASSWORD", "secret")
        self.platform_url = os.getenv("EGERIA_PLATFORM_URL", "https://127.0.0.1:9443")
        load_app_config()
        app_config = settings.Environment
        app_user = settings.User_Profile
        # config_logging()
        print("Platform:", app_config.egeria_platform_url)
        print("View Server:", app_config.egeria_view_server)
        self.user_name = app_user.user_name or "garygeeke"
        self.user_password = app_user.user_pwd or "secret"

    def on_mount(self) -> None:
        self.title = f"User: {self.user_name}, Karma Points: {self.user_karma_points}"
        self.subtitle = f"Technology Type: {self.tech_type_name}, Description: {self.tech_type_description}"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Create a new profile in Egeria")
        yield ScrollableContainer(
            Static("Fill in your information below:"),
            Input(placeholder="Courtesy Title", id="user_title"),
            Input(placeholder="Given Names", id="user_given_names"),
            Input(placeholder="Family Name", id="user_family_name"),
            Input(placeholder="Preferred Name", id="user_preferred_name"),
            Input(placeholder="Pronouns", id="user_pronouns"),
            Input(placeholder="Job Title", id="user_job_title"),
            Input(placeholder="Description", id="user_description"),
            Input(placeholder="Employee ID", id="user_employee_id"),
            Input(placeholder="Preferred Language", id="user_preferred_language"),
            Input(placeholder="Resident Country", id="user_resident_country"),
            Input(placeholder="Time Zone", id="user_time_zone"),
            Button("Create Profile", id="create_profile_btn"),
            id="create_profile_form",
        )

        yield Footer()

    @on(Button.Pressed, "#create_profile_btn")
    def create_profile(self) -> int:
        """Create a new profile in Egeria from data provided in Input fields."""

        self.new_element_request_body:dict = {"class": "NewElementRequestBody",
                                              "isOwnAnchor": True,
                                              "properties": {
                                                  "class": "PersonProperties",
                                                  "qualifiedName": "Person" + self.query_one("#user_employee_id",
                                                                                             Input).value +
                                                                   self.query_one("#user_resident_country",
                                                                                  Input).value +
                                                                   self.query_one("#user_given_names", Input).value +
                                                                   self.query_one("#user_family_name", Input).value,
                                                  "displayName": self.query_one("#user_preferred_name", Input).value,
                                                  "courtesyTitle": self.query_one("#user_title", Input).value,
                                                  "initials": "PAT",
                                                  "givenNames": self.query_one("#user_given_names", Input).value,
                                                  "surname": self.query_one("#user_family_name", Input).value,
                                                  "fullName": self.query_one("#user_preferred_name", Input).value,
                                                  "pronouns": self.query_one("#user_pronouns", Input).value,
                                                  "jobTitle": self.query_one("#user_job_title", Input).value,
                                                  "employeeNumber": self.query_one("#user_employee_id", Input).value,
                                                  "employeeType": "Full-Time",
                                                  "preferredLanguage": self.query_one("#user_preferred_language",
                                                                                      Input).value,
                                                  "residentCountry": self.query_one("#user_resident_country",
                                                                                    Input).value,
                                                  "timeZone": self.query_one("#user_time_zone", Input).value,
                                                  "description": self.query_one("#user_description", Input).value,
                                              }
                                            }
        try:
            new_profile_inst = MyProfile(self.app.view_server, self.app.platform_url, self.app.user, self.app.password)
            new_profile_guid = new_profile_inst.add_my_profile(self.new_element_request_body)
            self.log(f"Profile created with GUID: {new_profile_guid}")
            self.dismiss(200)
            return(200)
        except PyegeriaException as e:
            self.log(f"Error creating profile: {e!s} | request={self.new_element_request_body}")
            self.dismiss(400)
            return(400)

    def action_quit(self) -> int:
        self.dismiss(200)
        return(200)

class MyProfileTui(App):
    """My Profile App.

    Retrieves a user's profile from Egeria and displays current work items.
    If no profile is found, offers a UI to create one.
    """

    BINDINGS = [("q", "quit", "Quit")]
    CSS_PATH = "my_profile.tcss"

    SCREENS = {
        "create_profile": CreateProfileScreen,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        self.tech_type_response: dict = {}
        self.tech_type_list = []
        self.selected_t_node = None
        self.selected_t_node_label = None
        self.karma_points = 0

    def compose(self) -> ComposeResult:

        # Create tables up-front; populate them in on_mount()
        self.projects_table = DataTable(id="projects_table")
        self.communities_table = DataTable(id="communities_table")
        self.roles_table = DataTable(id="roles_table")
        self.actions_table = DataTable(id="actions_table")
        self.teams_table = DataTable(id="teams_table")
        self.user_identity_table = DataTable(id="user_identity_table")
        self.other_function_list = OptionList(id="other_function_list")

        # place widgets into grid on screen, note sequence determines position!
        yield Header(show_clock=True)

        yield ScrollableContainer(
            Static("Projects"),
            self.projects_table
        )

        yield ScrollableContainer(
            Static("Communities"),
            self.communities_table
        )

        yield ScrollableContainer(
            Static(f"Other Functions"),
            Static(f"[b]Select a function[/b]"),
            OptionList(
                Option("User Identities"),
                Option("Catalogs"),
                Option("Edit Profile"),
                Option("Subscriptions"),
                Option("Technology Types"),
                Option("Update Profile"),
                Option("User Bookmarks"),
            ),
            id="other_function_container"
        )

        yield ScrollableContainer(
            Static("Roles"),
            self.roles_table
        )

        yield ScrollableContainer(
            Static("Teams"),
            self.teams_table
        )

        yield ScrollableContainer(
            Static("Actions"),
            self.actions_table
        )

        yield Footer()

    async def on_mount(self) -> None:
        """Load profile; if missing, prompt to create it; then populate tables."""
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
            self.exit(400)
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
            self.exit(400)
            return

        self.result = result

        # Retry after creation if necessary
        try:
            self.user_profile_struct = self.my_profile_inst.get_my_profile(
                output_format="DICT",
                report_spec="My-User-MD",
            )
            self.log(f"Profile retrieved successfully: {self.user_profile_struct}")
        except PyegeriaException as e2:
            self.log(f"Error retrieving user profile: {e2!s}")
            self.exit(400)
            return
        if self.user_profile_struct is []:
            self.log(f"Error retrieving user profile. Exiting.")
            self.exit(400)
            return

        # strip out the individual profile elements
        self.user_profile = self.user_profile_struct[0]
        self.karma_points = self.user_profile.get("Karma Points") or 0
        self.my_projects_data = self.user_profile.get("Projects") or []
        self.my_teams_data = self.user_profile.get("Teams") or []
        self.my_communities_data = self.user_profile.get("Communities") or []
        self.my_roles_data = self.user_profile.get("Roles") or []
        self.my_actions_data = self.user_profile.get("Actions") or []
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
        SUB_TITLE = f"{self.full_name} ({self.user_profile.get('User ID')}, Karma Points: {self.karma_points})"
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

    @on(OptionList.OptionSelected)
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
                self.dismiss(200)
            elif self.tech_type_response == 400:
                self.log("Error fetching technology types.")
                self.dismiss(400)
            self.log("Technology types fetched successfully.")
            self.log("Displaying technology types...")
            await self.push_screen(TechnologyTypes(self.tech_type_list), callback=self.tech_type_callback)
            self.log("Technology types displayed successfully.")
        elif selected_option == "User Identities":
            pass
        elif selected_option == "Catalogs":
            pass
        elif selected_option == "User Bookmarks":
            pass
        elif selected_option == "Subscriptions":
            pass
        else:
            pass

    async def tech_type_callback(self, result) -> None:
        """ Callback for Technology Types screen
             If the result is int (400) it indicates an error in the screen
             if the result is str it contains the GUID of the selected technology type
        """
        #clear local data fields
        tech_type_guid = ""
        tech_type_name = ""
        tech_type_description = ""
        tech_type_templates = []
        tech_type_processes = []
        self.tech_type_data = {}
        self.tech_type_data_extracted = {}
        self.tech_type_templates = []
        self.tech_type_processes = []
        # check that we got a valid result from the screen
        if not result or isinstance(result, int) :
            self.log(f"Technology Types screen cancelled/failed; return: {result}, exiting.")
            self.exit(400)
            return
        self.selected_t_node = str(result)
        self.log(f"Technology Types screen returned: {self.selected_t_node}")
        # Request details for selected tech type
        try:
            self.tech_type_data = exec_report_spec(format_set_name="Tech-Type-Details",
                                                   output_format="DICT",
                                                   params={"search_string": self.selected_t_node, "filter_string": self.selected_t_node},
                                                   view_server=self.view_server,
                                                   view_url=self.platform_url,
                                                   user=self.user,
                                                   user_pass=self.user_password)
        except PyegeriaException as e:
            print_basic_exception(e)
            self.log(f"Error retrieving technology type details: {e!s}")
            self.exit(400)
            return
        self.log(f"Technology Type Data: {self.tech_type_data}, type: {type(self.tech_type_data)}")
        if self.tech_type_data.get("kind") is not None:
            self.tech_type_data_extracted = self.tech_type_data.get("data")
        else:
            self.tech_type_data_extracted = {"Error": "No data found for this technology type."}
        self.log (f"Technology Type Data Extracted: {self.tech_type_data_extracted}")
        for dataset in self.tech_type_data_extracted:
            tech_type_guid = dataset.get("GUID")
            tech_type_name = dataset.get("Display Name")
            tech_type_description = dataset.get("Description")

        await self.push_screen(TechnologyTypeOptions(tech_type_guid,
                                               tech_type_name,
                                               tech_type_description,
                                               tech_type_templates,
                                               tech_type_processes), callback = self.tech_type_options_callback)
        return

    def tech_type_options_callback(self, result):
        self.log(f"Technology Type Options screen returned: {result}")
        if not result or isinstance(result, int):
            self.log(f"Technology Type Options screen cancelled/failed; return: {result}, exiting.")
            self.exit(400)
            return
        self.log(f"Technology Type Options screen returned: {result}")
        self.selected_t_option = str(result)
        self.log(f"Technology Type Options screen returned: {self.selected_t_option}")
        # more logic to be implemented here

        return

    async def fetch_technology_types(self) -> int:
        self.tech_type_list: list = [{}]
        try:
            self.autoc = AutomatedCuration(self.view_server, self.platform_url, self.user_name, self.user_password)
            self.autoc.create_egeria_bearer_token(self.user_name, self.user_password)
            # retrieve the tech type data

            self.tech_type_json = await self.autoc.get_tech_type_hierarchy(
                                                    tech_type = "*",
            )

        except Exception as e:
            self.log(f"Exception in get_tech_type_list: {e}")
            self.tech_type_list = [{}]
            return(400)
        self.tech_type_resonse = json.loads(self.tech_type_json)
        self.log (f"tech_type_json: {self.tech_type_json}")
        self.log (f"tech_type_response: {self.tech_type_response}")
        print(f"tech type json: {self.tech_type_json}")
        print(f"tech type response: {self.tech_type_response}")
        self.tech_type_list = self.tech_type_response.get("data")
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
                            return(400)
                else:
                    self.log(f"error unknown outer data structure for Tech Type data")
                    return (401)
        else:
            self.log(f"Tech Type data not dict or list")
            return(402)

        self.log(f"output_data: {output_data}, {type(output_data)}")
        # return the extracted data (dict)
        self.tech_type_list = output_data
        return (200)

if __name__ == "__main__":
    app = MyProfileTui()
    app.run()