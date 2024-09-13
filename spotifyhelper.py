#!/usr/bin/env python3

from api import SpotifyAPI
from fire import Fire
from log import (
    get_logger,
    trace_func
)
import json
import sys

log = get_logger('spotify-helper')


class SpotifyHelper:

    _default_save_name: str = "__default__save__"
    api: SpotifyAPI
    saved: dict

    def __init__(
        self,
        client_id: str,
        client_secret: str,
    ):
        self.api = SpotifyAPI(
            client_id,
            client_secret
        )
        self.saved = {}

    @trace_func(log)
    def save(
        self,
        name: str,
        data: any
    ):
        """
        Save data

        Args:
            name (str): Name of saved data
            data (any): Data to save. Needs to be JSON serializable.
        """
        log.info(f'Saving data: {name}')
        self.saved[name] = data

    @trace_func(log)
    def search_by_genre(
        self,
        genre: str,
        save: str = _default_save_name
    ):
        """
        Search tracks by genre

        Args:
            genre (str): Genre to search by
            save (str): Save name for the results
        """
        log.info(f'Searching by genre: {genre}')
        query = {
            'q': f'genre:"{genre}"',
            'type': 'track',
        }
        tracks = self.api.request_paginated(
            'search',
            query=query,
            parser=lambda v: (
                v
                .get('tracks', {})
                .get('items', [])
            )
        )
        self.save(save, list(tracks))
        return self

    @trace_func(log)
    def fetch_my_tracks(
        self,
        limit: int = None,
        save: str = _default_save_name
    ):
        """
        Fetch user tracks
        """
        log.info('Fetching user tracks')
        tracks = self.api.request_paginated(
            'me/tracks',
            parser=lambda res: [
                item['track']
                for item in res.get('items', [])
                if 'track' in item
            ]
        )
        if limit is not None:
            tracks = list(tracks)[:limit]
        self.save(save, list(tracks))
        return self

    @trace_func(log)
    def _has_genre(
        self,
        track: dict,
        genre: str
    ):
        """
        Check if track has genre

        Args:
            track (dict): Track to check
            genre (str): Genre to check
        """
        track_id = track.get('id')
        track_name = track.get('name')
        search_results = self.api.request(
            'search',
            query={
                'q': f'track:"{track_name}" genre:"{genre}"',
                'type': 'track',
            },
            parser=lambda v: (
                v
                .get('tracks', {})
                .get('items', [])
            )
        )
        ids = [t.get('id') for t in search_results]
        if track_id in ids:
            return True

    @trace_func(log)
    def filter_by_genre(
        self,
        genre: str,
        load: str = _default_save_name,
        save: str = _default_save_name
    ):
        """
        Filter tracks by genre

        Args:
            genre (str): Genre to filter by
            load (str): Load name for the data
            save (str): Save name for the results
        """
        log.info(f'Filtering by genre: {genre}')
        tracks = self.saved[load]
        filtered = [
            t for t in tracks
            if self._has_genre(t, genre)
        ]
        self.save(save, filtered)
        return self

    @trace_func(log)
    def print(
        self,
        name: str | None = None,
        pretty: bool = False
    ):
        """
        Print saved data

        Args:
            name (str | None): Name of saved data. By default, print all saved data.
            pretty (bool): Pretty print saved data.
        """
        log.info(f'Printing saved data: {name}')
        json.dump(
            self.saved[name] if name is not None else self.saved,
            sys.stdout,
            indent=2 if pretty else None
        )

    @trace_func(log)
    def end():
        """
        End the command
        """
        log.info('Ending')
        return self



if __name__ == '__main__':
    Fire(SpotifyHelper)
