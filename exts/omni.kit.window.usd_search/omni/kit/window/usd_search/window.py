# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


from .utils.animate_widget import AnimateWindget
from .utils.image_handler import ImageHandler
from .utils.image_widget import USDSearchImageWidget
from .utils.ngc_connect import NgcConnect
from .utils.search_models import USDSearchModel

__all__ = ["UsdSearchWindow"]

import asyncio
import logging
from typing import Optional

import carb
import omni.client
import omni.ui as ui

from .style import WINDOW_STYLE

logger = logging.getLogger(__name__)


class FieldState:
    """
    Manages the state of a field (input box) in the UI.
    """

    def __init__(self, on_enter_pressed: callable):
        """
        Initializes a new instance of FieldState.

        Args:
            on_enter_pressed (function): A callback function when enter pressed.
        """
        self._on_enter_pressed = on_enter_pressed

        app_window = omni.appwindow.get_default_app_window()
        self._key_input = carb.input.acquire_input_interface()
        self._keyboard = app_window.get_keyboard()

        self._loop_task = None
        self._loop_event = None
        self.model = None
        self.edit = False

        self._image_path = None  # TODO: want some more general container for attachments

    def __del__(self):
        """
        Deletes the instance of FieldState & cancels any running tasks, if any.
        """
        self.destroy()

    def destroy(self):
        if self._loop_event is not None:
            self._loop_event.set()

        if self._loop_task is not None:
            self._loop_task.cancel()

        self._on_enter_pressed = None

    @property
    def edit(self):
        """
        Returns the editing state of the field.

        Returns:
            bool: True if the field is being edited, False otherwise.
        """
        return self._edit

    @edit.setter
    def edit(self, value):
        """
        Sets the editing state of the field & starts/stops the loop task accordingly.

        Args:
            value (bool): The new editing state of the field.
        """
        self._edit = value
        if value and self._loop_task is None:
            if self._loop_event is not None:
                self._loop_event.set()

            self._loop_event = asyncio.Event()

            self._loop_task = asyncio.ensure_future(self._loop(self._loop_event))
        elif not value and self._loop_task is not None:
            self._loop_event.set()
            self._loop_event = None
            self._loop_task.cancel()
            self._loop_task = None

    def send_message_on_enter(self):
        """
        Sends a message from the input field to the callback.
        """
        if not self.model:
            return

        self._on_enter_pressed()

    async def _loop(self, loop_event):
        """
        Updates the state of the input field as long as the field is being edited.
        Sends a message from the field once Enter is pressed.
        """
        while True:
            await omni.kit.app.get_app().next_update_async()

            KeyboardInput = carb.input.KeyboardInput
            key_input = self._key_input

            def is_key_down(key):
                return key_input.get_keyboard_button_flags(self._keyboard, key) & carb.input.BUTTON_FLAG_DOWN

            enter_pressed = is_key_down(KeyboardInput.ENTER) or is_key_down(KeyboardInput.NUMPAD_ENTER)
            shift_down = is_key_down(KeyboardInput.LEFT_SHIFT) or is_key_down(KeyboardInput.RIGHT_SHIFT)
            alt_down = is_key_down(KeyboardInput.LEFT_ALT) or is_key_down(KeyboardInput.RIGHT_ALT)
            ctrl_down = is_key_down(KeyboardInput.LEFT_CONTROL) or is_key_down(KeyboardInput.RIGHT_CONTROL)

            if enter_pressed and not (shift_down or alt_down or ctrl_down):
                self.send_message_on_enter()

            if loop_event.is_set():
                break


