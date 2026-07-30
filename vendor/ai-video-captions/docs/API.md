# API Documentation

Base URL: `http://localhost:5000`

## Endpoints

### Health Check

```
GET /api/health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### Process Video

```
POST /api/process
Content-Type: multipart/form-data
```

Fields:
- `file` — Video file (MP4, MOV, or WebM)
- `captionStyle` — Style ID: hormozi, mrbeast, karaoke, minimal, bounce, classic
- `captionPosition` — Integer 5-50 (percentage from bottom)

Response:
```json
{
  "jobId": "uuid",
  "status": "pending"
}
```

Errors:
- `400` — Invalid file type, size, style, or position
- `429` — Too many concurrent jobs

### Job Status

```
GET /api/status/{jobId}
```

Response:
```json
{
  "jobId": "uuid",
  "status": "processing",
  "progress": 50,
  "currentPhase": "burning",
  "language": "en",
  "durationSeconds": 120.5,
  "errorMessage": null
}
```

Status values: `pending`, `processing`, `completed`, `failed`
Phase values: `transcribing`, `burning`, `finalizing`

### Download Result

```
GET /api/download/{jobId}
```

Response: Video file stream (`video/mp4`)

Headers:
- `Content-Disposition: attachment; filename="original_captioned.mp4"`

Errors:
- `404` — Job not found
- `409` — Job not completed yet

### Delete Job

```
DELETE /api/jobs/{jobId}
```

Response:
```json
{
  "deleted": true
}
```

Errors:
- `404` — Job not found
