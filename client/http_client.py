"""
HTTP client for making GET and POST requests and decoding the response using Pydantic.
"""

import sys
import httpx
import pydantic
from common import exceptions
from common.allocation import Allocation
from common.signature import Signature
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

        def __init__(self, local_pool, peer_pool):
            self._local_pool = local_pool
            self._peer_pool = peer_pool

        async def async_auth_flow(self, request):
            print(f"auth_flow: {request=}", file=sys.stderr)
            signing_key = SigningKey.from_pool(self._local_pool)
            signature = signing_key.sign([request.url.query, request.content])
            signature.add_to_headers(request.headers)
            response = yield request
            print(f"auth_flow: {response=}", file=sys.stderr)
            received_signature = Signature.from_headers(response.headers)
            print(f"auth_flow: {received_signature=}", file=sys.stderr)
            allocation = Allocation.from_enc_str(
                received_signature.signing_key_allocation_enc_str, self._peer_pool
            )
            allocation.mark_allocated()
            print(f"auth_flow: {allocation=}", file=sys.stderr)
            signing_key = SigningKey(allocation)
            print(f"auth_flow: {signing_key=}", file=sys.stderr)
            await response.aread()
            content = response.content
            print(f"auth_flow: {content=}", file=sys.stderr)
            computed_signature = signing_key.sign([content])
            print(f"auth_flow: {computed_signature=}", file=sys.stderr)
            signature_ok = received_signature.same_as(computed_signature)
            print(f"auth_flow: {signature_ok=}", file=sys.stderr)
            if not signature_ok:
                # TODO: Better exception, that causes a 403 forbidden response
                raise ValueError("Invalid signature")

            # TODO: $$$
            # TODO: where do we check the response signature?
            # TODO: do we need to store the peer pool for checking it?
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
