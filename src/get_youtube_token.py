"""ONE-TIME helper (run locally). Generates the YouTube refresh token you paste
into GitHub Secrets. Needs client_secret.json from Google Cloud (OAuth Desktop)."""
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

if __name__ == "__main__":
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)
    print("\n==== ADD THESE TO GITHUB SECRETS / .env ====")
    print("YOUTUBE_CLIENT_ID    =", creds.client_id)
    print("YOUTUBE_CLIENT_SECRET=", creds.client_secret)
    print("YOUTUBE_REFRESH_TOKEN=", creds.refresh_token)
