from fastai import *
from fastai.vision import *
import fastai

from io import BytesIO
from typing import List, Dict, Union, ByteString, Any

import flask
from flask import Flask
import requests
import torch
import json

app = Flask(__name__)


def load_model(classes: List[str], path=".", model_name="final"
               , architecture=models.resnet50
               , image_size=224) -> ClassificationLearner:
    data = ImageDataBunch.single_from_classes(path, classes
                                              , tfms=get_transforms()
                                              , size=image_size).normalize(imagenet_stats)
    learn = create_cnn(data, architecture)
    learn.load(model_name)
    return learn


def load_image_url(url: str) -> Image:
    response = requests.get(url)
    img = open_image(BytesIO(response.content))
    return img


def load_image_bytes(raw_bytes: ByteString) -> Image:
    img = open_image(BytesIO(raw_bytes))
    return img


def predict(img, n: int = 3) -> Dict[str, Union[str,List]]:
    pred_class, pred_idx, outputs = model.predict(img)
    pred_probs = outputs/sum(outputs)
    pred_probs = pred_probs.tolist()
    predictions = []
    for image_class, output, prob in zip(model.data.classes, outputs.tolist(), pred_probs):
        output = round(output, 1)
        prob = round(prob,2)
        predictions.append(
            {"class": image_class.replace("_", " "), "output": output, "prob": prob}
        )

    predictions = sorted(predictions, key=lambda x: x["output"], reverse=True)
    predictions = predictions[0:n]
    return {"class": pred_class, "predictions": predictions}


@app.route('/api/classify', methods=['POST', 'GET'])
def upload_file():
    if flask.request.method == 'GET':
        url = flask.request.args.get("url")
        img = load_image_url(url)
    else:
        bytes = flask.request.files['file'].read()
        img = load_image_bytes(bytes)
    res = predict(img)
    return flask.jsonify(res)


@app.route('/api/classes', methods=['GET'])
def classes():
    classes = sorted(CLASSES)
    return flask.jsonify(classes)


@app.route('/ping', methods=['GET'])
def ping():
    return "pong"


@app.route('/')
def index():
    return flask.render_template('index.html')


with open('models/classes.txt', 'r') as filehandle:
    CLASSES = json.load(filehandle)
model = load_model(CLASSES)

if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)
    if "prepare" not in sys.argv:
        app.jinja_env.auto_reload = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.run(debug=True, host='0.0.0.0', port=port)
        # app.run(host='0.0.0.0', port=port)
