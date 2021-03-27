# -*- coding: utf-8 -*-
"""
Raw Line Edit.

Licensed under MIT
Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
"""
from __future__ import unicode_literals
import sublime
import sublime_plugin
import codecs
import re
from os.path import exists
try:
    from SubNotify.sub_notify import SubNotifyIsReadyCommand as Notify
except Exception:

    class Notify(object):
        """Fallback notify class."""

        @classmethod
        def is_ready(cls):
            """Disable SubNotify by returning False."""

            return False

CSS = """
<style>
span {
  display: inline;
  font-size: 0.9rem;
  font-weight: bold;
  padding: 0.05rem 0.25rem;
  border-radius: 0.25rem;
  background-color: var(--foreground);
  color: var(--background);
  border: 1px solid var(--mdpopups-kbd-border);
}
html.light span {
  border: 1px solid color(var(--foreground) blend(white 80%));
}
html.light span {
  border: 1px solid color(var(--foreground) blend(black 80%));;
}
</style>
"""

RE_NEW_LINE = re.compile(r'(?:\r\n|(?!\r\n)[\n\r])')


def process_lines(text):
    """Count line ending types and return buffer with only new lines."""

    crlf = []
    lf = []
    cr = []
    line = {'value': -1}

    def repl(m):
        """Replace."""

        line['value'] += 1
        end = m.group(0)
        if end == '\r\n':
            crlf.append(line['value'])
        elif end == '\n':
            lf.append(line['value'])
        else:
            cr.append((line['value']))
        return '\n'

    text = RE_NEW_LINE.sub(repl, text)
    return text, lf, cr, crlf


def strip_buffer_glyphs(view):
    """Strip all glyphs from buffer to load back into view."""

    line = -1
    more = True
    last_value = -1
    lines = []
    mappings = {'crlf': '\r\n', 'cr': '\r', 'lf': '\n'}
    while more:
        line += 1
        value = view.text_point(line, 0)
        region = None
        for line_type in ('crlf', 'cr', 'lf'):
            regions = view.get_regions('rle_line_%d_%s' % (line, line_type))
            if regions:
                view.erase_regions('rle_line_%d_%s' % (line, line_type))
                region = regions[0]
                break
        if region is not None:
            view.erase_phantoms('rle_line_%d' % line)
            lines.append(view.substr(view.line(region)) + mappings[line_type])
        if value == last_value:
            more = False
        last_value = value
    return ''.join(lines)


def convert_buffers():
    """Operate on unsaved buffers."""

    return bool(sublime.load_settings("raw_line_edit.sublime-settings").get("operate_on_unsaved_buffers", False))


def get_encoding(view):
    """Get the file encoding."""

    encoding = view.encoding()
    mapping = [
        ("with BOM", ""),
        ("Windows", "cp"),
        ("-", "_"),
        (" ", "")
    ]
    encoding = view.encoding()
    m = re.match(r'.+\((.*)\)', encoding)
    if m is not None:
        encoding = m.group(1)

    for item in mapping:
        encoding = encoding.replace(item[0], item[1])

    return "utf_8" if encoding in ["Undefined", "Hexidecimal"] else encoding


