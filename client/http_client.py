"""
HTTP client for making GET and POST requests and decoding the response using Pydantic.
"""

import httpx
import pydantic
from common import exceptions
from common.allocation import Allocation
from common.logging import LOGGER
from common.signature import Signature
from common.signing_key import SigningKey
from common.pool import Pool


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

        def __init__(self, local_pool, peer_pool):
            self._local_pool = local_pool
            self._peer_pool = peer_pool

        async def async_auth_flow(self, request):
            signing_key = SigningKey.from_pool(self._local_pool)
            signature = signing_key.sign([request.url.query, request.content])
            signature.add_to_headers(request.headers)
            response = yield request
            received_signature = Signature.from_headers(response.headers)
            allocation = Allocation.from_enc_str(
                received_signature.signing_key_allocation_enc_str, self._peer_pool
            )
            allocation.mark_allocated()
            signing_key = SigningKey(allocation)
            await response.aread()
            content = response.content
            computed_signature = signing_key.sign([content])
            signature_ok = received_signature.same_as(computed_signature)
            if not signature_ok:
                # TODO: Better exception, that causes a 403 forbidden response
                raise ValueError("Invalid signature")
            # TODO: I noticed that the response to a POST key-share is the string null; that's not
            #       right

    def __init__(self, local_pool: Pool, peer_pool: Pool):
        super().__init__()
        self._httpx_client = httpx.AsyncClient()
        self._auth = self.Auth(local_pool, peer_pool)

    async def get(
        self,
        url: str,
        params: str,
        api_response_class: APIClass | None = None,
        authentication: bool = False,
    ) -> APIObject | None:
        """
        Send a HTTP GET request return the parsed response (if any).
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
        LOGGER.info(f"Call GET {url} {response.status_code}")
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
                LOGGER.error(f"Call {method} {url} {response.status_code}")
                raise exceptions.HTTPError(
                    method=method,
                    url=url,
                    reason="Status code not OK",
                    data=api_request_obj,
                    status_code=response.status_code,
                    response=response.content,
                )
            LOGGER.info(f"Call {method} {url} {response.status_code}")
            if api_response_class is None:
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
