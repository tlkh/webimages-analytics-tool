from google.cloud import vision
from google.cloud.vision import types
import json
import io


def detect_web(path, max_results, return_json=True):
    """Detects web annotations given an image."""
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.web_detection(image=image, max_results=max_results)
    annotations = response.web_detection

    if return_json:
        return annotations

    else:
        if annotations.best_guess_labels:
            for label in annotations.best_guess_labels:
                print('\nBest guess label: {}'.format(label.label))

        if annotations.pages_with_matching_images:
            print('\n{} Pages with matching images found:'.format(
                len(annotations.pages_with_matching_images)))

            for page in annotations.pages_with_matching_images:
                print('\n\tPage url   : {}'.format(page.url))

                if page.full_matching_images:
                    print('\t{} Full Matches found: '.format(
                        len(page.full_matching_images)))

                    for image in page.full_matching_images:
                        print('\t\tImage url  : {}'.format(image.url))

                if page.partial_matching_images:
                    print('\t{} Partial Matches found: '.format(
                        len(page.partial_matching_images)))

                    for image in page.partial_matching_images:
                        print('\t\tImage url  : {}'.format(image.url))

        if annotations.web_entities:
            print('\n{} Web entities found: '.format(
                len(annotations.web_entities)))

            for entity in annotations.web_entities:
                print('\n\tScore      : {}'.format(entity.score))
                print(u'\tDescription: {}'.format(entity.description))

        if annotations.visually_similar_images:
            print('\n{} visually similar images found:\n'.format(
                len(annotations.visually_similar_images)))

            for image in annotations.visually_similar_images:
                print('\tImage url    : {}'.format(image.url))

    return True


def detect_text(path, lang):
    """Detects text in the file."""
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)
    image_context = types.ImageContext(language_hints=[lang])

    response = client.text_detection(image=image, image_context=image_context)

    texts = response.text_annotations

    output = []

    for text in texts:
        if len(text.description.split(" ")) > 1:
            output.append(text.description)

    return output
