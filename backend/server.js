import app from "./index.js";
import dotenv from "dotenv";

dotenv.config();

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
    console.log(`Backend running on http://localhost:${PORT}`);
});