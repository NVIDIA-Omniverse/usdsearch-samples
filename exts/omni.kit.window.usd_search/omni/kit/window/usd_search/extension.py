# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


import omni.ext
import asyncio
import omni.ui as ui
import logging
import carb
from .window import UsdSearchWindow
from omni.kit.menu.utils import MenuItemDescription

logger = logging.getLogger(__name__)
# Settings paths that start with "/persistent" are saved between sessions.
PREFIX = "/persistent/exts/omni.kit.window.usd_search"

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.


class UsdSearchWindowExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.

    WINDOW_NAME = "USD Search"
    MENU_GROUP = "Window"

    def on_startup(self, ext_id):
        """Runs once when extension is starting up."""
        logger.info("Starting Up")
        self._window = None
        self._menu = None
        self._ext_name = omni.ext.get_extension_name(ext_id)
        self._open_pref_name = "start_window_open"
        self._settings = carb.settings.get_settings()
        self._open = self._settings.get(PREFIX + "/" + self._open_pref_name)

        self._menu = [MenuItemDescription(
            name=UsdSearchWindowExtension.WINDOW_NAME,
            ticked=self._open,
            ticked_fn=self._is_visible,
            onclick_fn=self._menu_toggle_window
        )]
        omni.kit.menu.utils.add_menu_items(self._menu, name=UsdSearchWindowExtension.MENU_GROUP)

        self._app_ready_sub = (
            omni.kit.app.get_app().get_startup_event_stream().create_subscription_to_pop_by_type(
                omni.kit.app.EVENT_APP_READY, self._app_started, name=f"{self._ext_name} app start trigger"
            )
        )

    def _app_started(self, payload):
        """Runs when UI finishes building (for successful docking)."""
        self.toggle_window(self._open, True)

    def _is_visible(self) -> bool:
        """Used by menuitem to set checked state."""
        return False if self._window is None else self._window.get_visible()

    def _menu_toggle_window(self):
        """Callback for menuitem to toggle window."""
        self.toggle_window(False if self._is_visible() else True)

    def _visibility_changed_fn(self, visible):
        """Callback when visibility changes (ie: pressing close button)."""
        # Refresh menu item checked state (via self._is_visible)
        omni.kit.menu.utils.refresh_menu_items(UsdSearchWindowExtension.MENU_GROUP)
        # Update the setting to remember window visibility on app start.
        self._settings.set(PREFIX + "/" + self._open_pref_name, visible)

    def toggle_window(self, toggled, startup=False):
        """Main function to toggle window and update preferences."""
        asyncio.ensure_future(self._toggle_window_async(toggled, startup))

    async def _toggle_window_async(self, toggled, startup=False):
        """Toggle window if it exists or build if necessary."""
        await omni.kit.app.get_app().next_update_async()
        # If window already initialized, then we just toggled it.
        if self._window:
            self._window.set_visible(toggled)
        # If window is NOT initialized and toggle is True
        elif toggled:
            # Dont create a docked window on startup if no property window exists.
            property_window = ui.Workspace.get_window("Property")
            if (not property_window or not property_window.visible) and startup:
                return
            self._window = UsdSearchWindow(UsdSearchWindowExtension.WINDOW_NAME, width=416, height=562)
            self._window.set_visibility_changed_fn(self._visibility_changed_fn)
            # Determine where the window docks when creating.
            self._window.dockPreference = ui.DockPreference.RIGHT_BOTTOM
            self._window.dock_order = 1
            dock_policy = ui.DockPolicy.DO_NOTHING if startup else ui.DockPolicy.CURRENT_WINDOW_IS_ACTIVE
            self._window.deferred_dock_in("Property", dock_policy)
            # Initialize setting to remember window visibility on app start.
            self._settings.set(PREFIX + "/" + self._open_pref_name, toggled)

    def on_shutdown(self):
        """Runs once when extension is shutting down."""
        logger.info("Shutting Down")
        omni.kit.menu.utils.remove_menu_items(self._menu, name=UsdSearchWindowExtension.MENU_GROUP)
        self._menu = None
        self._app_ready_sub = None
        self._setings = None
        if self._window:
            self._window.destroy()
            self._window = None
