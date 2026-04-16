from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, Static, DataTable


class MyTeam(ModalScreen):
    """ Display a list of team Members for a Team Leader """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("b", "back", "Go back")
        ]
    CSS_PATH = "my_profile.tcss"

    def __init__(self, my_team, leader_name):
        super().__init__(my_team)
        self.title = "My Team"
        self.my_team = my_team
        self.leader_name = leader_name
        self.team_table: DataTable = DataTable()

    def on_mount(self) -> None:
        if self.my_team:
            if "Selection Error" in self.my_team[0][0]:
                self.team_table.add_column("Error")
                self.team_table.add_column("Description")
                self.team_table.add_row(self.my_team[0][0], self.my_team[0][1])
            else:
                self.team_table.add_column("Name")
                self.team_table.add_column("Role")
                self.team_table.add_column("Karma Points")
                self.team_table.border_title = f"{self.leader_name}: My Team "
                self.team_table.border = True
                self.team_table.zebra_stripes = True
                self.team_table.cursor = "row"
                for member in self.my_team:
                    self.team_table.add_row(member[0], member[1], member[2])
        else:
            self.log(f"No team member data for MyTeam Screen", { "my_team": self.my_team})
            self.team_table.add_column("Error")
            self.team_table.add_column("Description")
            self.team_table.add_row("No team members found", "No team members returned from Egeria for this team")

        self.team_table.refresh()

    def compose(self) -> ComposeResult:
        yield Header()
        yield ScrollableContainer(
            Static(f"List of Team Members"),
            self.my_team)
        yield Footer()

    def action_quit(self) -> None:
        self.dismiss("200")

    def action_back(self) -> None:
        self.dismiss(
            "201")