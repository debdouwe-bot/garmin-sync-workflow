# garmin-sync-workflow

A Mistral Workflows worker that fetches Garmin Connect data through the Garmin Connect Personal API and returns it as the execution result of the `garmin-sync` workflow.

## Workflow

`garmin-sync` takes one input:

```json
{"days_back": 2}
```

It delegates to the `fetch-garmin-data` activity, which:

1. Reads the Garmin Personal API key from the environment variable `GARMIN_PERSONAL_API_KEY` (bound from a Mistral workspace secret).
2. Exchanges the key for a bearer token with the `garmin-connect-personal-api-python` client.
3. Fetches activities, daily summaries, sleep summaries and daily heart rate for the last `days_back` days.

The result is a JSON dict stored as the execution result, retrievable from the Mistral console or via the Workflows API.

## Deployment

Managed deployment of this repository. Requirements:

- Dockerfile at the repository root; the container command starts the worker.
- Workspace secret `garmin_personal_api_key` bound to the environment variable `GARMIN_PERSONAL_API_KEY`.
- A schedule (e.g. daily) executing `garmin-sync` with `{"days_back": 2}`.
