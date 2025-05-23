"""
HTTP client for making GET and POST requests and decoding the response using Pydantic.
"""

import pydantic
import httpx
from common import exceptions


# TODO: Introduce common APIError to return and decode non-OK response

APIObject = pydantic.BaseModel

APIClass = type[pydantic.BaseModel]


async def get(
    url: str,
    params: str,
    api_response_class: APIClass | None = None,
) -> APIObject | None:
    """
    Send a HTTP GET request and use Pydantic to parse the response.
    """
    async with httpx.AsyncClient() as httpx_client:
        try:
            response = await httpx_client.get(url, params=params)
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
    api_obj: APIObject,
    api_response_class: APIClass | None = None,
) -> APIObject:
    """
    Send a HTTP POST request and use Pydantic to parse the response.
    """
    async with httpx.AsyncClient() as httpx_client:
        json = api_obj.model_dump()
        try:
            response = await httpx_client.post(url, json=json)
        except httpx.HTTPError as exc:
            raise exceptions.HTTPError(
                method="POST",
                url=url,
                reason="Exception raised",
                data=api_obj,
                exception=str(exc),
            ) from exc
        if response.status_code != 200:
            raise exceptions.HTTPError(
                method="POST",
                url=url,
                reason="Status code not OK",
                data=api_obj,
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
                method="POST",
                url=url,
                reason="Response validation error",
                data=api_obj,
                exception=str(exc),
            ) from exc
        return obj