class UsdSearchWindow(ui.Window):
    """The class that represents the window"""

    def __init__(self, title: str, search_models=[], **kwargs):
        super().__init__(title, **kwargs)

        self._settings = carb.settings.get_settings()
        # This setting is pulled from config/extension.toml
        settings_path = "exts/omni.kit.window.usd_search/host_url"
        self._service_url = self._settings.get(settings_path)
        self._search_models = search_models

        self._default_prompt = ""
        self._visibility_changed_listener = None
        self._image_handler = ImageHandler()
        self._query_model = ui.SimpleStringModel()
        self._ngc_connect = NgcConnect()
        self._status = None
        self._default_status = "Enter an office / warehouse related description."
        self._last_query = None
        self._last_scene_url = None
        self._query_future: Optional[asyncio.Future] = None
        self._search_in_scene_model = ui.SimpleBoolModel(False)
        self._scene_url_model = ui.SimpleStringModel()

        self._field_state = FieldState(self._query)

        # These are default parameters for USD Search API
        self._payload = {
            "description": None,
            "limit": 30,
            "cutoff_threshold": 1.05,
            "return_images": True,
            "return_metadata": False,
            "return_root_prims": False, # There will be "Internal Server Error" for proper instance if True
            "return_predictions": False,
            "file_extension_include": "usd*",
        }

        # Use to switch to raw bytes instead of saving/loading image
        # self._image_provider = ui.ByteImageProvider()

        self.frame.set_style(WINDOW_STYLE)

        # Set function that will be called when window is visible
        self.frame.set_build_fn(self._build_fn)

    def update_payload(self, query: str, scene_url: str):
        self._payload["description"] = query
        self._payload["search_in_scene"] = scene_url
        return

    def destroy(self):
        self._visibility_changed_listener = None
        if self._query_future and not self._query_future.done():
            self._query_future.cancel()
        # Will destroy all children
        super().destroy()

    def _build_fn(self):
        """
        Method that is called to auto build UI when visible.
        """
        self._status = self._default_status
        self.rebuild_ui()

    def set_visibility_changed_listener(self, listener):
        self._visibility_changed_listener = listener

    def rebuild_ui(self):
        # Defer window updates until queries are completed.
        asyncio.ensure_future(self._rebuild_ui_async())

    async def _rebuild_ui_async(self):
        # Wait for next update
        await omni.kit.app.get_app().next_update_async()

        # Triggered by search button.
        def on_click_request():
            self._query()

        # Triggered by pressing enter in query field.
        def on_query_changed(model):
            self._query()

        # Triggered by reset button.
        def on_reset():
            if self._query_future and not self._query_future.done():
                self._query_future.cancel()
            self._last_scene_url = None
            self._last_query = None
            self._query_model.set_value(self._default_prompt)
            self._search_models = []
            self._status = self._default_status
            self._scene_url_model.set_value("")
            self._search_in_scene_model.set_value(False)
            self.rebuild_ui()

        self._query_model.add_begin_edit_fn(self._on_begin_edit)
        self._query_model.add_end_edit_fn(self._on_end_edit)

        with self.frame:
            with ui.VStack():
                with ui.HStack(height=22, spacing=0):
                    ui.Spacer(width=4)
                    with ui.VStack():
                        ui.Spacer()
                        tooltip = 'Descriptive search ex: "cardboard box", "red chairs", etc.'
                        ui.StringField(height=22, tooltip=tooltip, model=self._query_model, multiline=False)
                        ui.Spacer()
                    ui.Spacer(width=2)
                    ui.Button("Search", height=18, width=70, clicked_fn=on_click_request)
                    ui.Button("Reset", height=18, width=70, clicked_fn=on_reset)

                with ui.HStack(height=22, spacing=0):
                    ui.Spacer(width=4)
                    with ui.VStack(width=0):
                        ui.Spacer()
                        ui.CheckBox(self._search_in_scene_model, height=0)
                        ui.Spacer()
                    ui.Spacer(width=4)
                    ui.Label("Search in scene", width=0, mouse_pressed_fn=lambda x, y, btn, flag: self._search_in_scene_model.set_value(not self._search_in_scene_model.as_bool))
                    ui.Spacer(width=4)
                    self._scene_url_field = ui.StringField(self._scene_url_model, height=22, visible=self._search_in_scene_model.as_bool, name="scene_url")
                    ui.Spacer(width=4)

                ui.Spacer(height=5)
                ui.Separator(height=1)

                with ui.ZStack():
                    with ui.ScrollingFrame(
                        horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                        vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED
                    ) as self._result_frame:
                        with ui.VStack():
                            query = self._query_model.get_value_as_string()
                            with ui.VStack():
                                images = []
                                usd_paths = []
                                for model in self._search_models:
                                    images.append(model.image_url)
                                    usd_paths.append(model.asset_url)
                                    # dont want to deal with bounding boxes for now
                                    # bounding_boxes = [item.get("bbox_dimension", None) for item in data]
                                USDSearchImageWidget(query, self._service_url, images, usd_paths, status=self._status)
                    self._animate_widget = AnimateWindget(visible=False)

        def on_search_in_scene_changed(model):
            self._scene_url_field.visible = model.as_bool
            if model.as_bool:
                if not self._scene_url_model.as_string:
                    usd_context = omni.usd.get_context()
                    if usd_context and not usd_context.is_new_stage():
                        self._scene_url_model.set_value(usd_context.get_stage_url())

            if self._query_future and not self._query_future.done():
                # If searching in progress, restart
                self._query()

        self._search_in_scene_model.add_value_changed_fn(on_search_in_scene_changed)

    def download_s3_asset(self, model):
        """Example of how one would download an S3 asset (unused)."""
        # Initialize the client
        omni.client.initialize()
        logger.info("Downloading Asset URL" + model.asset_url)
        local_path = self._image_handler.get_asset_directory() + model.asset_name
        local_path = local_path.replace("\\", "/")
        # Start the download
        omni.client.copy(model.asset_url, local_path)
        # Shutdown the client
        # omni.client.shutdown()
        return local_path

    # reference usd file
    def on_click_image(self, model):
        logger.info(f"Pressed url: {model.asset_url}")

        # Create a Reference of the Props in the stage
        stage = omni.usd.get_context().get_stage()
        if not stage:
            return

        prim_path = omni.usd.get_stage_next_free_path(stage, "/" + model.asset_name.split(".")[0], True)
        logger.info(f"On Click - Prim Path: {prim_path}")

        asset_path = model.asset_url

        omni.kit.commands.execute(
            "CreateReferenceCommand",
            path_to=prim_path,
            asset_path=asset_path,
            usd_context=omni.usd.get_context(),
        )

    async def on_send_server_request_async(self):
        query = self._query_model.get_value_as_string()
        scene_url = self._scene_url_model.as_string if self._search_in_scene_model.as_bool else ""
        # dont run the same query again
        if query == self._last_query and scene_url == self._last_scene_url:
            return

        if query == "":
            # reset to default status
            self._status = self._default_status
            self.rebuild_ui()
            return

        self._result_frame.visible = False
        self._animate_widget.visible = True

        # clear status to allow search results to take over
        self._status = None

        self.update_payload(query, scene_url)
        self._ngc_connect.set_payload(self._payload)

        # Query via API (requires key) change to _url_ for URL queries (TODO).
        data = await self._ngc_connect.send_api_request_async(self._service_url)

        self._search_models = []
        for bundle in data:
            # Log errors if found
            if bundle == "error":
                logger.error(data["error"])
            # Skip generation of thumbnail if image key is missing (for errors).
            if "image" not in bundle:
                continue
            image = self._image_handler.generate_image_from_string(bundle['image'])
            asset = bundle['url']
            name = asset.split("/")[-1]
            self._search_models.append(USDSearchModel(image, asset, name))
        # To prevent repeating identical queries.
        self._last_query = query
        self._last_scene_url = scene_url
        await self._rebuild_ui_async()

    def set_visible(self, value):
        # Good place for visibility/refresh related functionality.
        self.visible = value

    def get_visible(self):
        # Used by menuitem to set checked status.
        return self.visible

    def _query(self):
        if self._query_future and not self._query_future.done():
            self._query_future.cancel()
        self._query_future = asyncio.ensure_future(self.on_send_server_request_async())

    def _on_begin_edit(self, *args):
        self._field_state.model = self._query_model
        self._field_state.edit = True

    def _on_end_edit(self, *args):
        self._field_state.model = None
        self._field_state.edit = False
