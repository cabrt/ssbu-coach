# Smash Coach

AI-powered replay analysis for Super Smash Bros Ultimate. Upload a replay video and get coaching feedback with explanations.

## Features

- **Video Analysis**: Extracts game state (percent, stocks) from replay videos
- **Pattern Detection**: Identifies damage spikes, stock losses, combos, and neutral exchanges
- **AI Coaching**: GPT-powered analysis and personalized improvement tips
- **Timeline View**: Visual timeline of key moments in your match

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with your OpenAI key for AI-powered coaching:
```
OPENAI_API_KEY=your_key_here
```

Run the backend:
```bash
uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## How It Works

1. Upload a replay video (.mp4, .mov, .webm)
2. Backend extracts frames and reads game state using EasyOCR
3. Pattern detection finds key moments (damage spikes, combos, stock losses)
4. AI generates personalized coaching feedback
5. Results displayed with a visual timeline

## Supported Resolutions

- 720p (1280x720) - optimized
- 1080p (1920x1080) - supported

Tournament VODs with standard Smash UI layouts work best.

## Tech Stack

- **Frontend**: React + Vite
- **Backend**: Python FastAPI
- **CV**: OpenCV + EasyOCR
- **AI**: OpenAI GPT-4o-mini

## Roadmap

- [ ] Character detection with YOLO
- [ ] Move recognition for combo analysis  
- [ ] Real-time analysis with capture card
- [ ] Train custom OCR for Smash fonts
