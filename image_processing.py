import numpy as np
import matplotlib.pyplot as plt
import cv2
import io
import os
import base64
import json
from imageio import imread
import time
import urllib
from urllib.parse import urlparse
import email.utils as eut
import json
import socket
from geolite2 import geolite2
from newspaper import Article
from threading import Thread
from cloud_api_functions import *

# global variables
output = {}
threads_list = []


def base64_decode_image(data):
    try:
        image_data = bytes(data, 'utf-8')
    except Exception as e:
        print(e)
        image_data = data
    try:
        image_raw = base64.decodestring(image_data)
    except Exception as e:
        missing_padding = len(image_data) % 4
        if missing_padding != 0:
            image_data += b'=' * (4 - missing_padding)
        image_raw = base64.decodestring(image_data)
    return image_raw


def parse_crop_instructions(data):
    '''
    input: dict
    output: cropped image
    '''
    
    image_raw = base64_decode_image(data["imageData"])

    image = imread(image_raw)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite("scratch_encoder.jpg", image)

    crop_x = int(data["x"])
    crop_y = int(data["y"])
    crop_w = int(data["width"])
    crop_h = int(data["height"])

    rotate = int(data["rotate"])
    image = rotate_image(image, rotate)

    if crop_w == 0 or crop_h == 0:
        return image

    else:
        ocv_box = [crop_x, crop_y, crop_w, crop_h]
        cropped_image = crop_image(image, ocv_box)
        return cropped_image


class analyse_page():

    def __init__(self):
        pass

    def start(self, page, annotations):
        global threads_list
        self.start_time = time.time()
        t = Thread(target=self.update, args=([page, annotations, False]))
        t.start()
        threads_list.append(t)
        return self

    def update(self, page, annotations, debug):
        global output
        page_url = page.url
        article = Article(page_url)
        article.download()
        article.parse()
        article.nlp()
        page_summary = article.summary
        page_title = article.title
        page_keywords = article.keywords
        if article.publish_date is not None:
            page_published = time.mktime(article.publish_date.timetuple())
        else:
            page_published = "no_date"

        print("Analysing article:", page_title)
        print(page_url)
        for image in page.full_matching_images:
            try:
                img_url = str(image.url).split("?")[0]
                conn = urllib.request.urlopen(img_url, timeout=3)
                date_time = conn.headers['last-modified']
                date_time = eut.parsedate(date_time)
                unixtime = time.mktime(date_time)
                if debug:
                    print("FULL")
                    print(img_url, end="\n: ")
                    print(unixtime)
                ip_a = socket.gethostbyname(urlparse(img_url).netloc)
                reader = geolite2.reader()
                country = reader.get(ip_a)['country']['names']['en']

                output["full_matches"].append({"page_url": page_url, "image_url": img_url, "page_published": page_published,
                                               "page_title": page_title, "page_summary": page_summary, "page_keywords": page_keywords,
                                               "unix_time": unixtime, "country": country})
            except Exception as e:
                if debug:
                    print(e, date_time)

        for image in page.partial_matching_images:
            try:
                img_url = str(image.url).split("?")[0]
                conn = urllib.request.urlopen(img_url, timeout=3)
                date_time = conn.headers['last-modified']
                date_time = eut.parsedate(date_time)
                unixtime = time.mktime(date_time)
                if debug:
                    print(img_url, end="\n: ")
                    print(unixtime)
                ip_a = socket.gethostbyname(urlparse(img_url).netloc)
                reader = geolite2.reader()
                country = reader.get(ip_a)['country']['names']['en']

                output["partial_matches"].append({"page_url": page_url, "image_url": img_url, "page_published": page_published,
                                                  "page_title": page_title, "page_summary": page_summary, "page_keywords": page_keywords,
                                                  "unix_time": unixtime, "country": country})
            except Exception as e:
                if debug:
                    print(e, date_time)

        for image in annotations.visually_similar_images:
            try:
                img_url = str(image.url).split("?")[0]
                conn = urllib.request.urlopen(img_url, timeout=3)
                date_time = conn.headers['last-modified']
                date_time = eut.parsedate(date_time)
                unixtime = time.mktime(date_time)
                if debug:
                    print(img_url, end="\n: ")
                    print(unixtime)
                ip_a = socket.gethostbyname(urlparse(img_url).netloc)
                reader = geolite2.reader()
                country = reader.get(ip_a)['country']['names']['en']

                output["similar_images"].append({"page_url": page_url, "image_url": img_url, "page_published": page_published,
                                                 "page_title": page_title, "page_summary": page_summary, "page_keywords": page_keywords,
                                                 "unix_time": unixtime, "country": country})
            except Exception as e:
                if debug:
                    print(e, date_time)

        self.stop()

    def stop(self):
        self.stopped = True


