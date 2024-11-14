# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

__all__ = ["USDSearchImageWidget"]

import asyncio
import logging
from typing import List

import omni.ui as ui
from omni.ui import color as cl

logger = logging.getLogger(__name__)

# Define colors
cl.bg = cl.shade(cl("#00000000"))
cl.tool_bg = cl.shade(cl("#303030ff"))
cl.sel = cl.shade(cl("#4a90e2"))
cl.label = cl.shade(cl("#ffffff"))
cl.item_pressed = cl.shade(cl("#ffffff"))
cl.item_hovered = cl.shade(cl("#d4d4d4"))
cl.item_dim = cl.shade(cl("#b6b6b6"))
cl.item_bg = cl.shade(cl("#1a1919ff"))


class USDSearchImageWidget:
    """
    Creates an image widget grid array for USD Search Results.
    """
    def __init__(
        self, query: str, service_url, images: List[str], usd_paths: List[str], bounding_boxs: List[list] = [], status=None, *args, **kwargs
    ):
        self._frame = ui.Frame(*args, **kwargs)
        self._query = query
        self._service_url = service_url
        self._image_preview = None
        self._images = images
        self._usd_paths = usd_paths
        self._bounding_boxs = bounding_boxs
        self._selected_items = set()
        self._image_frames = {}
        self._status = status

        self._w = 162
        self._h = 162
        self._pad = 4
        self._results_label = None

        self._build_ui()

    def _build_ui(self):
        with self._frame:
            with ui.VStack(height=16):
                ui.Spacer(height=self._pad)
                # Make results / status label.
                if len(self._images) > 0:
                    results_text = f'Found {len(self._images)} Assets for "{self._query}"\nfrom {self._service_url}'
                else:
                    results_text = f'No matches for "{self._query}" - try warehouse terms.'

                if self._status is not None:
                    results_text = str(self._status)

                self._results_label = ui.Label(results_text, style={"font_size": 16}, alignment=ui.Alignment.CENTER_TOP)
                self._results_label.visible = (self._query != "" or self._status is not None)
                # Make image item grid.
                ui.Spacer(height=self._pad)
                with ui.VGrid(height=0, column_width=self._w, row_height=self._h, spacing=self._pad * 4, padding=0) as self._grid:
                    for i, image in enumerate(self._images):
                        self._build_image_item(i, image)
                # Deselect all trigger.
                self._grid.set_mouse_released_fn(self._on_background_click)

    def _build_image_item(self, index: int, image: str):
        with ui.ZStack(content_clipping=True, selected=False) as frame:
            self._image_frames[index] = frame
            ui.Rectangle(
                style={
                    "background_color": cl.bg,
                    "border_width": 3,
                    "border_radius": 4,
                    ":checked": {"border_color": cl.sel},
                }
            )
            with ui.VStack():
                # Top Padding
                ui.Spacer(height=self._pad)
                with ui.HStack():
                    # Left Padding
                    ui.Spacer(width=self._pad)
                    # ZStack with label above image
                    with ui.ZStack(style={"Tooltip": {"background_color": cl.tool_bg}}):
                        file_url = self._usd_paths[index]
                        short_url = file_url.split("/")[-1].rsplit(".", 1)[0]
                        # Create thumbnail
                        img = ui.Image(image, width=self._w - self._pad * 2, height=self._h - self._pad * 2)
                        img.set_mouse_released_fn(lambda x, y, b, m, idx=index: self._on_image_click(x, y, idx, b, m))
                        self._set_drag_fn(img, index)
                        # Shorten url  to keep label from overflowing
                        if len(short_url) > 22:
                            short_url = short_url[:20] + ".."
                        # Label at the bottom of item
                        ui.Label(
                            f"{short_url}", style={"font_size": 14, "color": cl.label},
                            tooltip=file_url, alignment=ui.Alignment.CENTER_BOTTOM
                        )
                    # Right Padding
                    ui.Spacer(width=self._pad)
                # Bottom Padding
                ui.Spacer(height=self._pad)

    def _on_image_click(self, x, y, index: int, button: int, modifier):
        # Handle item selection and context menu
        if button == 0:  # Left click
            frame = self._image_frames[index]
            if (
                frame.screen_position_x < x < frame.screen_position_x + frame.computed_content_width
                and frame.screen_position_y < y < frame.screen_position_y + frame.computed_content_height
            ):
                self._image_frames[index].checked = not self._image_frames[index].checked
                if self._image_frames[index].checked:
                    self._selected_items.add(index)
                else:
                    if index in self._selected_items:
                        self._selected_items.remove(index)

        elif button == 1:  # Right click
            self._show_context_menu(index)

    def _on_background_click(self, x, y, button, modifier):
        # Clear item selection
        if (
            self._grid.screen_position_x < x < self._grid.screen_position_x + self._grid.computed_content_width
            and self._grid.screen_position_y < y < self._grid.screen_position_y + self._grid.computed_content_height
        ):

            if button == 0:  # Left click
                import copy
                _selections = copy.copy(self._selected_items)

                async def __delay_unselect():
                    import omni.kit.app
                    await omni.kit.app.get_app().next_update_async()
                    # Only deselect all if no selection changed
                    if self._selected_items == _selections:
                        for index in range(len(self._image_frames)):
                            self._image_frames[index].checked = False

                        self._selected_items.clear()

                asyncio.ensure_future(__delay_unselect())

    def _set_drag_fn(self, image_widget: ui.Image, index: int):
        def _get_drag_data(index):
            thumbnail = self._images[index]
            ui.ImageWithProvider(thumbnail, width=self._w, height=self._h)

            selected_urls = (
                [self._usd_paths[i] for i in self._selected_items] if self._selected_items else [self._usd_paths[index]]
            )
            return "\n".join(selected_urls)

        image_widget.set_drag_fn(lambda: _get_drag_data(index))

    def _show_context_menu(self, index: int):
        item_style = {
            "MenuItem": {"color": cl.item_dim, "background_selected_color": cl.item_bg},
            "MenuItem:selected": {"color": cl.item_hovered},
            "MenuItem:pressed": {"color": cl.item_pressed},
        }
        self._menu = ui.Menu(style=item_style)
        with self._menu:
            ui.MenuItem("Copy URL", triggered_fn=lambda: self._copy_url(index))
        self._menu.show()

    def _copy_url(self, index: int):
        import omni.kit.clipboard as clipboard

        urls = [self._usd_paths[i] for i in self._selected_items] if self._selected_items else [self._usd_paths[index]]
        # print(f"Copying URLs: {urls}")
        # build a url string with the selected urls separated by new lines
        url = "\n".join(urls)
        clipboard.copy(url)
