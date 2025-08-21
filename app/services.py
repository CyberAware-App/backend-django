import mux_python
from mux_python.rest import ApiException
from django.conf import settings

def create_mux_asset(video_url):
    configuration = mux_python.Configuration()
    configuration.username = settings.MUX_TOKEN_ID
    configuration.password = settings.MUX_TOKEN_SECRET
    api_client = mux_python.ApiClient(configuration)
    assets_api = mux_python.AssetsApi(api_client)

    try:
        input_settings = mux_python.InputSettings(url=video_url)
        asset = assets_api.create_asset(mux_python.CreateAssetRequest(
            input=[input_settings],
            playback_policy=[mux_python.PlaybackPolicy.PUBLIC],
        ))
        return asset
    except ApiException as e:
        print(f"Exception creating Mux asset: {e}")
        return None
