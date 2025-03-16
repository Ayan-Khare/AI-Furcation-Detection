from fastapi import FastAPI, File, UploadFile
import uvicorn
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
from PIL import Image, ImageOps
import io
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import torch
from ultralytics import YOLO  
import logging
import gdown

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

UPLOAD_FOLDER = "uploads/"
IMG_SIZE = (512, 512)
CLASS_LABELS = {0: "With Furcation", 1: "Without Furcation"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


MODEL_DIR = "model"
os.makedirs(MODEL_DIR, exist_ok=True)

# Google Drive file IDs (Replace these with actual file IDs)
MODEL_FILES = {
    "DenseNet201_FT.h5": "1viJkoqpHkQedtPo3dfxsnyyTIiiVlGlO",
    "boneloss_marker.h5": "1BIpY_zH4ySlhjEe0nCzXYhUjgyGPr3Qa",
    "furcation_marker.h5": "1xJ3cAhCvnMxKeBiMim7_IS5RkiOOgQi_",
    "teeth_extractor.pt": "1GJszJvwMVH1oYFrdVhVqaMHoqvf9bp1c",
}

def download_model(model_name, file_id):
    """Download model from Google Drive if not already present."""
    model_path = os.path.join(MODEL_DIR, model_name)
    if not os.path.exists(model_path):
        logging.info(f"Downloading {model_name} from Google Drive...")
        gdown.download(f"https://drive.google.com/uc?id={file_id}", model_path, quiet=False)
    return model_path

# Download models if not present
for model_name, file_id in MODEL_FILES.items():
    download_model(model_name, file_id)


FURCATION_MODEL = load_model("model/DenseNet201_FT.h5")
BONE_LOSS_MODEL = load_model("model/boneloss_marker.h5")
FURCATION_MARKER_MODEL = load_model("model/furcation_marker.h5")
TEETH_EXTRACTOR_MODEL = YOLO("model/teeth_extractor.pt")

app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

def preprocess_image(img, target_size):
    """Preprocess an image for model input."""
    img = img.resize(target_size)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    return img_array

def crop_teeth(image_path, results):
    """Crop the detected tooth region and return the cropped image path."""
    img = Image.open(image_path)
    for result in results[0].boxes.xyxy:
        x1, y1, x2, y2 = map(int, result.tolist())
        cropped_teeth = img.crop((x1, y1, x2, y2))
        cropped_path = os.path.join(UPLOAD_FOLDER, "cropped_teeth.jpg")
        cropped_teeth.save(cropped_path)
        return cropped_path
    return None

def apply_mask(original_img, mask_array):
    """Overlay the model's predicted mask onto the original image."""
    mask_array = np.squeeze(mask_array)
    if mask_array.ndim == 2:
        mask_image = Image.fromarray((mask_array * 255).astype(np.uint8))
    else:
        raise ValueError(f"Incorrect mask shape: Expected (H, W), got {mask_array.shape}")
    
    mask_image = mask_image.resize(original_img.size, Image.LANCZOS).convert("L")
    blended = Image.blend(original_img, ImageOps.colorize(mask_image, black="black", white="red"), alpha=0.5)
    return blended

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    """Process the uploaded image and return model predictions."""
    try:
        # Read and process the uploaded image
        image_data = await file.read()
        img = Image.open(io.BytesIO(image_data)).convert("RGB")
        processed_img = preprocess_image(img, IMG_SIZE)

        # Predict furcation class
        prediction = FURCATION_MODEL.predict(processed_img)[0]  # Ensure it's a 1D array
        print(prediction)
        confidence = float(np.max(prediction))
        print(confidence)
        if confidence > 0.5:
            predicted_class = 1
        else:
            predicted_class = 0  # Ensure it's an integer
        print(predicted_class)
        predicted_label = CLASS_LABELS[predicted_class]
        print(predicted_label)

        # If furcation is detected, proceed with further processing
        if predicted_label == "With Furcation":
            temp_path = os.path.join(UPLOAD_FOLDER, "temp_image.jpg")
            img.save(temp_path)
            
            # Extract tooth using YOLO
            teeth_results = TEETH_EXTRACTOR_MODEL(temp_path)
            cropped_teeth_path = crop_teeth(temp_path, teeth_results)

            if cropped_teeth_path:
                cropped_teeth_img = Image.open(cropped_teeth_path).convert("RGB")
                processed_teeth_img = preprocess_image(cropped_teeth_img, IMG_SIZE)

                # Predict bone loss
                bone_loss_prediction = BONE_LOSS_MODEL.predict(processed_teeth_img)[0]
                bone_loss_image = apply_mask(cropped_teeth_img, bone_loss_prediction)
                bone_loss_image_path = os.path.join(UPLOAD_FOLDER, "bone_loss_applied.jpg")
                bone_loss_image.save(bone_loss_image_path)

                # Predict furcation marker
                furcation_marker_prediction = FURCATION_MARKER_MODEL.predict(processed_teeth_img)[0]
                furcation_marker_image = apply_mask(cropped_teeth_img, furcation_marker_prediction)
                furcation_marker_path = os.path.join(UPLOAD_FOLDER, "furcation_marker_applied.jpg")
                furcation_marker_image.save(furcation_marker_path)

                return {
                    "prediction": predicted_label,
                    "confidence": confidence,
                    "bone_loss_image_url": "/uploads/bone_loss_applied.jpg",
                    "furcation_marker_url": "/uploads/furcation_marker_applied.jpg"
                }

        return {"prediction": predicted_label, "confidence": confidence}

    except Exception as e:
        logging.error(f"Prediction Error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
