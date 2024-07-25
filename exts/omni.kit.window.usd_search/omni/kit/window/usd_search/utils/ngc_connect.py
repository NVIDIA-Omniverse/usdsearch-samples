# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


import logging
import json
import omni.kit.pipapi
omni.kit.pipapi.install("requests")
import requests

logger = logging.getLogger(__name__)


class NgcConnect:
    """
    Handle search API or URL requests and return JSON data.
    """
    def __init__(self):
        self._headers = None
        self._payload = None
        self._api_key = None
        self._response = None

    def set_api_key(self, api_key):
        self._api_key = api_key
        self.set_headers()

    def set_headers(self):
        self._headers = {
            "Authorization": "Bearer {}".format(self._api_key),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def set_payload(self, payload):
        self._payload = payload

    # #TODO: Make non-blocking
    def send_api_request(self, url):
        """Handle request via API - REQUIRES KEY"""

        if not self._payload.get("description", None):
            return

        if self._api_key is None:
            import carb.settings

            settings = carb.settings.get_settings().get("/exts/omni.kit.window.usd_search/nvidia_api_key")
            if settings:
                self._api_key = settings
            else:
                # Get from NVIDIA_API_KEY environment variable
                import os

                self._api_key = os.environ.get("NVIDIA_API_KEY")
                if self._api_key is None:
                    logger.error("NVIDIA_API_KEY is required for URL request")

        self.set_headers()
        self._payload = json.dumps(self._payload)
        logger.info(f"Invoked URL: {url}")
        logger.info(f"Headers used: {self._headers}")
        logger.info(f"Payload used: {self._payload}")
        try:
            # Send the GET request
            self._response = requests.post(url, headers=self._headers, data=self._payload)
            self._response.raise_for_status()  # Raise an exception for non-200 status codes
            logger.info(f"Response Code: {self._response.status_code}")
            result = self._response.json()
            # Process the JSON data (same the images )
            filtered_result = self._process_json_data(result)
            return filtered_result
        except requests.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

    def send_url_request(self, url):
        """Handle request via URL"""

        if not self._payload.get("description", None):
            return

        self.set_headers()
        logger.info(f"Headers used: {self._headers}")

        # Construct the URL with query parameters
        URLP = (url + "?")
        URLP += f'description={self._payload.get("description", "")}&'
        URLP += f'return_metadata={self._payload.get("return_metadata", "False")}&'
        URLP += f'limit={self._payload.get("limit", "30")}&'
        URLP += f'file_extension_include={self._payload.get("file_extension_include", "")}&'
        URLP += f'return_images={self._payload.get("return_images", "True")}&'

        try:
            # Send the GET request
            response = requests.get(URLP)
            response.raise_for_status()  # Raise an exception for non-200 status codes
            result = response.json()

            # Process the JSON data (same the images )
            filtered_result = self._process_json_data(result)
            return filtered_result
        except requests.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

    def _process_json_data(self, json_data):
        """Process the JSON data returned by USD Search API."""
        for item in json_data:
            # replace search server with content server
            item["url"] = item["url"].replace(
                "s3://deepsearch-demo-content/",
                "https://omniverse-content-production.s3.us-west-2.amazonaws.com/"
            )
            # optionally store images in temp location
            """
            import base64
            import tempfile
            if "image" in item:
                # Create a temporary file in the system's temp directory
                with tempfile.NamedTemporaryFile(prefix="temp_", suffix=".png", delete=False) as temp_file:
                    # Decode the base64 image data and write it to the temp file
                    image_data = base64.b64decode(item["image"])
                    temp_file.write(image_data)
                    full_path = temp_file.name

                # Replace the base64 encoded image with the file path
                item["image"] = full_path

                if "bbox_dimension_x" in item:
                    item["bbox_dimension"] = [
                        item["bbox_dimension_x"],
                        item["bbox_dimension_y"],
                        item["bbox_dimension_z"],
                    ]
            """

        clean_json_data = []
        for item in json_data:
            new_item = {}
            # Remove any other keys that we dont care about
            for key in item.keys():
                if key in ["url", "image", "bbox_dimension"]:
                    new_item[key] = item[key]

            clean_json_data.append(new_item)

        return clean_json_data
