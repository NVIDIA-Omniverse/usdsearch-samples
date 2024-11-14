import asyncio

import omni.kit.app
import omni.ui as ui
from omni.ui import color as cl
from omni.ui import scene as sc

from ..style import ICON_PATH


class AnimateWindget():
    def __init__(self, visible: bool = True):
        self._build_ui()

        self._rotate_future = None
        self.visible = visible

    def destroy(self) -> None:
        self.visible = False

    @property
    def visible(self) -> bool:
        return self._frame.visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._frame.visible = value
        if value:
            self._rotate_future = asyncio.ensure_future(self._rotate())
        elif self._rotate_future:
            self._rotate_future.cancel()

    def _build_ui(self) -> None:
        with ui.Frame() as self._frame:
            with sc.SceneView().scene:
                self._transform = sc.Transform()
                with self._transform:
                    sc.Image(f"{ICON_PATH}/nvidia-omniverse-viewer-icon.png")

    async def _rotate(self):
        angle = [0]
        while True:
            delta = await omni.kit.app.get_app().next_update_async()
            angle[0] -= delta
            transform = sc.Matrix44.get_rotation_matrix(0, 0, angle[0])
            self._transform.transform = transform
