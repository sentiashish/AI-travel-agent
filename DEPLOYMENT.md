# Deployment guide

The Streamlit interface in `app.py` can be deployed. It needs Python 3.10+
and the packages in `requirements.txt`.

## Required secret

Set `OPENROUTER_API_KEY` in the host's secrets or environment-variable page.
Do not upload or commit `.env`. The app remains usable without a key, but it
will generate an offline fallback plan instead of using the live AI agent.

## Streamlit Community Cloud

1. Push this repository to GitHub.
2. Create an app at Streamlit Community Cloud and select the repository.
3. Set the main file path to `app.py`.
4. In **Advanced settings > Secrets**, add:

   ```toml
   OPENROUTER_API_KEY = "sk-or-v1-your-real-key"
   ```

5. Deploy. Streamlit installs `requirements.txt` automatically.

## Render or Railway

Use these settings:

- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`
- Environment variable: `OPENROUTER_API_KEY`

## Before publishing

- Run the app locally and make one test itinerary.
- Confirm `.env` contains no placeholder key and is not staged in Git.
- Do not commit generated logs or private user queries.
- Treat itineraries, prices, weather, and booking availability as estimates to verify.
