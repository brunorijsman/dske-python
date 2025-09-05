"""
HTTP client for making GET and POST requests and decoding the response using Pydantic.
"""

import pydantic
import httpx
from common import authentication
from common import exceptions
from common.pool import Pool


# TODO: Introduce common APIError to return and decode non-OK response

APIObject = pydantic.BaseModel

APIClass = type[pydantic.BaseModel]


def determine_headers(authentication_key_pool: Pool | None) -> dict:
    """
    If `authentication_key_pool` is not None, use it to allocate a key and compute an authentication
    signature. Add the signature to the `headers` dictionary.
    """
    headers = {}
    if authentication_key_pool is not None:
        signature = authentication.compute_signature(authentication_key_pool)
        headers["DSKE-Authentication"] = signature
    return headers


async def get(
    url: str,
    params: str,
    api_response_class: APIClass | None = None,
    authentication_key_pool: Pool | None = None,
) -> APIObject | None:
    """
    Send a HTTP GET request return the parsed response (if any).

    If `authentication_key_pool` is None, no authentication is done. If it is not None, use it to
    allocate a key the request authentication signature.
    """
    headers = determine_headers(authentication_key_pool)
    async with httpx.AsyncClient() as httpx_client:
        try:
            response = await httpx_client.get(url, params=params, headers=headers)
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
    url: str,
    api_request_obj: APIObject,
    api_response_class: APIClass | None = None,
    authentication_key_pool: Pool | None = None,
) -> APIObject:
    """
    Send a HTTP POST request and return the parsed response (if any).
    """
    return await put_or_post(
        "POST", url, api_request_obj, api_response_class, authentication_key_pool
    )


async def put(
    url: str,
    api_request_obj: APIObject,
    api_response_class: APIClass | None = None,
    authentication_key_pool: Pool | None = None,
) -> APIObject:
    """
    Send a HTTP PUT request and return the parsed response (if any).
    """
    return await put_or_post(
        "PUT", url, api_request_obj, api_response_class, authentication_key_pool
    )


async def put_or_post(
    method: str,
    url: str,
    api_request_obj: APIObject,
    api_response_class: APIClass | None = None,
    authentication_key_pool: Pool | None = None,
) -> APIObject:
    """
    Send a HTTP PUT or POST request. Use Pydantic to encode the request data and to decode the
    response data.
    """
    headers = determine_headers(authentication_key_pool)
    async with httpx.AsyncClient() as httpx_client:
        json = api_request_obj.model_dump()
        try:
            response = await httpx_client.request(
                method, url, json=json, headers=headers
            )
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
