# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


from .utils.image_handler import ImageHandler
from .utils.ngc_connect import NgcConnect
from .utils.search_models import USDSearchModel
from .utils.image_widget import USDSearchImageWidget

__all__ = ["UsdSearchWindow"]

import omni.client
import carb
import omni.ui as ui
import logging
import asyncio

logger = logging.getLogger(__name__)


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
        self._visiblity_changed_listener = None
        self._image_handler = ImageHandler()
        self._query_model = ui.SimpleStringModel()
        self._ngc_connect = NgcConnect()
        self._status = None
        self._default_status = "Enter an office / warehouse related description."
        self._last_query = None

        # These are default parameters for USD Search API
        self._payload = {
            "description": None,
            "limit": 30,
            "cutoff_threshold": 1.05,
            "return_images": True,
            "return_metadata": False,
            "return_root_prims": True,
            "return_predictions": False,
            "file_extension_include": "usd*"
        }

        # Use to switch to raw bytes instead of saving/loading image
        # self._image_provider = ui.ByteImageProvider()

        # Set function that will be called when window is visible
        self.frame.set_build_fn(self._build_fn)

    def update_payload(self, query):
        self._payload["description"] = query
        return

    def destroy(self):
        self._visiblity_changed_listener = None
        # Will destroy all children
        super().destroy()

    def _build_fn(self):
        """
        Method that is called to auto build UI when visible.
        """
        self._status = self._default_status
        self.rebuild_ui()

    def set_visibility_changed_listener(self, listener):
        self._visiblity_changed_listener = listener

    def rebuild_ui(self):
        # Defer window updates until queries are completed.
        asyncio.ensure_future(self._rebuild_ui_async())

    async def _rebuild_ui_async(self):
        # Wait for next update
        await omni.kit.app.get_app().next_update_async()

        # Triggered by search button.
        def on_click_request():
            self.on_send_server_request()

        # Triggered by pressing enter in query field.
        def on_query_changed(model):
            self.on_send_server_request()

        # Triggered by reset button.
        def on_reset():
            self._query_model.set_value(self._default_prompt)
            self._search_models = []
            self._status = self._default_status
            self.rebuild_ui()

        self._query_model.add_end_edit_fn(on_query_changed)

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

                ui.Spacer(height=5)
                ui.Separator(height=1)

                with ui.ScrollingFrame(
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED
                ):
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
                            USDSearchImageWidget(query, images, usd_paths, status=self._status)

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

    def on_send_server_request(self):

        query = self._query_model.get_value_as_string()
        # dont run the same query again
        if query == self._last_query:
            return

        if query == "":
            # reset to default status
            self._status = self._default_status
            self.rebuild_ui()
            return

        # clear status to allow search results to take over
        self._status = None

        self.update_payload(query)
        self._ngc_connect.set_payload(self._payload)

        # Query via API (requires key) change to _url_ for URL queries (TODO).
        data = self._ngc_connect.send_api_request(self._service_url)

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
        self.rebuild_ui()

    def set_visible(self, value):
        # Good place for visibility/refresh related functionality.
        self.visible = value

    def get_visible(self):
        # Used by menuitem to set checked status.
        return self.visible
