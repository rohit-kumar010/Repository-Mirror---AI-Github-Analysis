# Quick Start Guide

## Prerequisites
- Python 3.8+
- Node.js 16+
- Internet connection (for GitHub API)

## Setup (5 minutes)

### 1. Backend Setup
```powershell
cd backend
pip install -r requirements.txt
python app.py
```
Keep this terminal open - backend runs on port 5000

### 2. Frontend Setup (New Terminal)
```powershell
cd frontend
npm install
npm run dev
```
Frontend runs on port 3000

### 3. Open Browser
Navigate to: http://localhost:3000

### 4. Test It!
Paste any public GitHub repo URL and click "Analyze"

Example URLs to try:
- https://github.com/facebook/react
- https://github.com/microsoft/vscode
- https://github.com/vercel/next.js

## Troubleshooting

**Port already in use?**
- Backend: Edit `app.py` and change port 5000 to 5001
- Frontend: Edit `vite.config.js` and change port 3000 to 3001

**GitHub rate limit?**
- Get a GitHub token: https://github.com/settings/tokens
- Set environment variable: `$env:GITHUB_TOKEN="your_token_here"`
- Restart backend

**Module not found?**
- Backend: Make sure virtual environment is activated
- Frontend: Delete `node_modules` and run `npm install` again

## Project Structure
```
Hackathon/
├── backend/
│   ├── app.py              # Flask server + analysis logic
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main React component
│   │   ├── main.jsx        # Entry point
│   │   └── index.css       # Styles
│   ├── package.json        # Node dependencies
│   └── vite.config.js      # Vite configuration
└── README.md               # Full documentation
```

## Recording Demo

1. Start both backend and frontend
2. Open browser to localhost:3000
3. Use screen recording tool (OBS, ShareX, or Windows Game Bar: Win+G)
4. Show:
   - Entering a repo URL
   - Clicking analyze
   - Scrolling through results
   - Highlighting score, summary, and roadmap
5. Keep it under 3 minutes!

## Tips for Winning

✅ **Demo real repositories** - Show variety (good and bad repos)
✅ **Highlight the roadmap** - This is the unique value
✅ **Show the metrics** - Demonstrate data-driven analysis
✅ **Mention the tech stack** - Flask, React, GitHub API, Tailwind
✅ **Explain the scoring** - 6 dimensions, 100-point scale
✅ **Polish matters** - The UI looks professional

Good luck! 🚀
