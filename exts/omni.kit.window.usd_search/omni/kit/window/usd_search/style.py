from pathlib import Path

from omni import ui

CURRENT_PATH = Path(__file__).parent
ICON_PATH = CURRENT_PATH.parent.parent.parent.parent.joinpath("data")

WINDOW_STYLE = {
    "CheckBox": {"background_color": 0xFF9A9A9A, "border_radius": 0},
    "Field::scene_url:disabled": {"color": 0xFF50504E},
}