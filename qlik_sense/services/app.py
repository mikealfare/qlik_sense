"""
This module provides the mechanics for interacting with Qlik Sense apps. It uses a one-to-one model
to wrap the QRS endpoints and uses marshmallow to parse the results into Qlik Sense App objects where appropriate.
"""
from typing import TYPE_CHECKING, List, Optional, Iterable
from dataclasses import asdict

import uuid

from qlik_sense.models.app import AppCondensedSchema, AppSchema
from qlik_sense.services import util

if TYPE_CHECKING:
    from qlik_sense.clients.base import Client
    from qlik_sense.models.app import AppCondensed, App
    from qlik_sense.models.stream import StreamCondensed
    import requests


class AppService:
    """
    AppService wraps each one of the app-based QlikSense endpoints in a method. This buffers the application
    from API updates.

    Args:
        client: a Client class that provides an interface over the Qlik Sense APIs


    Supported Methods:

        - qrs/app: GET
        - qrs/app/count: GET
        - qrs/app/full: GET
        - qrs/app/{app.id}: GET, PUT, DELETE
        - qrs/app/{app.id}/copy: POST
        - qrs/app/{app.id}/export/{token}: POST
        - qrs/app/{app.id}/reload: POST
        - qrs/app/{app.id}/publish: PUT
        - qrs/app/{app.id}/replace: PUT
        - qrs/app/{app.id}/unpublish: POST

    Unsupported Methods:

        - qrs/app/import: POST
        - qrs/app/import/replace: POST
        - qrs/app/importfolder: GET
        - qrs/app/previewcreateprivilege: POST
        - qrs/app/previewprivileges: POST
        - qrs/app/table: POST
        - qrs/app/upload: POST
        - qrs/app/upload/replace: POST
        - qrs/app/{app.id}/export/{token}: DELETE
        - qrs/app/{app.id}/export: GET
        - qrs/app/{app.id}/hubinfo: GET
        - qrs/app/{app.id}/migrate: PUT
        - qrs/app/{app.id}/migrationcompleted: POST
        - qrs/app/{app.id}/privileges: GET
        - qrs/app/{app.id}/replace/target: PUT
        - qrs/app/{app.id}/state: GET

        - qrs/app/content: GET
        - qrs/app/content/count: GET
        - qrs/app/content/full: GET
        - qrs/app/content/table: POST
        - qrs/app/content/{app.id}: GET
        - qrs/app/content/{app.id}/fileextensionwhitelist: GET

        - qrs/app/datasegment: GET
        - qrs/app/datasegment/count: GET
        - qrs/app/datasegment/full: GET
        - qrs/app/datasegment/previewprivileges: POST
        - qrs/app/datasegment/table: POST
        - qrs/app/datasegment/{app.id}: GET

        - qrs/app/hublist: GET
        - qrs/app/hublist/full: GET

        - qrs/app/internal: GET
        - qrs/app/internal/count: GET
        - qrs/app/internal/full: GET
        - qrs/app/internal/previewprivileges: POST
        - qrs/app/internal/table: POST
        - qrs/app/internal/{app.id}: GET

        - qrs/app/object: GET
        - qrs/app/object/count: GET
        - qrs/app/object/full: GET
        - qrs/app/object/previewprivileges: POST
        - qrs/app/object/table: POST
        - qrs/app/object/{app.id}: GET, PUT, DELETE
        - qrs/app/object/{app.id}/approve: POST
        - qrs/app/object/{app.id}/publish: PUT
        - qrs/app/object/{app.id}/unapprove: POST
        - qrs/app/object/{app.id}/unpublish: PUT
    """
    requests = list()

    def __init__(self, client: 'Client'):
        self.client = client
        self.url = '/qrs/app'

    def _call(self, request: 'util.QSAPIRequest') -> 'requests.Response':
        return self.client.call(**asdict(request))

    def query(self, filter_by: str = None, order_by: str = None, privileges: 'Optional[List[str]]' = None,
              full_attribution: bool = False) -> 'Optional[List[AppCondensed]]':
        """
        This method queries Qlik Sense apps based on the provided criteria and provides either partial or
        full attribution of the apps based on the setting of full_attribution

        Args:
            filter_by: a filter string in jquery format
            order_by: an order by string
            privileges:
            full_attribution: allows the response to contain the full user attribution,
            defaults to False (limited attribution)

        Returns: a list of Qlik Sense Apps that meet the query_string criteria (or None)
        """
        if full_attribution:
            schema = AppSchema()
            url = f'{self.url}/full'
        else:
            schema = AppCondensedSchema()
            url = f'{self.url}'
        params = {
            'filter': filter_by,
            'orderby': order_by,
            'privileges': privileges
        }
        request = util.QSAPIRequest(method='GET', url=url, params=params)
        response = self._call(request)
        if 200 <= response.status_code < 300:
            return schema.loads(response.json())
        return None

    def query_count(self, filter_by: str = None) -> 'Optional[int]':
        """
        This method queries Qlik Sense apps based on the provided criteria and returns the count

        Args:
            filter_by: a filter string in jquery format

        Returns: the number of Qlik Sense Apps that meet the query_string criteria (or None)
        """
        params = {'filter': filter_by}
        request = util.QSAPIRequest(method='GET', url=f'{self.url}/count', params=params)
        response = self._call(request)
        if 200 <= response.status_code < 300:
            return int(response.text())
        return None

    def get_by_name_and_stream(self, app_name: str, stream_name: str) -> 'Optional[List[AppCondensed]]':
        """
        This method is such a common use case of the query() method that it gets its own method

        Args:
            app_name: name of the app
            stream_name: name of the stream

        Returns: the Qlik Sense app(s) that fit the criteria
        """
        filter_by = f"name eq '{app_name}' and stream.name eq '{stream_name}'"
        return self.query(filter_by=filter_by)

    def get(self, id: str, privileges: 'Optional[List[str]]' = None) -> 'Optional[App]':
        """
        This method returns a Qlik Sense app by its id

        Args:
            id: id of the app on the server in uuid format
            privileges:

        Returns: a Qlik Sense app
        """
        schema = AppSchema()
        request = util.QSAPIRequest(
            method='GET',
            url=f'{self.url}/{id}',
            params={'privileges': privileges}
        )
        response = self._call(request)
        if 200 <= response.status_code < 300:
            return schema.loads(response.json())
        return None

    def update(self, app: 'App', privileges: 'Optional[List[str]]' = None) -> 'Optional[App]':
        """
        This method updates attributes of the provided app on the server

        Args:
            app: app to update
            privileges:

        Returns: a Qlik Sense app object for the updated app
        """
        schema = AppSchema()
        request = util.QSAPIRequest(
            method='PUT',
            url=f'{self.url}/{app.id}',
            params={'privileges': privileges},
            data=asdict(app)
        )
        response = self._call(request)
        if 200 <= response.status_code < 300:
            return schema.loads(response.json())
        return None

    def delete(self, app: 'AppCondensed'):
        """
        This method deletes the provided app from the server

        Args:
            app: app to delete
        """
        request = util.QSAPIRequest(
            method='DELETE',
            url=f'{self.url}/{app.id}'
        )
        self._call(request)

    def reload(self, app: 'AppCondensed'):
        """
        This method reloads the provided app

        Args:
            app: app to reload
        """
        request = util.QSAPIRequest(
            method='POST',
            url=f'{self.url}/{app.id}/reload'
        )
        self._call(request)

    def copy(self, app: 'AppCondensed', name: str = None, include_custom_properties: bool = False) -> 'Optional[App]':
        """
        This method copies the provided app

        Args:
            app: app to copy
            name: name for the new app
            include_custom_properties: flag to include custom properties on the new app

        Returns: a Qlik Sense App object for the newly copied app
        """
        schema = AppSchema()
        params = {
            'name': name,
            'includecustomproperties': include_custom_properties
        }
        request = util.QSAPIRequest(
            method='POST',
            url=f'{self.url}/{app.id}/copy',
            params=params
        )
        response = self._call(request)
        if 200 <= response.status_code < 300:
            return schema.loads(response.json())
        return None

    def prepare_export(self, app: 'AppCondensed', keep_data: bool = False) -> 'Optional[str]':
        """
        This method returns a download path for the provided app. It can be passed into download_file() to obtain
        the app itself

        Args:
            app: app to export
            keep_data: indicates if the data should be exported with the app

        Returns: the download path extension for the app (i.e. localhost/qrs/app/{returns this piece})

        TODO: create export object/schema and return that
        """
        token = uuid.uuid4()
        request = util.QSAPIRequest(
            method='POST',
            url=f'{self.url}/{app.id}/export/{token}',
            params={'skipdata': not keep_data}
        )
        response = self._call(request)
        if 200 <= response.status_code < 300:
            return response.json()['downloadPath']
        return None

    def unpublish(self, app: 'AppCondensed') -> 'Optional[App]':
        """
        Unpublishes the provided app

        Args:
            app: app to unpublish

        Returns: a Qlik Sense App object for the un-published app
        """
        schema = AppSchema()
        request = util.QSAPIRequest(
            method='POST',
            url=f'{self.url}/{app.id}/unpublish'
        )
        response = self._call(request)
        if 200 <= response.status_code < 300:
            return schema.loads(response.json())
        return None

    def delete_export(self, app: 'AppCondensed', token: 'uuid.UUID'):
        """
        This method cancels the download path for the provided app.

        Args:
            app: app originally getting exported
            token: download token

        TODO: accept prepare_export() output instead of app/token
        """
        request = util.QSAPIRequest(
            method='DELETE',
            url=f'{self.url}/{app.id}/export/{token}'
        )
        self._call(request)

    def publish(self, app: 'AppCondensed', stream: 'StreamCondensed', name: str = None) -> 'Optional[App]':
        """
        This method will publish the provided app to the provided stream

        Args:
            app: app to publish
            stream: stream to which to publish the app
            name: name of the published app

        Returns: a Qlik Sense App object for the published app
        """
        schema = AppSchema()
        params = {
            'stream': stream.id,
            'name': name if name else app.name
        }
        request = util.QSAPIRequest(
            method='PUT',
            url=f'{self.url}/{app.id}/publish',
            params=params
        )
        response = self._call(request)
        if 200 <= response.status_code < 300:
            return schema.loads(response.json())
        return None

    def replace(self, app: 'AppCondensed', app_to_replace: 'AppCondensed') -> 'Optional[App]':
        """
        This method replaces the target app with the provided app

        Args:
            app: app to copy
            app_to_replace: app to replace

        Returns: a Qlik Sense App object for the new app
        """
        schema = AppSchema()
        request = util.QSAPIRequest(
            method='PUT',
            url=f'{self.url}/{app.id}/replace',
            params={'app': app_to_replace.id}
        )
        response = self._call(request)
        if 200 <= response.status_code < 300:
            return schema.loads(response.json())
        return None

    def download_file(self, url: str) -> 'Optional[Iterable]':
        """
        This method downloads an app given a download link

        Args:
            url: download path extension for the app (i.e., localhost/qrs/app/{this piece}

        Returns: the file as an iterable

        TODO: accept prepare_export() output instead of hard coded url, add option to auto-delete on success
        """
        request = util.QSAPIRequest(
            method='GET',
            url=f'{self.url}/{url}'
        )
        response = self._call(request)
        if 200 <= response.status_code < 300:
            return response.iter_content(chunk_size=512 << 10)
        return None
