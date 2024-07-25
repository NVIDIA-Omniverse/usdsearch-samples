# USD Search Samples

A collection of code samples for interfacing with `USD Search` API.


## Overview

`USD Search` is an AI-powered search for OpenUSD data, 3D models, images, and assets using text or image input. It is a collection of cloud-native microservices that help users navigate unstructured, untagged 3D data. It is capable of searching and indexing 3D asset databases, searching in-scene, and performing spatial searches, without requiring any manual tagging of assets.


### Included Extensions

- [**USD Search Window**](exts/omni.kit.window.usd_search#overview) - a simple, dockable UI for **GUI Kit Apps**.


## Installation

The workflow is broken down into key steps :

1) **Obtain API Key** and store in safe location.
2) **Clone and Create Application** *(DO NOT BUILD)*.
3) **Clone and Configure Extensions** from this repo.
4) **Build and Launch** Kit Template Application.


### 1 - Obtain API Key

[**Click to get API Key**](https://nvidia.github.io/GenerativeAIExamples/latest/api-catalog.html#get-an-api-key-for-the-accessing-models-on-the-api-catalog) - add to **NVIDIA_API_KEY** `env.variable` **NOW** or `extension.toml` files **LATER**.

>  **NOTE :** *Restart relevant **kit-app terminals** after changing environment variables.*


### 2 - Clone and Create Application

> **CREATE - BUT DON'T BUILD OR LAUNCH APPLICATION**

[**Click for instructions**](https://github.com/NVIDIA-Omniverse/kit-app-template?tab=readme-ov-file#quick-start) - to clone **`kit-app-template`** and create app *(if you haven't already)*.


### 3 - Clone and Configure Extensions

Navigate to parent directory of **`kit-app-template`** and clone this extension repo.

> Execute using **powershell** in Windows or **terminal** in Linux / MacOS

```
git clone https://github.com/NVIDIA-Omniverse/usdsearch-samples
```

> **NOTE :** *You may also use **Code** drop-down in repo webpage to extract to desired location.*


#### 3.1 - Copy to kit-app-template

> Using Command Line or File Manager:

Copy contents from `usdsearch-samples/exts/` to `kit-app-template/source/extensions/`

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