# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 10:58:27 2021

@author: DELL
"""
import os
from google.cloud import vision
from google.cloud.vision import types
import io
import pandas as pd
def visionocr(imagePath):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "apikey.json"
    client = vision.ImageAnnotatorClient()

    with io.open(imagePath, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    # Performs text detection on image
    # kwargs = {"image_context": {"language_hints": ["en", "hi", "mr", "bn", "ta"]}}
    # response = client.document_text_detection(image, **kwargs)
    kwargs = {"image_context": {"language_hints": ["en"]}}

    response = client.document_text_detection(image, **kwargs)
    
    response = client.text_detection(image)

    texts = response.text_annotations
    imvertices = []
    for text in texts[1:]:
        vertices = (['{}\t{}'.format(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices])
        vertices = ' '.join(vertices)
        vertices = vertices.split()
        vertices = [int(x) for x in vertices]
        vertices.insert(0, text.description)
        imvertices.append(vertices)
    df = pd.DataFrame(imvertices, columns=['Token', 'x0', 'y0', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3'])
    return df