# Copyright 2019-2023 NVIDIA CORPORATION

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

# Extension for writing UI tests (to simulate UI interaction)
import omni.kit.ui_test as ui_test

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.window.usd_search


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class Test(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    # Actual test, notice it is an "async" function, so "await" can be used if needed
    async def test_hello_public_function(self):
        result = omni.kit.window.usd_search.show_window(True)
        self.assertEqual(result, True)

    async def test_window_button(self):

        # Find a label in our window
        label = ui_test.find("Usd Search Window//Frame/**/Label[*]")

        # Find buttons in our window
        search_button = ui_test.find("Usd Search Window//Frame/**/Button[*].text=='Search'")
        reset_button = ui_test.find("Usd Search Window//Frame/**/Button[*].text=='Reset'")

        # Click reset button
        await reset_button.click()
        self.assertEqual(label.widget.text, "")
