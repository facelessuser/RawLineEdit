#RawLineEdit

## 2.0.3

-   **FIX**: Update dependenciest to remove uneeded ones and add `typing`.

## 2.0.2

-   **FIX**: Fix issue when viewing a file over and over old phantoms persist.

## 2.0.1

-   **FIX**: Fix installation message referring to non-existent quick start guide.

## 2.0.0

-   **NEW**: When view is unsaved, allow the ability to save, continue without saving, and canceling when using popup
    output.
-   **NEW**: Raw Line views will now use phantoms to show line endings.
-   **NEW**: Raw Line views will always use the same syntax as the original view.
-   **NEW**: Raw Line views, due to change in implementation (phantoms), can now properly handle toggling between macOS
    9 `\r`, Windows `\r\n`, and Linux/Unix `\n` line endings.
-   **NEW**: Remove `view_only` setting as you can now call either the edit command or the view command as desired.

## 1.2.1

-   **FIX**: When view is unsaved, allow the ability to save, continue without saving, and canceling.

## 1.2.0

-   **FIX**: Update dependencies.

## 1.1.0

-   **NEW**: Migrate to tag releases.

## 1.0.0

-   **NEW**: Initial release.
