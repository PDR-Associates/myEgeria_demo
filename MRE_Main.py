import os

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Label, Button, TextArea, Header, Static, Footer
from textual import on

class SplashScreen(Screen):
    """Splash screen MRE version"""

    class SplashContinue(Message):
        """Message to continue to the login screen."""

        def __init__(self):
            super().__init__()

    def __init__(self) -> None:
        super().__init__()
        self.app_build_author = "Peter Coldicott"
        self.app_build_platform = "MacOS"
        self.welcome_text = ("\n\n"
            "This is example UI code package that leverages the Textual/Rich open source UI Frameworks,\n"
            "and the pyegeria package which is part of the Egeria Project.\n\n")

    def compose(self) -> ComposeResult:

        yield Header(show_clock=True)
        yield Container(
            Static(
                "egeria server info ..... ", id="connection_info"),
            TextArea(self.welcome_text, id="splash_text"),
            Label(
                f"Build Author: {self.app_build_author} | "
                f"Platform: {self.app_build_platform}", id="splash_meta",
                )
            )
        yield Button("Continue", variant="primary", id="continue")
        yield Footer()

    @on(Button.Pressed, "#continue")
    async def continue_to_app(self) -> None:
        """ Quit button pressed, isssue continue message to app """

        self.log(f"Continue button pressed, app is: {self.app}")
        self.post_message(SplashScreen.SplashContinue())


class DataProducts(App):

    SCREENS = {
        "splash": SplashScreen,
    }

    class EgeriaDataReceived(Message):
        def __init__(self, data: list):
            super().__init__()
            self.data = data

    def __init__(self):
        super().__init__()

    def on_mount(self):
        self.title = "MyEgeria"
        self.subtitle = "Data Products"
        # display the splash screen
        self.log(f"Pushing Splash Screen")
        self.push_screen("splash")

    @on(SplashScreen.SplashContinue)
    def handle_splash_screen_splash_continue(self):
        """ Continue received from the Splash Screen"""
        self.log(f"Continue received from Splash Screen, pushing Data Product Screen")
        # run the function to retrieve collections data from Egeria
        self.log(f"Retrieving Data Products from Egeria - get_collections_from_egeria")

if __name__ == "__main__":
    DataProducts().run()