""" python

   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file provides a utility function for my_egeria.


"""
import time
from textual.widget import Widget
from .config import EgeriaConfig, get_global_config
from pyegeria import EgeriaTech


class DemoService(Widget):
    def __init__(self):
        super().__init__()
        self.config = get_global_config()
        self._last_auth_ts: float = 0.0
        self.client = None


    def _access_egeria(self) -> bool:
        # put in a timer and every 15 minutes (900 seconds) refresh the token.

        try:
            # create egeria client
            self._client = EgeriaTech(
                view_server=self.config.view_server,
                platform_url=self.config.platform_url,
                user_id=self.config.user,
                user_pwd=self.config.password,
                )
            # generate egeria bearer token
            if self._token_expired():
                self._authenticate()
            #return True to signal client successfully connected to egeria
            if not self._client:
                return False
            return True
        except Exception:
            #return False to signal client failed to connect to egeria
            return False

    def _token_expired(self) -> bool:
        """check to verify if bearer token is still valid, we refresh every 15 minutes,
           at time of writing the Egeria default is 30 minutes, however, we use15 minuutes
           to be completely safe """
        if self._last_auth_ts <= 0:
            return True
        return (time.time() - self._last_auth_ts) >= self.config.token_ttl_seconds

    def close_egeria_connection(self):
        if self._client:
            self._client.close_session()

    def _authenticate(self) -> None:
        if self._client and hasattr(self._client, "create_egeria_bearer_token"):
            self._client.create_egeria_bearer_token(self.config.user, self.config.password)
            self._last_auth_ts = time.time()
        else:
            self._client = None

    def refresh_token(self) -> None:
        self._authenticate()

    def _find_collections(self) -> dict:
        if self._client and not self._token_expired():
            return self._client.get_collection_list()
        elif self._client:
            self._token_expired()
            return self._client.get_collection_list()
        else:
            self._access_egeria()
            return self._client.get_collection_list()

