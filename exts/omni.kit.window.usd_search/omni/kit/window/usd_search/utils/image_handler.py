# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


import base64
from PIL import Image
from io import BytesIO
import omni.kit
import os
from datetime import datetime
from .io import IoHelper
import asyncio
import uuid
import logging

logger = logging.getLogger(__name__)


class ImageHandler:
    # max size of image dimensions in pixels
    # current AI Playground limit is 1000
    MAX_SIZE = 1000

    def __init__(self) -> None:
        self.clear_resized_image_directory()

    # image needs to be resized to meet AI Playground size limit (currently 200 kb, 1000x1000 pixels)
    def resize_image(self, input_image_path, resized_url, size=MAX_SIZE):
        image = Image.open(input_image_path)

        # If the image has an alpha channel, convert it to RGB and replace the alpha channel with a white background
        if image.mode == 'RGBA':
            # Create a blank background image with a white background
            background = Image.new("RGB", image.size, (255, 255, 255))
            # Paste the PNG image onto the background image, using the alpha channel as the mask
            # 3 is the index of the alpha channel
            background.paste(image, mask=image.split()[3])
            image = background

        width, height = image.size

        if width > height:
            max_size = (size, int((height / width) * size))
        else:
            max_size = (int((width / height) * size), size)

        # resize image based on max_size
        resized_image = image.resize(max_size, Image.ANTIALIAS)
        # quality value of 85 should get image under 200kb limit
        # TODO: Loop optmizations until it's below limit
        resized_image.save(resized_url, "JPEG", quality=85, optimize=True)

    def save_image(self):
        image_path = self.get_image_directory()
        self.convert_base64_to_image()
        with open(image_path, "wb") as fh:
            fh.write(base64.decodebytes(self._image_data_bytes))

    # convert to base64 encoding as required by API
    def generate_image_string(self, url):
        with open(url, "rb") as image:
            return base64.b64encode(image.read()).decode()

    def generate_image_from_string(self, image_string):
        image_data = base64.b64decode(image_string.encode('utf-8'))
        image_bytes = BytesIO(image_data)
        image = Image.open(image_bytes)

        # saving out image as workaround for now
        random_str = str(uuid.uuid4())[:8]
        captured_stage_images_directory = os.path.join(self.get_image_directory(), random_str + ".jpg")
        image.save(captured_stage_images_directory)

        # use this to pass along raw bytes in the future
        # pixels = [int(c) for p in image.getdata() for c in p]

        return captured_stage_images_directory

    def prep_image_string(self, input_image_path):
        resized_url = self.get_resized_image_url()
        self.resize_image(input_image_path, resized_url)

        # delete original screenshot
        os.remove(input_image_path)
        logger.info("Image resize complete")

        return (self.generate_image_string(resized_url), resized_url)

    def get_image_directory(self):
        extension_path = IoHelper.get_extension_path()
        return os.path.join(extension_path, "captures/")

    def get_asset_directory(self):
        extension_path = IoHelper.get_extension_path()
        return os.path.join(extension_path, "assets/")

    def get_resized_image_url(self):
        # randomize image name
        current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        captured_stage_images_directory = os.path.join(self.get_image_directory(), current_datetime + ".jpg")

        return captured_stage_images_directory

    # clear image directory on extension launch to prevent images from accumulating
    def clear_resized_image_directory(self):
        directory_path = self.get_image_directory()
        try:
            files = os.listdir(directory_path)
            for file in files:
                file_path = os.path.join(directory_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except OSError:
            logger.error("Error occurred while deleting files.")

    # capture screenshot and return base64 encoded string
    async def on_capture_screenshot(self):
        event = asyncio.Event()

        menu_action_success = False
        capture_screenshot_filepath = None

        def on_capture_callback(success: bool, captured_image_path: str) -> None:
            nonlocal menu_action_success, capture_screenshot_filepath
            menu_action_success = success
            capture_screenshot_filepath = captured_image_path
            event.set()

        # capture the screenshot
        omni.kit.actions.core.execute_action("omni.kit.menu.edit", "capture_screenshot", on_capture_callback)

        # wait for event to complete
        await event.wait()
        # give it an extra buffer to finish up
        await asyncio.sleep(delay=1.0)

        if menu_action_success:
            logger.info(f"screenshot successful {capture_screenshot_filepath}")
            return self.prep_image_string(capture_screenshot_filepath)

        else:
            logger.error("error while completing screenshot")
            return None