def notify(msg):
    """Notify message."""

    settings = sublime.load_settings("raw_line_edit.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "RawLineEdit", "msg": msg})
    else:
        sublime.status_message(msg)


def error(msg):
    """Error message."""

    settings = sublime.load_settings("raw_line_edit.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "RawLineEdit", "msg": msg, "level": "error"})
    else:
        sublime.error_message("RawLineEdit:\n%s" % msg)


class RawLineTextBuffer(object):
    """Text buffer."""

    bfr = None
    syntax = None
    endings = None
    view = None

    @classmethod
    def set_buffer(cls, view):
        """Read buffer from view and strip new line glyphs."""

        cls.bfr = strip_buffer_glyphs(view)

    @classmethod
    def clear_buffer(cls):
        """Clear the buffer object."""

        cls.bfr = None
        cls.view = None

    @classmethod
    def check_loading(cls, view):
        """Check if file is done loading yet before applying buffer."""

        cls.view = view
        sublime.set_timeout(cls.poll_loading, 300)

    @classmethod
    def poll_loading(cls):
        """Check if file is done loading, and if so, update view with buffer."""

        if cls.view.is_loading():
            sublime.set_timeout(cls.poll_loading, 300)
        else:
            cls.view.run_command("write_raw_line_text")


class WriteRawLineTextCommand(sublime_plugin.TextCommand):
    """Write buffer to view."""

    def run(self, edit):
        """Write the unsaved buffer to the view."""

        if RawLineTextBuffer.bfr is None:
            return
        self.view.replace(edit, sublime.Region(0, self.view.size()), RawLineTextBuffer.bfr)
        RawLineTextBuffer.clear_buffer()


class ToggleRawLineEditCommand(sublime_plugin.TextCommand):
    """Toggle raw line edit mode."""

    def disable_rle(self, edit):
        """Disable raw line ending mode."""

        # Save raw line ending changes
        if self.view.is_dirty():
            if sublime.ok_cancel_dialog("Raw Line Edit:\nFile has unsaved changes.  Save?", "Save"):
                self.view.run_command("save")

        # Get the settings
        settings = self.view.settings()
        file_name = settings.get("RawLineEditFilename")
        syntax = settings.get("RawLineEditSyntax")
        buffer_endings = settings.get("RawLineBuffer", None)

        # Strip the buffer of glyphs and prepare to write
        # the stripped buffer back to the view
        if buffer_endings is not None:
            RawLineTextBuffer.set_buffer(self.view)

        # Open temp view if only one view is open,
        # so not to close the window when we remove the view.
        window = self.view.window()
        temp = None
        if len(window.views()) <= 1:
            temp = window.new_file()

        # Close raw line view
        window.focus_view(self.view)
        window.run_command("close_file")

        # Open the file on disk
        new_view = window.open_file(file_name)

        # Close temp view if needed
        if temp is not None:
            window.focus_view(temp)
            window.run_command("close_file")

        # Set view settings
        window.focus_view(new_view)
        new_view.set_syntax_file(syntax)

        # Reapply unsaved buffer if needed
        if buffer_endings is not None:
            new_view.set_line_endings(buffer_endings)
            RawLineTextBuffer.check_loading(new_view)

    def enable_rle(self, edit, file_name):
        """Enable raw line ending mode."""

        if self.view.is_dirty():
            if convert_buffers():
                msg = (
                    "File has unsaved changes.  If you choose to 'continue' without a 'save', "
                    "the view buffer will be parsed as the source.\n\nSave?"
                )
            else:
                msg = (
                    "File has unsaved changes.  If you choose to 'continue' without a 'save', "
                    "changes will be discarded and the file will be parsed from disk.\n\nSave?"
                )
            value = sublime.yes_no_cancel_dialog(msg, "Save", "Continue")
            if value == sublime.DIALOG_YES:
                # Save the file
                self.view.run_command("save")
            elif value == sublime.DIALOG_NO:
                # Convert the unsaved buffer
                if convert_buffers():
                    self.enable_buffer_rle(edit, file_name)
                    return
                else:
                    if file_name is None:
                        error("File must exist on disk!")
                        return
                    else:
                        notify("Changes discarded.")
            else:
                return

        if file_name is None or not exists(file_name):
            if convert_buffers():
                self.enable_buffer_rle(edit)
            else:
                error("File must exist on disk!")
            return

        # Convert the file on disk to a raw line view
        encoding = get_encoding(self.view)
        try:
            self.show_rle(edit, file_name, encoding)
        except Exception:
            self.show_rle(edit, file_name, "utf-8")

    def show_rle(self, edit, file_name, encoding):
        """
        Read the file from disk converting actual lines to glyphs.

        Present the info in raw line view.
        """
        with codecs.open(file_name, "r", encoding) as f:
            text, lf, cr, crlf = process_lines(f.read())
            self.view.replace(edit, sublime.Region(0, self.view.size()), text)
            self.view.set_line_endings("Unix")
            settings = self.view.settings()
            settings.set("RawLineEdit", True)
            settings.set("RawLineEditSyntax", settings.get('syntax'))
            settings.set("RawLineEditFilename", file_name)
            self.view.assign_syntax(settings.get('syntax'))
            self.view.set_scratch(True)
            self.view.set_read_only(True)

            self.update_phantoms(crlf, cr, lf)

    def read_buffer(self):
        """Read the unsaved buffer and replace with new line glyphs."""

        endings = {
            "Windows": "\r\n",
            "Unix": "\n",
            "CR": "\r"
        }
        line_ending = endings[self.view.line_endings()]
        bfr = []
        for line in self.view.split_by_newlines(sublime.Region(0, self.view.size())):
            bfr.append(self.view.substr(line) + line_ending)
        return "".join(bfr)

    def enable_buffer_rle(self, edit, file_name=None):
        """Enable the raw line mode on an unsaved buffer."""

        if self.view.is_read_only():
            self.view.set_read_only(False)
        settings = self.view.settings()
        self.view.settings().set("RawLineBuffer", self.view.line_endings())
        text, lf, cr, crlf = process_lines(self.read_buffer())
        self.view.replace(edit, sublime.Region(0, self.view.size()), text)
        self.view.set_line_endings("Unix")
        settings.set("RawLineEdit", True)
        settings.set("RawLineEditSyntax", self.view.settings().get('syntax'))
        if file_name is not None:
            settings.set("RawLineEditFilename", file_name)
        self.view.set_scratch(True)
        self.view.set_read_only(True)
        self.update_phantoms(crlf, cr, lf)

    def disable_buffer_rle(self, edit):
        """Disable the raw line mode on an unsaved buffer."""

        if self.view.is_dirty():
            if sublime.ok_cancel_dialog("Raw Line Edit:\nFile has unsaved changes.  Save?", "Save"):
                self.view.run_command("save")
                self.disable_rle(edit)
                return
        win = self.view.window()
        new_view = win.new_file()
        settings = self.view.settings()
        syntax = settings.get("RawLineEditSyntax")
        line_endings = settings.get("RawLineBuffer")
        bfr = strip_buffer_glyphs(self.view)
        new_view.replace(edit, sublime.Region(0, self.view.size()), bfr)
        new_view.set_line_endings(line_endings)
        new_view.set_syntax_file(syntax)
        win.focus_view(self.view)
        win.run_command("close_file")
        win.focus_view(new_view)

    def update_phantoms(self, crlf, cr, lf):
        """Update phantoms."""

        for line in crlf:
            pt = self.view.text_point(line + 1, 0) - 1
            region = sublime.Region(pt)
            self.view.add_phantom(
                'rle_line_%d' % line,
                region,
                '%s<span>¤</span><span>¬</span>' % CSS,
                sublime.LAYOUT_INLINE
            )
            self.view.add_regions('rle_line_%d_crlf' % line, [region], '', '', sublime.HIDDEN)
        for line in cr:
            pt = self.view.text_point(line + 1, 0) - 1
            region = sublime.Region(pt)
            self.view.add_phantom(
                'rle_line_%d' % line,
                region,
                '%s<span>¤</span>' % CSS,
                sublime.LAYOUT_INLINE
            )
            self.view.add_regions('rle_line_%d_cr' % line, [region], '', '', sublime.HIDDEN)
        for line in lf:
            pt = self.view.text_point(line + 1, 0) - 1
            region = sublime.Region(pt)
            self.view.add_phantom(
                'rle_line_%d' % line,
                region,
                '%s<span>¬</span>' % CSS,
                sublime.LAYOUT_INLINE
            )
            self.view.add_regions('rle_line_%d_lf' % line, [region], '', '', sublime.HIDDEN)

    def run(self, edit):
        """Toggle the raw line mode."""

        file_name = self.view.file_name()
        settings = self.view.settings()

        if (file_name is None or not exists(file_name)) and settings.get("RawLineEdit", False):
            self.disable_buffer_rle(edit)
        elif settings.get("RawLineEdit", False):
            self.disable_rle(edit)
        elif not settings.get("RawLineEdit", False):
            self.enable_rle(edit, file_name)


class PopupRawLineEditCommand(sublime_plugin.TextCommand):
    """Popup command."""

    def popup_rle(self, file_name):
        """Popup raw line edit view."""

        if self.view.is_dirty():
            if convert_buffers():
                msg = (
                    "File has unsaved changes.  If you choose to 'continue' without a 'save', "
                    "the view buffer will be parsed as the source.\n\nSave?"
                )
            else:
                msg = (
                    "File has unsaved changes.  If you choose to 'continue' without a 'save', "
                    "changes will be discarded and the file will be parsed from disk.\n\nSave?"
                )
            value = sublime.yes_no_cancel_dialog(msg, "Save", "Discard Changes", "Cancel")
            if value == sublime.DIALOG_YES:
                self.view.run_command("save")
            elif value == sublime.DIALOG_NO:
                # Convert the unsaved buffer
                if convert_buffers():
                    self.enable_buffer_rle(file_name)
                    return
                else:
                    if file_name is None:
                        error("File must exist on disk!")
                        return
                    else:
                        notify("Changes discarded.")
            else:
                return

        if file_name is None or not exists(file_name):
            if convert_buffers():
                self.enable_buffer_rle()
            else:
                error("File must exist on disk!")
            return

        encoding = get_encoding(self.view)
        try:
            self.show_rle(file_name, encoding)
        except Exception:
            self.show_rle(file_name, "utf-8")

    def read_buffer(self):
        """Read the unsaved buffer and replace with new line glyphs."""

        endings = {
            "Windows": "\r\n",
            "Unix": "\n",
            "CR": "\r"
        }
        line_ending = endings[self.view.line_endings()]
        bfr = []
        for line in self.view.split_by_newlines(sublime.Region(0, self.view.size())):
            bfr.append(self.view.substr(line) + line_ending)
        return "".join(bfr)

    def get_output_panel(self):
        """Get output panel."""

        win = self.view.window()
        view = win.find_output_panel('raw_line_edit_view')
        if view is not None:
            win.destroy_output_panel('raw_line_edit_view')
        return win.get_output_panel('raw_line_edit_view')

    def enable_buffer_rle(self, file_name=None):
        """Enable the raw line mode on an unsaved buffer."""

        view = self.get_output_panel()
        view.set_line_endings("Unix")
        view.set_read_only(False)

        RawLinesEditReplaceCommand.region = sublime.Region(0, view.size())
        RawLinesEditReplaceCommand.text, lf, cr, crlf = process_lines(self.read_buffer())
        view.run_command("raw_lines_edit_replace")
        view.sel().clear()
        settings = view.settings()
        view.assign_syntax(self.view.settings().get('syntax'))
        settings.set("RawLineEdit", True)
        settings.set("RawLineEditSyntax", self.view.settings().get('syntax'))
        settings.set("RawLineEditPopup", True)
        settings.set("RawLineBuffer", self.view.line_endings())
        if file_name is not None:
            settings.set("RawLineEditFilename", file_name)
        view.set_scratch(True)
        view.set_read_only(True)

        self.update_phantoms(view, crlf, cr, lf)
        self.view.window().run_command("show_panel", {"panel": "output.raw_line_edit_view"})

    def show_rle(self, file_name, encoding):
        """Show the raw line view popup."""

        try:
            view = self.get_output_panel()
            view.set_line_endings("Unix")
            with codecs.open(file_name, "r", encoding) as f:
                view.set_read_only(False)
                RawLinesEditReplaceCommand.region = sublime.Region(0, view.size())
                RawLinesEditReplaceCommand.text, lf, cr, crlf = process_lines(f.read())
                view.run_command("raw_lines_edit_replace")
                view.sel().clear()
                view.assign_syntax(self.view.settings().get('syntax'))
                view.settings().set("RawLineEditSyntax", self.view.settings().get('syntax'))
                view.settings().set("RawLineEdit", True)
                view.settings().set("RawLineEditFilename", file_name)
                view.settings().set("RawLineEditPopup", True)
                view.set_scratch(True)
                view.set_read_only(True)

                self.update_phantoms(view, crlf, cr, lf)
                self.view.window().run_command("show_panel", {"panel": "output.raw_line_edit_view"})
        except Exception:
            self.view.window().run_command("hide_panel", {"panel": "output.raw_line_edit_view"})
            raise

    def update_phantoms(self, view, crlf, cr, lf):
        """Update phantoms."""

        for line in crlf:
            pt = view.text_point(line + 1, 0) - 1
            region = sublime.Region(pt)
            view.add_phantom(
                'rle_line_%d' % line,
                region,
                '%s<span>¤</span><span>¬</span>' % CSS,
                sublime.LAYOUT_INLINE
            )
            view.add_regions('rle_line_%d_crlf' % line, [region], '', '', sublime.HIDDEN)
        for line in cr:
            pt = view.text_point(line + 1, 0) - 1
            region = sublime.Region(pt)
            view.add_phantom(
                'rle_line_%d' % line,
                region,
                '%s<span>¤</span>' % CSS,
                sublime.LAYOUT_INLINE
            )
            view.add_regions('rle_line_%d_cr' % line, [region], '', '', sublime.HIDDEN)
        for line in lf:
            pt = view.text_point(line + 1, 0) - 1
            region = sublime.Region(pt)
            view.add_phantom(
                'rle_line_%d' % line,
                region,
                '%s<span>¬</span>' % CSS,
                sublime.LAYOUT_INLINE
            )
            view.add_regions('rle_line_%d_lf' % line, [region], '', '', sublime.HIDDEN)

    def run(self, edit):
        """Popup panel with raw line view."""

        file_name = self.view.file_name()
        settings = self.view.settings()
        if (not settings.get("RawLineEdit", False)) and not settings.get('RawLineEditPopup', False):
            self.popup_rle(file_name)


class RawLineInsertCommand(sublime_plugin.TextCommand):
    """Insert text in view."""

    def run(self, edit, style="Unix"):
        """Insert text."""

        for s in reversed(self.view.sel()):
            line_regions = self.view.lines(s)
            for region in line_regions:
                row = self.view.rowcol(region.begin())[0]
                if row >= 0:
                    r = None
                    for line_type in ('crlf', 'cr', 'lf'):
                        temp = self.view.get_regions('rle_line_%d_%s' % (row, line_type))
                        if temp:
                            r = temp[0]
                            break
                    if r is not None:
                        self.view.erase_regions('rle_line_%d_%s' % (row, line_type))
                        self.view.erase_phantoms('rle_line_%d' % row)

                        pt = self.view.text_point(row + 1, 0) - 1
                        r = sublime.Region(pt)
                        if style == "Unix":
                            temp = '%s<span>¬</span>'
                            line_type = 'lf'
                        elif style == "Windows":
                            temp = '%s<span>¤</span><span>¬</span>'
                            line_type = 'crlf'
                        else:
                            temp = '%s<span>¤</span>'
                            line_type = 'cr'
                        self.view.add_phantom(
                            'rle_line_%d' % row,
                            r,
                            temp % CSS,
                            sublime.LAYOUT_INLINE
                        )
                        self.view.add_regions('rle_line_%d_%s' % (row, line_type), [r], '', '', sublime.HIDDEN)


class RawLinesEditReplaceCommand(sublime_plugin.TextCommand):
    """Replace text in view."""

    text = None
    region = None

    def run(self, edit):
        """Replace text."""

        cls = RawLinesEditReplaceCommand
        if cls.text is not None and cls.region is not None:
            self.view.replace(edit, cls.region, cls.text)
        cls.text = None
        cls.region = None


class RawLineEditListener(sublime_plugin.EventListener):
    """RawLineEdit Listener."""

    def on_pre_save(self, view):
        """Convert raw line mode back to normal mode before save."""

        if view.settings().get("RawLineEdit", False) and not view.settings().get('RawLineEditPopup', False):
            RawLinesEditReplaceCommand.region = sublime.Region(0, view.size())
            RawLinesEditReplaceCommand.text = strip_buffer_glyphs(view)
            view.set_read_only(False)
            view.run_command("raw_lines_edit_replace")
            view.set_read_only(True)

    def on_post_save(self, view):
        """Convert view back to raw line mode after save."""

        if view.settings().get("RawLineEdit", False) and not view.settings().get('RawLineEditPopup', False):
            file_name = view.file_name()
            if file_name is not None:
                view.settings().set("RawLineEditFilename", file_name)
            if view.settings().set("RawLineBuffer", None) is not None:
                view.settings().erase("RawLineBuffer")

            view.set_read_only(False)
            RawLinesEditReplaceCommand.region = sublime.Region(0, view.size())
            RawLinesEditReplaceCommand.text, lf, cr, crlf = process_lines(
                view.substr(RawLinesEditReplaceCommand.region)
            )
            view.run_command("raw_lines_edit_replace")

            for line in crlf:
                pt = view.text_point(line + 1, 0) - 1
                region = sublime.Region(pt)
                view.add_phantom(
                    'rle_line_%d' % line,
                    region,
                    '%s<span>¤</span><span>¬</span>' % CSS,
                    sublime.LAYOUT_INLINE
                )
                view.add_regions('rle_line_%d_crlf' % line, [region], '', '', sublime.HIDDEN)
            for line in cr:
                pt = view.text_point(line + 1, 0) - 1
                region = sublime.Region(pt)
                view.add_phantom(
                    'rle_line_%d' % line,
                    region,
                    '%s<span>¤</span>' % CSS,
                    sublime.LAYOUT_INLINE
                )
                view.add_regions('rle_line_%d_cr' % line, [region], '', '', sublime.HIDDEN)
            for line in lf:
                pt = view.text_point(line + 1, 0) - 1
                region = sublime.Region(pt)
                view.add_phantom(
                    'rle_line_%d' % line,
                    region,
                    '%s<span>¬</span>' % CSS,
                    sublime.LAYOUT_INLINE
                )
                view.add_regions('rle_line_%d_lf' % line, [region], '', '', sublime.HIDDEN)

            view.set_scratch(True)
            view.set_read_only(True)

    def on_query_context(self, view, key, operator, operand, match_all):
        """Handle raw line mode shortcuts."""

        settings = view.settings()
        return (
            settings.get("RawLineEdit", False) and key.startswith("raw_line_edit") and
            not settings.get('RawLineEditPopup', False)
        )
