# User Guide

## General Usage

Toggle the current view to a "RawLineEdit" view via the command palette command `Raw Line Edit: Toggle` (you can setup your own keybinding or add it to your context menu if you choose).

Using the ++enter++ key you can change a line ending to Windows style, to Linux/Unix style with ++shift+enter++, or even macOS 9 with ++ctrl+enter++.  Select multiple lines to change more than one line.

## Settings

RawLineEdit has a few settings that can tweak the behavior and look of the plugin.

### `view_only`

Instead of opening a read/write view, RawLineEdit will open up a read only output panel.

```js
    // View only mode: pops up an output panel showing line endings.
    // No editing possible.
    "view_only": false,
```

### `operate_on_unsaved_buffers`

Allows RawLineEdit to operate on views that haven't been saved to disk.

```js
    // Operate on sublime unsaved view buffer
    // Instead of reading the file from disk,
    // The file will be read directly from the buffer
    // In these cases the line endings will be normalized,
    // but you can edit them and save them back to disk.
    // Not sure how useful this is.
    "operate_on_unsaved_buffers": false
```

### `use_sub_notify`

Enables sending messages through the [SubNotify][subnotify] plugin.

```javascript
    // Use subnotify if available
    "use_sub_notify": true,
```

## `Colorize Line Endings`

When the [use_raw_line_edit_theme](#use_raw_line_edit_theme) is enabled, RawLineEdit will use a special language file so that a theme can colorize the line endings.  In order to get the special colors, you must add special keys to your current tmTheme file.

Here are the keys; you can specify whatever color you like:

```xml
        <dict>
            <key>name</key>
            <string>Raw New Line: Carriage Return</string>
            <key>scope</key>
            <string>glyph.carriage-return</string>
            <key>settings</key>
            <dict>
                <key>foreground</key>
                <string>#66CCCC</string>
            </dict>
        </dict>
        <dict>
            <key>name</key>
            <string>Raw New Line: New Line Glyph</string>
            <key>scope</key>
            <string>glyph.new-line</string>
            <key>settings</key>
            <dict>
                <key>foreground</key>
                <string>#F2777A</string>
            </dict>
        </dict>
```

--8<-- "refs.md"
