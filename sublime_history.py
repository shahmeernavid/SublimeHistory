import sublime, sublime_plugin

SETTINGS = sublime.load_settings('SublimeHistory.sublime-settings')
# The minimum number of lines between the new and old cursor positions to
# trigger adding the new cursor position to history.
SPACE = SETTINGS.get('sublime_history_space_barrier', 25)
# Maximum number of cursor positions history can contain.
HISTORY_LIMIT = SETTINGS.get('sublime_history_limit', 20)

# Map of view ids to lists of cursor positions.
history = {}
# Current position in history.
# 0: Most recent entry.
# -1: Second most recent entry.
# -2: Third most recent entry.
# etc
position = 0
# Boolean indicating if the back/forward history commands moved the cursor.
cmd_ran = False

class Events(sublime_plugin.EventListener):
    @classmethod
    def on_close(cls, view):
        """Standard sublime_plugin.EventListener method. Called when a view is
        closed. Implemented so that we keep out history free of unnecessary
        data.

        Args:
            view - View that was closed.
        """
        if history.get(view.id()) is not None:
            del history[view.id()]

    @classmethod
    def get_line_diff(cls, view, region_one, region_two):
        """Computes the number of lines that separate the beginning of
        region_one and the end of region_two.

        Args:
            view - View that the given regions are in.
            region_one - First region.
            region_two - Second region.

        Returns: Number of lines that separate the two regions.
        """
        region = sublime.Region(region_one.begin(), region_two.end())
        return len(view.split_by_newlines(region))

    @classmethod
    def on_selection_modified(cls, view):
        """Standard sublime_plugin.EventListener method. Called when a selection
        is modified. Implemented so that we can add the position of the cursor
        to history.

        Args:
            view - View selection change occurred on.
        """
        # Get write access to global variables.
        global position
        global cmd_ran
        global history

        # If this view is not in our history map, add it.
        if history.get(view.id()) is None or history.get(view.id()) == []:
            history[view.id()] = [view.sel()[0]]

        # Prevent adding cursor change to history if the change occurred due
        # to this plugin.
        if cmd_ran:
            cmd_ran = False
            return

        # Get the new and old positions of the cursor.
        pos = view.sel()[0]
        old_pos = history[view.id()][-1]
        # If the line difference is sufficient, add the new cursor position to
        # history.
        if cls.get_line_diff(view, pos, old_pos) > SPACE:
            # If we've moved back in history, a new entry should overwrite
            # entries that come after the current position.
            # [1, 2, 3] - Initial.
            # [1, 2] - Go back in history.
            # [1, 2, 4] - Add new entry, 3 is lost.
            history[view.id()] = history[view.id()][:position + \
                len(history[view.id()])]
            # Reset position.
            position = 0
            # Add new cursor position.
            history[view.id()].append(pos)

            # If history exceeds length limits, remove the oldest entry.
            if len(history[view.id()]) > HISTORY_LIMIT:
                history[view.id()].pop(0)

class BackSublimeHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Get write access to global variables.
        global position
        global cmd_ran

        # Only move back in history if we are not at the end.
        if position > -len(history[self.view.id()]) + 1:
            # Indicate that this cursor move is because of a cmd.
            cmd_ran = True
            # decrement position counter, indicating moving back in history.
            position -= 1
            # Get new position from history. Since array[-1] refers to the last
            # element of array, we need to subtract 1 to get the right element.
            new_pos = history[self.view.id()][position - 1]
            # Clear current cursor, create new cursor, scroll to cursor.
            self.view.sel().clear()
            self.view.sel().add(new_pos)
            self.view.show_at_center(new_pos)

class ForwardSublimeHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Get write access to global variables.
        global position
        global cmd_ran

        # Only move forward in history if we are not at the beginning.
        if position < 0:
            # Indicate that this cursor move is because of a cmd.
            cmd_ran = True
            # Increment position counter, indicating moving forward in history.
            position += 1
            # Get new position from history. Since array[-1] refers to the last
            # element of array, we need to subtract 1 to get the right element.
            new_pos = history[self.view.id()][position - 1]
            # Clear current cursor, create new cursor, scroll to cursor.
            self.view.sel().clear()
            self.view.sel().add(new_pos)
            self.view.show_at_center(new_pos)
