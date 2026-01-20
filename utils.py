import cv2
import numpy as np
from PIL import Image
from tensorflow.keras.applications.vgg16 import preprocess_input

def load_image_vector(path, size=(16,16)):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, size)
    return img.astype(np.float32).flatten() / 255.0

def preprocess_for_model(path, size=(224,224)):
    img = Image.open(path).convert("RGB").resize(size)
    arr = np.array(img).astype(np.float32)
    return preprocess_input(arr[None, ...])
