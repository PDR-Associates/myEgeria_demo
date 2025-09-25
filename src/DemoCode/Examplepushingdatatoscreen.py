from textual.screen import Screen
from textual.widgets import Header, Footer, Label
from textual.app import App, ComposeResult
from textual.widgets import Button

class DetailScreen(Screen):
    def __init__(self, message: str, name: str | None = None, id: str | None = None):
        super().__init__(name=name, id=id)
        self.message = message

    def compose(self):
        yield Header()
        yield Label(f"Welcome to the Detail Screen! You passed: {self.message}")
        yield Footer()


class MyApp(App):
    SCREENS = {"detail": DetailScreen} # Register the screen if using string names

    def compose(self) -> ComposeResult:
        yield Button("Go to Detail Screen", id="go_detail")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "go_detail":
            # Create an instance of the DetailScreen, passing the message
            detail_screen_instance = DetailScreen(message="Hello from Main Screen!")
            self.push_screen(detail_screen_instance)

if __name__ == "__main__":
    app = MyApp()
    app.run()