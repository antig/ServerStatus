#!/usr/bin/python
# coding: utf-8

# ServerStatus - game.py
# 2018/10/4 10:00
#

__author__ = "Benny <benny@bennythink.com>"

import logging
import time

from valve.source.a2s import ServerQuerier

from serverstatus.config import GAME
from serverstatus.constants import L4D2
from serverstatus.utils import Mongo, BaseSSH, template


class SourceServer(BaseSSH):
    """
    Obtain information from Source Server and systemd
    """

    def __init__(self, conf):
        # valve server maybe inactive
        super().__init__(conf)
        self.__host = conf
        try:
            self.__server = ServerQuerier((conf['host'], conf['port']))
            self.game = self.__server.info().values
        except Exception as e:
            logging.warning(e)
            self.game = {'server_name': None, 'map': '', 'game': None, 'app_id': None, 'player_count': None,
                         'max_players': None}

    def __del__(self):
        self.ssh.close()
        if self.game['game']:
            self.__server.close()

    def parse_info(self):
        """
        process gathered and form it to dict.
        :return: json
        """
        game = L4D2.get(self.game['app_id'])
        name = self.game['server_name']
        h = self.__host
        address = f"{h['host']}:{h['port']}"

        map_name = L4D2.get(self.game['map'].lower(), self.game['map'])
        player = f"{self.game['player_count']}/{self.game['max_players']}"

        cpu, memory, _, status_bool, status_msg = self.systemd_info()

        response = dict(app_id=self.__host['app_id'], game=game, name=name, address=address, map=map_name,
                        player=player, cpu=cpu, memory=memory, status=[status_bool, status_msg, time.time()])
        return response


class SourceMongo(Mongo):
    @staticmethod
    def get_status():
        """
        form entire data field provide with config for each request
        :return: [{},{}]
        """
        data = [SourceServer(i).parse_info() for i in GAME]
        return data


def game_response():
    c, lst = template('game')
    c['data'] = SourceMongo('game_status').get_many(lst)
    return c


def game_sync():
    SourceMongo('game_status').insert_record()
