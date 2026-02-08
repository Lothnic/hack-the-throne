# ForgetMeNot

An AI-powered memory companion for dementia patients. ForgetMeNot uses real-time face recognition, voice transcription, and large language models to help patients remember the people who visit them.

## The Problem

Over 55 million people worldwide live with dementia. One of the most distressing symptoms is the inability to recognize family members and caregivers. Current solutions like photo albums and whiteboards are passive and require constant manual updates.

## Our Solution

ForgetMeNot is an always-on AI system that:

- **Recognizes faces** in real-time using MediaPipe Vision
- **Listens to conversations** and transcribes speech with Whisper
- **Extracts relationships** automatically ("I'm your son" → stores relationship)
- **Remembers across visits** with persistent storage
- **Provides context** to patients and caregivers through a dementia-friendly interface

## Features

### For Patients
- Real-time face recognition with name and relationship display
- Large, high-contrast UI designed for cognitive accessibility
- Passive operation—no interaction required

### For Caregivers
- Dashboard showing all known visitors
- Conversation history and activity feed
- Relationship tracking across sessions

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, React 19, TailwindCSS |
| Backend | FastAPI, WebRTC, Python 3.12 |
| Face Detection | MediaPipe Vision (browser-based) |
| Voice Transcription | Whisper Large V3 via Groq |
| Relationship Extraction | LLaMA 3 70B via Groq |
| Speaker Identification | PyAnnote Audio embeddings |
| Database | Convex (real-time sync) |

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Camera    │────▶│  MediaPipe  │────▶│   Face DB   │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐
│ Microphone  │────▶│   Whisper   │────▶│  LLM (Groq) │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │   Convex    │
                                        │  Database   │
                                        └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │  Dashboard  │
                                        └─────────────┘
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Convex account (for database)
- Groq API key (for LLM and transcription)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Lothnic/hack-the-throne.git
   cd hack-the-throne
   ```

2. Set up the Python environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Add your GROQ_API_KEY and CONVEX credentials
   ```

5. Start all services:
   ```bash
   ./start_all.sh
   ```

6. Open http://localhost:3000 in your browser.

## Usage

1. **Allow camera and microphone access** when prompted
2. **Face detection** will automatically identify people in frame
3. **Record conversations** using the record button or spacebar
4. The system will **automatically extract names and relationships**
5. Visit **/dashboard** to see all known people and activity

## Project Structure

```
hack-the-throne/
├── backend/           # FastAPI server, WebRTC, audio processing
│   ├── app/
│   │   ├── audio/     # Voice activity detection, transcription
│   │   ├── core/      # Shared models
│   │   └── services/  # Convex client, LLM service
├── frontend/          # Next.js application
│   ├── app/           # Pages (home, dashboard)
│   ├── components/    # UI components
│   ├── convex/        # Database schema and queries
│   └── hooks/         # Custom React hooks
├── inference/         # Inference service for LLM processing
└── start_all.sh       # Script to run all services
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/offer` | POST | WebRTC signaling |
| `/transcribe` | POST | Audio transcription |
| `/stream/inference` | GET | SSE stream for real-time updates |
| `/stream/conversation` | GET | SSE stream for conversation events |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | API key for Groq (LLM and Whisper) |
| `CONVEX_URL` | Convex deployment URL |
| `CONVEX_ADMIN_KEY` | Convex admin key for server-side mutations |

## Contributing

Contributions are welcome. Please open an issue first to discuss proposed changes.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- [MediaPipe](https://mediapipe.dev/) for face detection
- [Groq](https://groq.com/) for fast LLM inference
- [Convex](https://convex.dev/) for real-time database
- [PyAnnote](https://github.com/pyannote/pyannote-audio) for speaker embeddings
