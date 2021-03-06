# Web Image Analytics Tool
First developed at a Design Sprint @ [Trusted Media Summit 2018](https://events.withgoogle.com/apac-trusted-media-summit-2018/)


## Overview

This repository contains two main tools:

* `server.py` - **REST API endpoint, developed at the Design Sprint**
  This takes in a JSON file (with an embedded base64 encoded image) and return a list of image results with corresponding metadata (country of origin etc.)
* `app.py` - **Dash WebApp which allows you to upload an image, crop, and plot image results on a timeline**

### User journey
The user wants to check an image-meme that is being circulated on social media or messaging platforms. 

He downloads the image-meme into his picture library. Then he opens up our web-app and uploads the image-meme to the web app. [(GitHub Repo for the Web App)](https://github.com/zarkhaari/fact-check-fe)

The web-app provides a default cropping region. The drags the cropping tool so that it covers exactly the picture. There are also options to flip the image and/or rotate the image.

The user confirms the crop. The image is sent to an online server (us!), where cropping is done. Then the server relays the cropped image to Google Vision API for reverse image search. We receive results from Google Vision API. 

## Other Technical Details

Everything is run server-side. The below are instructions for running the REST API endpoint.

### Quick Install Guide

Prerequisites:

* Ubuntu environment is preferred
* `sudo apt install python3-dev python3-pip python3-tk libsm6 libxext6 libfreeimage-dev`

1. `git clone https://github.com/tlkh/webimages-analytics-tool`
2. `sudo pip3 install -r requirements.txt`
3. Follow the [instructions to set up Cloud Vision authentication](https://cloud.google.com/vision/docs/libraries#client-libraries-install-python) in your environment
4. `python3 server.py -p 9000` to run the server at `localhost:9000`
5. Test your server with Postman

### The INPUT
Our server will receive a JSON file. 

```
{
    "imageData": "sk\djgdfku\h\s\kfh...in..base64",
    "x": "0",
    "y": "0",
    "width": "32", 
    "height": "100",
    "scaleX": "0",
    "scaleY": "0",
    "rotate": "90",
    "lang": "en"
}
```

The JSON file contains imageData, which is the image in base64 format, and cropping instructions contains the starting xy coordinates and the width and height. `lang` is the language of the caption, and having the correct input to the field does greatly improving OCR Language support. The list of supported languages is available here: https://cloud.google.com/vision/docs/languages

### The PROCESS
We will first parse the JSON file with `do_POST` in `server.py` into a Python dictionary. This Python dictionary is then passed into `parse_crop_instructions` in `image_processing.py`, and it returns a cropped image, which is a numpy array. This numpy array is sent to Google Cloud Vision API. 

The Google Cloud Vision API will return a JSON file containing information about the picture. A demonstration is available on their site. https://cloud.google.com/vision/ The critical information we want is the related images, as well as the date of publishing. As the API does not return information regarding the publishing date, we worked around it by sending a javascript console request `alert(document.lastModified)` URL hosting the image. We return the time in unix_time format so to allow sorting to be done more easier on the front-end. We will also use a newspaper module to make a summary, and it is part of our output.

Then we will consolidate the information and return the web-app a JSON file.

### The OUTPUT
This is the result when the full image_meme is being selected.

```
{
    "full_matches": [],
    "image_text": [],
    "best_guess": [
        "cadbury hiv"
    ],
    "similar_images": [
        {
            "unix_time": 1532591855,
            "country": "United States",
            "page_url": "https://www.snopes.com/fact-check/cadbury-hiv-arrest/",
            "page_title": "FACT CHECK: Are Cadbury Products Contaminated with HIV?",
            "page_summary": "CLAIMA worker at Cadbury plant was arrested for contaminating the company's products with HIV-infected blood.\nRATINGORIGINClaiming that various company's food products have somehow become contaminated with HIV/AIDS has been a prevalent form of hoax for many years, targeting foodstuffs from pineapples to canned goods to soft drinks.\nA more recent wrinkle in that decades-old trope posited in 2018 that an employee of Cadbury, a British multinational confectionery company, was arrested for "adding his HIV-infected blood" to the company's products:This rumor was nothing more than a variant of an old hoax that was previously aimed at Pepsi, with virtually no difference other than the substitution of one company's name for another's:No warnings have been issued, nor any arrests made, in conjunction with a supposed HIV contamination of Cadbury products, and as we noted in a similar previous article, the possibility of such an occurrence's taking place is low to non-existent:",
            "image_url": "https://i1.wp.com/verifykhabar.com/wp-content/uploads/2018/03/Cadbury-HIV-arrested.jpg"
        },
        {
            "unix_time": 1520426192,
            "country": "United States",
            "page_url": "https://www.snopes.com/fact-check/cadbury-hiv-arrest/",
            "page_title": "FACT CHECK: Are Cadbury Products Contaminated with HIV?",
            "page_summary": "CLAIMA worker at Cadbury plant was arrested for contaminating the company's products with HIV-infected blood.\nRATINGORIGINClaiming that various company's food products have somehow become contaminated with HIV/AIDS has been a prevalent form of hoax for many years, targeting foodstuffs from pineapples to canned goods to soft drinks.\nA more recent wrinkle in that decades-old trope posited in 2018 that an employee of Cadbury, a British multinational confectionery company, was arrested for "adding his HIV-infected blood" to the company's products:This rumor was nothing more than a variant of an old hoax that was previously aimed at Pepsi, with virtually no difference other than the substitution of one company's name for another's:No warnings have been issued, nor any arrests made, in conjunction with a supposed HIV contamination of Cadbury products, and as we noted in a similar previous article, the possibility of such an occurrence's taking place is low to non-existent:",
            "image_url": "https://www.ayupp.com/img/news/15204cadbury_product_viral.jpg"
        },
        {
            "unix_time": 1520070577,
            "country": "France",
            "page_url": "https://www.snopes.com/fact-check/cadbury-hiv-arrest/",
            "page_title": "FACT CHECK: Are Cadbury Products Contaminated with HIV?",
            "page_summary": "CLAIMA worker at Cadbury plant was arrested for contaminating the company's products with HIV-infected blood.\nRATINGORIGINClaiming that various company's food products have somehow become contaminated with HIV/AIDS has been a prevalent form of hoax for many years, targeting foodstuffs from pineapples to canned goods to soft drinks.\nA more recent wrinkle in that decades-old trope posited in 2018 that an employee of Cadbury, a British multinational confectionery company, was arrested for "adding his HIV-infected blood" to the company's products:This rumor was nothing more than a variant of an old hoax that was previously aimed at Pepsi, with virtually no difference other than the substitution of one company's name for another's:No warnings have been issued, nor any arrests made, in conjunction with a supposed HIV contamination of Cadbury products, and as we noted in a similar previous article, the possibility of such an occurrence's taking place is low to non-existent:",
            "image_url": "https://hoax-net.be/wp-content/uploads/2018/02/2018-HIV-3.jpg"
        }
    ],
    "partial_matches": [
        {
            "unix_time": 1532579640,
            "country": "United States",
            "page_url": "https://www.snopes.com/fact-check/cadbury-hiv-arrest/",
            "page_title": "FACT CHECK: Are Cadbury Products Contaminated with HIV?",
            "page_summary": "CLAIMA worker at Cadbury plant was arrested for contaminating the company's products with HIV-infected blood.\nRATINGORIGINClaiming that various company's food products have somehow become contaminated with HIV/AIDS has been a prevalent form of hoax for many years, targeting foodstuffs from pineapples to canned goods to soft drinks.\nA more recent wrinkle in that decades-old trope posited in 2018 that an employee of Cadbury, a British multinational confectionery company, was arrested for "adding his HIV-infected blood" to the company's products:This rumor was nothing more than a variant of an old hoax that was previously aimed at Pepsi, with virtually no difference other than the substitution of one company's name for another's:No warnings have been issued, nor any arrests made, in conjunction with a supposed HIV contamination of Cadbury products, and as we noted in a similar previous article, the possibility of such an occurrence's taking place is low to non-existent:",
            "image_url": "https://us-east-1.tchyn.io/snopes-production/uploads/2017/08/pepsicrime.jpg"
        },
        {
            "unix_time": 1532573962,
            "country": "United States",
            "page_url": "https://www.snopes.com/fact-check/cadbury-hiv-arrest/",
            "page_title": "FACT CHECK: Are Cadbury Products Contaminated with HIV?",
            "page_summary": "CLAIMA worker at Cadbury plant was arrested for contaminating the company's products with HIV-infected blood.\nRATINGORIGINClaiming that various company's food products have somehow become contaminated with HIV/AIDS has been a prevalent form of hoax for many years, targeting foodstuffs from pineapples to canned goods to soft drinks.\nA more recent wrinkle in that decades-old trope posited in 2018 that an employee of Cadbury, a British multinational confectionery company, was arrested for "adding his HIV-infected blood" to the company's products:This rumor was nothing more than a variant of an old hoax that was previously aimed at Pepsi, with virtually no difference other than the substitution of one company's name for another's:No warnings have been issued, nor any arrests made, in conjunction with a supposed HIV contamination of Cadbury products, and as we noted in a similar previous article, the possibility of such an occurrence's taking place is low to non-existent:",
            "image_url": "https://us-east-1.tchyn.io/snopes-production/uploads/2018/02/cadburyhiv.jpg"
        }
    ]
}
```


# How to run
In the same folder, run `python3 server.py`. You should see this line:
```Thu Jul 26 15:16:28 2018 Server Starts - 0.0.0.0:9000```

We will use Postman to test APIs. If the response is as expected, the front end should receive the same response as well. I shall not explain step by step installation as I managed to get it work by seeing Timothy (the main contributor to this repo) doing it. It is best to show how it is done with a picture.

![postman_result](./JSON_examples/postman_result.png)
You can see an IP address and its port. The IP address is the Google Cloud VM's IP address, which you can retrived from the Compute Engine console. In the first large text box it an field for JSON entry. In the screenshot it contains a JSON POST example `./JSON_examples/example_POST.json`. I pressed the blue send button, and after some time it returns the second large text box. The details and specifications of the input and output JSON file is elaborated in the eariler sections.


## Future Work 
These are not part of our prototype, but are very achievable functions that could be devised and integrated into our platform.

### Image Artefacts Removal
Following is a complaint by fact-checkers: When images added with added artefacts (such as arrows) are fed into Google reverse image search, images with the same added artefacts are returned. The intention was to find the original picture without the artefacts. However, as the edited picture is far more popular than the original picture, the original picture is buried deep within the search result. 

There is value in removing artefacts through machine learning. Similar work has been done to fill up missing patches of any picture with autoencoders. The current progress can be seen here. The removal of arrows and "warning" text has been quite successful: https://github.com/tlkh/edited-photo-autoencoder

### Universal Meme Segmentation
An example-based solution (machine learning) to image segmentation is appreciated. Our working experiment used a rule-based solution with OpenCV. <!-- Include an explanation of the method? -->
