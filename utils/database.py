import streamlit as st
from utils.auth import get_user_client


def initialize_user_usage(user_id, email):
    """Initialize usage tracking for a new user."""
    client = get_user_client()
    if client:
        client.table("api_usage").insert({
            "user_id": user_id,
            "email": email,
            "queries": 0
        }).execute()


def get_user_usage(user_id, email):
    """Get current API usage for a user."""
    client = get_user_client()
    if not client:
        return 0

    response = client.table("api_usage").select("*").eq("user_id", user_id).execute()
    if response.data:
        return response.data[0]["queries"]
    else:
        # Create usage record if it doesn't exist
        initialize_user_usage(str(user_id), email)
        return 0


def increment_usage(user_id, email):
    """Increment API usage count for a user."""
    client = get_user_client()
    if not client:
        return

    current = get_user_usage(user_id, email)
    client.table("api_usage").update({
        "queries": current + 1
    }).eq("user_id", user_id).execute()


def get_usage_history(user_id):
    """Get usage history for dashboard (you might want to add a usage_history table)."""
    client = get_user_client()
    if not client:
        return []

    # For now, just return current usage
    response = client.table("api_usage").select("*").eq("user_id", user_id).execute()
    return response.data if response.data else []
