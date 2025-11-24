## GreenGrow – Smart Agriculture Platform

GreenGrow is a full‑stack web application that helps farmers make better decisions with **AI‑powered crop recommendations** and **soil restoration guidance**, wrapped in a secure, modern web experience.
The project is split into a **React (Vite) frontend** and a **Flask API backend** with MongoDB and ML models.

---

## Project Structure

```text
GreenGrow/
├─ client/              # React frontend (Vite + Tailwind)
│  ├─ src/              # Pages, components, hooks, contexts
│  ├─ public/           # Static assets
│  └─ package.json      # Frontend dependencies & scripts
├─ server/              # Flask API + ML models
│  ├─ app.py            # Main API entrypoint
│  ├─ *.pkl             # Trained model & scalers
│  ├─ *.csv             # Datasets / reference data
│  └─ requirements.txt  # Backend dependencies
└─ README.md            # Root project documentation
```

For more detail, see `client/README.md` and `server/README.md`.

---

## Features

- **User authentication**
  - JWT‑based login and registration
  - Protected routes in the frontend using auth context
  - Profile fetching and secure logout
- **AI crop recommendation**
  - Uses trained ML model (`model.pkl`) with preprocessing scalers
  - Inputs: N, P, K, temperature, humidity, pH, rainfall
  - Returns recommended crop plus friendly tip text
- **Soil restoration guidance**
  - `/api/soil-restoration` endpoint powered by CSV data
  - Suggests rotation and restoration options based on last harvested crop
- **User profiles with avatars**
  - Upload, update, and remove profile pictures
  - Avatars served from `/uploads/avatars`
- **Modern frontend experience**
  - React + Vite + Tailwind CSS
  - Routing and protected views (e.g. profile, crop tools)

---

## Prerequisites

- **Node.js**: v18+ (for the frontend)
- **Python**: 3.10+ (for the backend)
- **MongoDB**: running locally or accessible via connection string

---

## Backend (Flask API) – Setup & Run

From the project root:

```bash
cd server

# (Optional but recommended) create & activate a virtual env
python -m venv myvenv
myvenv\Scripts\activate      # Windows PowerShell / CMD

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in `server/`:

```bash
SECRET_KEY=your-super-secret-key-change-in-production
JWT_SECRET_KEY=jwt-super-secret-key-change-in-production
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=greengrow
```

Start MongoDB (local or cloud), then run the server:

```bash
python app.py
```

The API will be available at `http://localhost:5000`.

---

## Frontend (React) – Setup & Run

In a separate terminal, from the project root:

```bash
cd client
npm install
npm run dev
```

By default, Vite runs on `http://localhost:5173` (or the next free port).  
The frontend is configured to talk to the Flask backend running on `http://localhost:5000` (ensure CORS and URLs match your setup).

---

## Key API Endpoints (Summary)

- **Auth**
  - `POST /api/auth/register` – create new user
  - `POST /api/auth/login` – obtain JWT access token
  - `GET /api/auth/profile` – fetch current user (JWT required)
  - `POST /api/auth/logout` – logical logout (JWT required)
- **Crop recommendation**
  - `POST /api/predict` – get recommended crop (JWT required)
- **Soil restoration**
  - `POST /api/soil-restoration` – recommendations based on last crop
- **Profile & avatar**
  - `GET /api/profile` – user profile (with avatar URL if present)
  - `POST /api/profile/avatar` – upload/update avatar
  - `DELETE /api/profile/avatar` – remove avatar
  - `GET /uploads/avatars/<filename>` – serve avatar image

See `server/app.py` for full request/response details and validations.

---

## Development Notes

- Environment‑specific secrets (`SECRET_KEY`, `JWT_SECRET_KEY`, `MONGO_URI`) are **not** committed; use a local `.env` file.
- Large or generated assets (`node_modules`, virtualenvs, `server/uploads/`) are ignored via `.gitignore`.
- When changing model files (`model.pkl`, scalers, CSVs), restart the Flask server so they are reloaded.

---

## License / Usage

This project is currently for educational / internal use.  
Add a formal license file if you plan to open‑source or distribute it. 