# USD Search Samples

A collection of code samples for interfacing with `USD Search API`. 

>  **NOTE** : These scripts are intended only for demonstration purposes. They don't show full functionality of USD Search (e.g. image-based search is not supported). In order to experience the complete USD Search API functionality, please install the USD Search API helm chart as described in [USD Search API documentation](https://docs.omniverse.nvidia.com/services/latest/services/usd-search/get-started.html). 

In order to extend it please refer to the [client library](https://github.com/NVIDIA-Omniverse/usdsearch-client).


## Overview

`USD Search API` is a collection of cloud-native microservices that enable developers, creators, and workflow specialists to efficiently search through vast collections of OpenUSD data, images, and other assets using natural language or image-based inputs. 

With these production-ready microservices, developers can deploy USD Search API onto their own infrastructure.  With USD Search API’s artificial intelligence (AI) features, you can quickly locate untagged and unstructured 3D data and digital assets, saving time navigating unstructured, untagged 3D data. USD Search API is capable of searching and indexing 3D asset databases, as well as navigating complex 3D scenes to perform spatial searches, without requiring manual tagging of assets.


### Included Extensions

- [**USD Search Window**](exts/omni.kit.window.usd_search#overview) - a simple, dockable UI for **GUI Kit Apps**. This extension is a demonstration of how to integrate an API endpoint to a front-end experience. 
    * It does not show complete USD Search API functionality. 
    * In order to extend it please refer to the [client library and API documentation](https://github.com/NVIDIA-Omniverse/usdsearch-client) and update the REST API calls in the `send_url_request_async` method of the `omni/kit/window/usd_search/utils/ngc_connect.py` module.


## Installation

The workflow is broken down into key steps :

1) **Obtain API Key** and store in safe location.
2) **Clone and Create Application** *(DO NOT BUILD)*.
3) **Clone and Configure Extensions** from this repo.
4) **Build and Launch** Kit Template Application.


### 1 - Obtain API Key

[**Click to get API Key**](https://build.nvidia.com/nvidia/usdsearch?signin=true&api_key=true) - add to **NVIDIA_API_KEY** `env.variable` **NOW** or `extension.toml` files **LATER**.

>  **NOTE :** *Restart relevant **kit-app terminals** after changing environment variables.*


### 2 - Clone and Create Application

> **CREATE - BUT DON'T BUILD OR LAUNCH APPLICATION**

[**Click for instructions**](https://github.com/NVIDIA-Omniverse/kit-app-template?tab=readme-ov-file#quick-start) - to clone **`kit-app-template`** and create app *(if you haven't already)*. 

> **NOTE :** For this particular sample any Kit App template could be used.


### 3 - Clone and Configure Extensions

Navigate to parent directory of **`kit-app-template`** and clone this extension repo.

> Execute using **powershell** in Windows or **terminal** in Linux / MacOS

```
git clone https://github.com/NVIDIA-Omniverse/usdsearch-samples
```

> **NOTE :** *You may also use **Code** drop-down in repo webpage to extract to desired location.*


#### 3.1 - Copy to kit-app-template

> Using Command Line or File Manager:

Copy contents from `usdsearch-samples/exts/` to `kit-app-template/source/extensions/` (create the folder if it does not exist).

#### 3.2 - Insert API Key

>  You may skip this part if you configured **NVIDIA_API_KEY** environment variable.

Open `config/extension.toml` in each copied folder and look for `Put API Key Here` comment.

Paste your key into quotes and save.

#### 3.3 - Configure Applications

Open new (or existing) **`[kit_app_name].kit`** file in `kit-app-template/source/apps/`

Add the following under `[dependencies]`:
```
"omni.kit.window.usd_search" = {}
```

### 4 - Build and Launch

> Ensure **API Key** is in **NVIDIA_API_KEY** environment variable or extension.toml

[**Click for instructions**](https://github.com/NVIDIA-Omniverse/kit-app-template?tab=readme-ov-file#3-build) - to continue building and launching your kit-application.

> **NOTE:** *You must build `kit-app-template` to register new extensions.*


## Additional Info

Usd Search Documentation - [here](https://docs.omniverse.nvidia.com/usdsearch.html)

Using S3 urls with Omniverse - [here](https://docs.omniverse.nvidia.com/kit/docs/client_library/latest/index.html#s3)

Details on omniverse.toml file - [here](https://docs.omniverse.nvidia.com/launcher/latest/it-managed-launcher/it-managed-installation-overview.html#toml-file)


## License

This repository contains software governed by the [LICENSE](LICENSE.txt) and NVIDIA Omniverse software and materials. NVIDIA Omniverse is governed by the [NVIDIA Agreements | Enterprise Software | NVIDIA Software License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-license-agreement/) and [NVIDIA Agreements | Cloud Services | Service-Specific Terms for NVIDIA Omniverse Cloud](https://www.nvidia.com/en-us/agreements/cloud-services/service-specific-terms-for-omniverse-cloud/). By downloading or using NVIDIA Omniverse, you agree to the NVIDIA Omniverse terms