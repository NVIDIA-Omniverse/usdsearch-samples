# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


from pathlib import Path
import logging
import omni.kit.app

logger = logging.getLogger(__name__)


class IoHelper:

    def get_extension_path():
        """
        This method will return the actual file system path of the extension
        :return:
        """

        # Identifying extension to receive path to extension
        manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = manager.get_extension_id_by_module(__name__)
        logger.info(f"ID of this extension is {ext_id}")
        # Resolving filesystem path
        extension_path = manager.get_extension_path(ext_id)
        logger.info(f"Extension path is: {extension_path}")
        python_path = Path(extension_path)

        return python_path
