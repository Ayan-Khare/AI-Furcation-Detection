import express from "express";
import cors from "cors";
import multer from "multer";
import axios from "axios";
import fs from "fs";
import path from "path";
import FormData from "form-data";

const app = express();
app.use(cors());
app.use(express.json());

const upload = multer({ dest: "uploads/" });
const FASTAPI_URL = "http://127.0.0.1:8000/predict/";

app.use("/uploads", express.static("uploads"));

app.post("/predict", upload.single("file"), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: "No file uploaded" });
        }

        const imagePath = path.resolve(req.file.path);
        const formData = new FormData();
        formData.append("file", fs.createReadStream(imagePath), req.file.originalname);

        const response = await axios.post(FASTAPI_URL, formData, {
            headers: formData.getHeaders(),
            responseType: "json",
        });

        fs.unlinkSync(imagePath);

        const responseData = response.data;
        
        if (responseData.bone_loss_image_url) {
            responseData.bone_loss_image_url = `http://localhost:5000${responseData.bone_loss_image_url}`;
        }
        
        if (responseData.furcation_marker_url) {
            responseData.furcation_marker_url = `http://localhost:5000${responseData.furcation_marker_url}`;
        }

        res.json(responseData);
    } catch (error) {
        console.error("Prediction Error:", error.response?.data || error.message);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

export default app;
