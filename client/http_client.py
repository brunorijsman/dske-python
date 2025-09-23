"""
HTTP client for making GET and POST requests and decoding the response using Pydantic.
"""

import httpx
import pydantic
from common import exceptions
from common.signing_key import SigningKey
from common.pool import Pool


# TODO: Introduce common APIError to return and decode non-OK response


class HttpClient:
    """
    An asynchronous HTTP client that:
      - Uses httpx to make requests.
      - Uses Pydantic to encode/decode request/response data.
      - Takes care of request authentication using an authentication key from a pool.
    """

    APIObject = pydantic.BaseModel

    APIClass = type[pydantic.BaseModel]

    class Auth(httpx.Auth):
        """
        An httpx Auth class that uses an authentication key from a pool to sign requests.
        """

        def __init__(self, signing_key_pool: Pool | None = None):
            self._signing_key_pool = signing_key_pool

        def auth_flow(self, request):
            signing_key = SigningKey.from_pool(self._signing_key_pool)
            signature = signing_key.sign([request.url.query, request.content])
            signature.add_to_headers(request.headers)
            yield request

    def __init__(self, signing_key_pool: Pool):
        super().__init__()
        self._httpx_client = httpx.AsyncClient()
        self._auth = self.Auth(signing_key_pool)

    async def get(
        self,
        url: str,
        params: str,
        api_response_class: APIClass | None = None,
        authentication: bool = False,
    ) -> APIObject | None:
        """
        Send a HTTP GET request return the parsed response (if any).

        If `signing_key_pool` is None, no authentication is done. If it is not None, use it
        to allocate a key the request authentication signature.
        """
        if authentication:
            auth = self._auth
        else:
            auth = None
        try:
            response = await self._httpx_client.get(url, params=params, auth=auth)
        except httpx.HTTPError as exc:
            raise exceptions.HTTPError(
                method="GET",
                url=url,
                reason="Exception raised",
                params=params,
                exception=str(exc),
            ) from exc
        if response.status_code != 200:
            raise exceptions.HTTPError(
                method="GET",
                url=url,
                reason="Status code not OK",
                params=params,
                status_code=response.status_code,
                response=response.content,
            )
        if api_response_class is None:
            # TODO: Check that the response is empty, since none is expected
            return None
        try:
            obj = api_response_class.model_validate(response.json())
        except pydantic.ValidationError as exc:
            raise exceptions.HTTPError(
                method="GET",
                url=url,
                reason="Response validation error",
                params=params,
                exception=str(exc),
            ) from exc
        return obj

    async def post(
        self,
        url: str,
        api_request_obj: APIObject,
        api_response_class: APIClass | None = None,
        authentication: bool = False,
    ) -> APIObject:
        """
        Send a HTTP POST request and return the parsed response (if any).
        """
        return await self._put_or_post(
            "POST", url, api_request_obj, api_response_class, authentication
        )

    async def put(
        self,
        url: str,
        api_request_obj: APIObject,
        api_response_class: APIClass | None = None,
        authentication: bool = False,
    ) -> APIObject:
        """
        Send a HTTP PUT request and return the parsed response (if any).
        """
        return await self._put_or_post(
            "PUT", url, api_request_obj, api_response_class, authentication
        )

    async def _put_or_post(
        self,
        method: str,
        url: str,
        api_request_obj: APIObject,
        api_response_class: APIClass | None = None,
        authentication: bool = False,
    ) -> APIObject:
        """
        Send a HTTP PUT or POST request. Use Pydantic to encode the request data and to decode the
        response data.
        """
        async with httpx.AsyncClient() as httpx_client:
            json = api_request_obj.model_dump()
            if authentication:
                auth = self._auth
            else:
                auth = None
            try:
                response = await httpx_client.request(method, url, json=json, auth=auth)
            except httpx.HTTPError as exc:
                raise exceptions.HTTPError(
                    method=method,
                    url=url,
                    reason="Exception raised",
                    data=api_request_obj,
                    exception=str(exc),
                ) from exc
            if response.status_code != 200:
                raise exceptions.HTTPError(
                    method=method,
                    url=url,
                    reason="Status code not OK",
                    data=api_request_obj,
                    status_code=response.status_code,
                    response=response.content,
                )
            if api_response_class is None:
                # TODO: Check that the response is empty, since none is expected
                return None
            try:
                obj = api_response_class.model_validate(response.json())
            except pydantic.ValidationError as exc:
                raise exceptions.HTTPError(
                    method=method,
                    url=url,
                    reason="Response validation error",
                    data=api_request_obj,
                    exception=str(exc),
                ) from exc
            return obj
