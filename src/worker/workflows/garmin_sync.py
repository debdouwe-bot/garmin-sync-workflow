"""Fetch Garmin Connect data through the Personal API and return it as the workflow result.

Intended for a scheduled managed deployment: the Garmin Personal API key is bound
from a workspace secret to the environment variable ``GARMIN_PERSONAL_API_KEY``.
"""

import os
from datetime import date, timedelta

from pydantic import BaseModel, Field

import mistralai.workflows as workflows


class GarminSyncInput(BaseModel):
    """Input for one sync run."""

    days_back: int = Field(
        default=2,
        ge=1,
        le=30,
        description="How many days back to fetch, counting from today (UTC).",
    )


@workflows.activity(
    name="fetch-garmin-data",
    start_to_close_timeout=timedelta(minutes=10),
    retry_policy_max_attempts=3,
)
async def fetch_garmin_data(days_back: int) -> dict:
    """Fetch runs/activities and daily summaries for the last `days_back` days."""
    from garmin_personal_api import GarminPersonalApiClient, PersonalApiAuthenticator

    api_key = os.environ.get("GARMIN_PERSONAL_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Bind a Garmin Personal API key to GARMIN_PERSONAL_API_KEY "
            "(workspace secret bound to the deployment)."
        )

    start = date.today() - timedelta(days=days_back)
    end = date.today()

    with PersonalApiAuthenticator() as authenticator:
        token = authenticator.obtain_token(api_key)

    with GarminPersonalApiClient(token.access_token) as client:
        activities = client.search_activities(
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            limit=50,
        )
        daily_summaries = client.get_daily_summaries(start.isoformat(), end.isoformat())
        sleep_summaries = client.get_daily_sleep_summaries(
            start.isoformat(), end.isoformat()
        )
        daily_heart_rate = {
            day.isoformat(): client.get_daily_heart_rate(day.isoformat())
            for day in _daterange(start, end)
        }

    return {
        "fetched_at": date.today().isoformat(),
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "activities": activities,
        "daily_summaries": daily_summaries,
        "sleep_summaries": sleep_summaries,
        "daily_heart_rate": daily_heart_rate,
    }


def _daterange(start: date, end: date):
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


@workflows.workflow.define(
    name="garmin-sync",
    workflow_display_name="Garmin Sync",
    workflow_description="Fetch Garmin Connect data via the Personal API.",
)
class GarminSyncWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: GarminSyncInput) -> dict:
        return await fetch_garmin_data(input.days_back)
