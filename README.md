# Remote ASR

A minimal FastAPI endpoint that transcribes audio with Pydantic AI and
`gemini-3.5-flash`.

## Run

```powershell
Copy-Item .env.example .env
# Put your Gemini API key in .env, then:
uv sync
uv run uvicorn app:app --env-file .env
```

The fixed API key is:

```text
7DJBK_iHnZpoNzdtHmuodHaF0bUhLddPuxX01qrbEdE
```

Send an audio file (maximum 10 MiB):

```powershell
curl.exe -X POST http://127.0.0.1:8000/transcribe `
  -H "X-API-Key: 7DJBK_iHnZpoNzdtHmuodHaF0bUhLddPuxX01qrbEdE" `
  -F "audio=@recording.mp3"
```

Response:

```json
{"transcription":"The transcribed speech appears here."}
```
