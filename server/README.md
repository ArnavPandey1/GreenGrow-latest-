# GreenGrow Server

This folder contains the server-side components of the GreenGrow application.

## Structure

- `app.py` - Flask API server for crop recommendation
- `Crop Recommendation Using ML.ipynb` - Jupyter notebook for ML model development
- `Crop_recommendation.csv` - Dataset for training the ML model
- `model.pkl` - Trained ML model
- `minmaxscaler.pkl` - MinMax scaler for data preprocessing
- `standscaler.pkl` - Standard scaler for data preprocessing

**Note:** This is a pure API server - no static files are served. The React frontend handles all UI assets.

## Setup

1. Install MongoDB:
   - **Windows**: Download from [MongoDB Community Server](https://www.mongodb.com/try/download/community)
   - **macOS**: `brew install mongodb-community`
   - **Linux**: Follow [MongoDB installation guide](https://docs.mongodb.com/manual/installation/)

2. Start MongoDB service:
   ```bash
   # Windows (if installed as service)
   net start MongoDB
   
   # macOS/Linux
   mongod
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (create a `.env` file):
   ```bash
   SECRET_KEY=your-super-secret-key-change-in-production
   JWT_SECRET_KEY=jwt-super-secret-key-change-in-production
   MONGO_URI=mongodb://localhost:27017/
   MONGO_DB_NAME=greengrow
   ```

5. Run the Flask application:
   ```bash
   python app.py
   ```

The server will start on `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/profile` - Get user profile (protected)
- `POST /api/auth/logout` - User logout (protected)

### Crop Recommendation
- `POST /api/predict` - Crop recommendation prediction (protected)

