from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, ListView, ListItem, Label
from textual.reactive import reactive


class TaskList(ListView):
    """A list view to display reactive items."""

    # Define a reactive variable for the list of items
    items = reactive([])

    # The watcher method automatically runs whenever 'items' is updated
    def watch_items(self, old_items, new_items) -> None:
        """Clear and repopulate the list with the new items."""
        self.clear()
        for item_data in new_items:
            self.append(ListItem(Label(item_data)))


class TaskApp(App):
    """A Textual app with a dynamic list."""

    BINDINGS = [("a", "add_task", "Add Task")]
    CSS_PATH = "main.css"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield Button("Add Task", id="add_task_button")
        yield TaskList(id="task_list")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when the button is pressed."""
        if event.button.id == "add_task_button":
            self.action_add_task()

    def action_add_task(self) -> None:
        """An action to add a new item to the task list."""
        task_list_widget = self.query_one(TaskList)

        # This is the key step for reactive lists: re-assign to a new list object
        current_tasks = task_list_widget.items
        new_task_number = len(current_tasks) + 1
        task_list_widget.items = current_tasks + [f"Task {new_task_number}"]


if __name__ == "__main__":
    app = TaskApp()
    app.run()
