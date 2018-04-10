#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import numpy as np
import PIL
import io
from HiveModel import HiveModel
import redis, json

image_id = 0
model = HiveModel(path='../data/128x128')

# connect to redis
r = redis.StrictRedis(host='localhost', port=6379)

app = Flask(__name__, static_url_path='/static')
CORS(app)

@app.route("/")
def hello():
    return render_template('realtime.html')

@app.route("/task")
def get_task():
    global image_id, model

    image_url = 'http://localhost:5000/image/%d' % image_id
    data = {
        'image': image_url,
        'image_id': image_id,
        'labels': model._classes,
    }

    # loop trough all images in dataset
    image_id += 1
    if image_id >= len(model._train_images):
        image_id = 0

    return jsonify(data)

@app.route("/status")
def get_status():
    acc = r.lrange('accuracies', 0, 10)
    acc = np.array(acc).astype('float')
    print(acc)
    mean = np.mean(acc)

    data = {
        'accuracy': mean,
    }

    return jsonify(data)

@app.route("/label", methods=['POST'])
def post_label():
    global r

    data = request.get_json()
    #print (data)
    #model.label(data['image_id'], data['class_id'])
    r.publish('labels', json.dumps(data))

    data['result'] = 'ok'
    return jsonify(data)

@app.route("/image/<int:image_id>")
def get_image(image_id):
    img_data = np.uint8(model._train_images[image_id])
    img = PIL.Image.fromarray(img_data)
    bytes = io.BytesIO()
    img.save(bytes, 'PNG')
    bytes.seek(0)
    return send_file(bytes, mimetype='image/png')
