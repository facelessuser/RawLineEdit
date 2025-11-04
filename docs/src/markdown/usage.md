# User Guide

## General Usage

Toggle the current view to a "RawLineEdit" view via the command palette command `Raw Line Edit: Toggle Line Edit Mode`.
To simply view the raw line endings in a output panel, call the command `Raw Line Edit: View Line Endings`.

Using the ++enter++ key you can change a line ending to Windows style, to Linux/Unix style with ++shift+enter++, or even
macOS 9 with ++ctrl+enter++.  Select multiple lines to change more than one line.

## Settings

RawLineEdit has a few settings that can tweak the behavior and look of the plugin.

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

## Create Key Bindings

To enable raw line edit/view mode via a keybinding you can bind the following commands:

-   `toggle_raw_line_edit`: a command for create a view where you can view and modify line endings.
-   `popup_raw_line_edit`: creates an output panel with a read only view of the line endings.

--8<-- "refs.md"