def ingest_image_disk(file_dir):
    image = cv2.imread(file_dir)
    return image


def base64_encode_image(image):
    encoded_string = base64.b64encode(image_file.read())
    return encoded_string


def geolocate_url(url_):
    ip_a = socket.gethostbyname(urlparse(url_).netloc)
    reader = geolite2.reader()
    country = reader.get(ip_a)['country']['names']['en']
    return ip_a, country


def crop_image(image, ocv_box):
    [x, y, w, h] = ocv_box
    cropped = image[y:y+h, x:x+w]
    return cropped


def hflip_image(image):
    hflip = cv2.flip(image.copy(), 0)
    return hflip


def vflip_image(image):
    vflip = cv2.flip(image.copy(), 1)
    return vflip


def plot_cv_image(image):
    plt.axis("off")
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.show()


def suggest_smart_crop(img, num_boxes, debug=False):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    thresh_gray = int(np.average(gray))
    ret, thresh = cv2.threshold(gray, thresh_gray, 255, cv2.THRESH_BINARY_INV)

    im2, contours, hierarchy = cv2.findContours(
        thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    img_ann = np.copy(img)
    draft_boxes = []
    boxes_size = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 100 or h > 100:
            cv2.rectangle(img_ann, (x, y), (x+w, y+h), (0, 0, 255), 3)
            draft_boxes.append([x, y, w, h])
            boxes_size.append(int(w*h))

    output_boxes = []

    boxes_size.sort()
    thres_box_size = boxes_size[-num_boxes] - 1

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if (int(w*h)) > thres_box_size:
            output_boxes.append([x, y, w, h])

    if debug:
        plt.figure(1)
        plt.subplot(1, 2, 1)
        plt.axis("off")
        plt.title("Original Image")
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.subplot(1, 2, 2)
        plt.axis("off")
        plt.title("Grayscale Image")
        plt.imshow(cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB))
        plt.show()
        plt.imshow(thresh)
        plt.show()
        plt.imshow(cv2.cvtColor(img_ann, cv2.COLOR_BGR2RGB))
        print(" x,y,w,h:\n", output_boxes)
        print(boxes_size)
        print("Generating output images")
        for i, box in enumerate(output_boxes):
            [x, y, w, h] = box
            output_img = img[y:y+h, x:x+w]
            plt.figure(i)
            plt.title("output_"+str(i)+".jpg; size: " + str(boxes_size[i]))
            plt.axis("off")
            plt.imshow(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB))
            plt.show()

    return output_boxes


def rotate_image(image, rotate):
    rows, cols, ch = image.shape
    M = cv2.getRotationMatrix2D((cols/2, rows/2), rotate, 1)
    image = cv2.warpAffine(image, M, (cols, rows))
    return image


def return_rms_payload(image, lang, num_results, debug=False):
    global output
    print("=====")
    file_name = "/tmp/"+str(time.time())+".jpg"
    print("Logged image:", file_name)
    cv2.imwrite(file_name, image)

    num_results = int(num_results)

    text_ann = detect_text(file_name, lang)
    annotations = detect_web(file_name, num_results, True)

    output = {}
    output["results"] = False
    output["full_matches"] = []
    output["partial_matches"] = []
    output["similar_images"] = []
    output["best_guess"] = []
    output["image_text"] = text_ann

    if annotations.best_guess_labels:
        for label in annotations.best_guess_labels:
            output["best_guess"].append(label.label)

    global threads_list

    threads_list = []
    for page in annotations.pages_with_matching_images:
        print("Analysing", page.url)
        analyse_page().start(page, annotations)

    print("\nNumber of threads:")
    print(len(threads_list))
    print("Waiting...")
    [t.join() for t in threads_list]
    print("All threads completed!")

    if (len(output["full_matches"])+len(output["partial_matches"])+len(output["similar_images"])) < 1:
        output["results"] = False
        output["errors"] = "No images can be found by GCP Vision API"
    else:
        output["results"] = True

    return json.dumps(output)
