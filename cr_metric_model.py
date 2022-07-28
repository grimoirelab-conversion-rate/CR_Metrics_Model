#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2022 Yehu Wang, Chenqi Shan
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Yehu Wang <yehui.wang.mdh@gmail.com>
#     Chenqi Shan <chenqishan337@gmail.com>
#     TieWay59 <tieway59@foxmail.com>

from perceval.backend import uuid
from datetime import datetime, timedelta
import json
import yaml
import pandas as pd
import ssl, certifi
from grimoire_elk.enriched.utils import get_time_diff_days
from grimoirelab_toolkit.datetime import (
    datetime_utcnow,
    str_to_datetime,
    datetime_to_utc,
)
from elasticsearch import Elasticsearch, RequestsHttpConnection
from grimoire_elk.elastic import ElasticSearch

MAX_BULK_UPDATE_SIZE = 100


def get_date_list(begin_date, end_date, freq="W-MON"):
    """Get date list from begin_date to end_date every Monday"""
    date_list = [
        x
        for x in list(
            pd.date_range(
                freq=freq,
                start=datetime_to_utc(str_to_datetime(begin_date)),
                end=datetime_to_utc(str_to_datetime(end_date)),
            )
        )
    ]
    return date_list


def get_all_project(file):
    """Get all projects from json file"""
    file_json = json.load(open(file))
    all_project = []
    for i in file_json:
        all_project.append(i)
    return all_project


def get_time_diff_months(start, end):
    """Number of months between two dates in UTC format"""

    if start is None or end is None:
        return None

    if type(start) is not datetime:
        start = str_to_datetime(start).replace(tzinfo=None)
    if type(end) is not datetime:
        end = str_to_datetime(end).replace(tzinfo=None)

    seconds_month = float(60 * 60 * 24 * 30)
    diff_months = (end - start).total_seconds() / seconds_month
    diff_months = float("%.2f" % diff_months)

    return diff_months


class MetricsModel:
    def __init__(self, json_file, out_index=None, community=None, level=None):
        """Metrics Model is designed for the integration of multiple CHAOSS metrics.
        :param json_file: the path of json file containing repository message.
        :param out_index: target index for Metrics Model.
        :param community: used to mark the repo belongs to which community.
        :param level: str representation of the metrics, choose from repo, project, community.
        """
        self.json_file = json_file
        self.out_index = out_index
        self.community = community
        self.level = level

    def metrics_model_metrics(self):
        self.es_in = Elasticsearch(
            elastic_url,
            use_ssl=True,
            verify_certs=False,
            connection_class=RequestsHttpConnection,
        )
        self.es_out = ElasticSearch(elastic_url, self.out_index)

        if self.level == "community":
            all_repos_list = self.all_repo
            label = "community"
            self.metrics_model_enrich(all_repos_list, self.community)

        if self.level == "project":
            all_repo_json = json.load(open(self.json_file))
            for project in all_repo_json:
                repos_list = []
                for j in all_repo_json[project][self.issue_index.split("_")[0]]:
                    repos_list.append(j)
                self.metrics_model_enrich(repos_list, project)

        if self.level == "repo":
            all_repo_json = json.load(open(self.json_file))
            for project in all_repo_json:
                for j in all_repo_json[project][self.issue_index.split("_")[0]]:
                    self.metrics_model_enrich([j], j)

    def metrics_model_enrich(repos_list, label):
        pass

    def get_uuid_count_query(
        self,
        option,
        repos_list,
        field,
        date_field="grimoire_creation_date",
        from_date=str_to_datetime("1970-01-01"),
        to_date=datetime_utcnow(),
    ):
        query = {
            "size": 0,
            "track_total_hits": "true",
            "aggs": {"count_of_uuid": {option: {"field": field}}},
            "query": {
                "bool": {
                    "should": [
                        {
                            "simple_query_string": {
                                "query": i + "*",
                                "fields": ["origin"],
                            }
                        }
                        for i in repos_list
                    ],
                    "minimum_should_match": 1,
                    "filter": {
                        "range": {
                            date_field: {
                                "gte": from_date.strftime("%Y-%m-%d"),
                                "lt": to_date.strftime("%Y-%m-%d"),
                            }
                        }
                    },
                }
            },
        }
        return query

    def get_uuid_count_contribute_query(
        self,
        project,
        company=None,
        from_date=str_to_datetime("1970-01-01"),
        to_date=datetime_utcnow(),
    ):
        query = {
            "size": 0,
            "aggs": {
                "count_of_contributors": {
                    "cardinality": {
                        "script": "if (doc['author_domain'].size()>0){ return doc['author_name'].value }  else { return doc['author_name'].value}"
                    }
                }
            },
            "query": {
                "bool": {
                    "should": [
                        {"simple_query_string": {"query": i, "fields": ["project"]}}
                        for i in project
                    ],
                    "minimum_should_match": 1,
                    "filter": {
                        "range": {
                            "grimoire_creation_date": {
                                "gte": from_date.strftime("%Y-%m-%d"),
                                "lt": to_date.strftime("%Y-%m-%d"),
                            }
                        }
                    },
                }
            },
        }

        if company:
            query["query"]["bool"]["must"] = [
                {
                    "bool": {
                        "should": [
                            {
                                "simple_query_string": {
                                    "query": j + "*",
                                    "fields": ["author_domain"],
                                }
                            }
                            for j in company
                        ],
                        "minimum_should_match": 1,
                    }
                }
            ]
        return query

    def get_created_since_query(self, repo, order="asc"):
        query = {
            "query": {
                "bool": {
                    "should": [{"match_phrase": {"tag": repo + ".git"}}],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"grimoire_creation_date": {"order": order}}],
        }
        return query

    def get_updated_since_query(self, repository_url, date):
        query = """
            {
                "track_total_hits":true,
                "query": {
                    "bool": {
                        "filter": [
                            {
                                "term": {
                                    "origin": "%s"
                                }
                            },
                            {
                                "range": {
                                    "metadata__updated_on": {
                                        "lt": "%s"
                                    }
                                }
                            }
                        ]
                    }
                },
                    "sort": [
                {
                "metadata__updated_on": { "order": "desc"}
                }]
            }
            """ % (
            repository_url,
            date.strftime("%Y-%m-%d"),
        )
        return query

    def get_issue_closed_uuid_count(
        self,
        option,
        repos_list,
        field,
        from_date=str_to_datetime("1970-01-01"),
        to_date=datetime_utcnow(),
    ):
        query = {
            "size": 0,
            "track_total_hits": True,
            "aggs": {"count_of_uuid": {option: {"field": field}}},
            "query": {
                "bool": {
                    "must": [
                        {
                            "bool": {
                                "should": [
                                    {
                                        "simple_query_string": {
                                            "query": i,
                                            "fields": ["tag"],
                                        }
                                    }
                                    for i in repos_list
                                ],
                                "minimum_should_match": 1,
                            }
                        }
                    ],
                    "must_not": [
                        {"term": {"state": "open"}},
                        {"term": {"state": "progressing"}},
                    ],
                    "filter": {
                        "range": {
                            "closed_at": {
                                "gte": from_date.strftime("%Y-%m-%d"),
                                "lt": to_date.strftime("%Y-%m-%d"),
                            }
                        }
                    },
                }
            },
        }

        return query


class ConversionRate_MetricsModel(MetricsModel):
    """
    TODO list what is needed for `ConversionRate_MetricsModel`
    TODO metrics_model_enrich
    TODO metrics_model_metrics
    """


if __name__ == "__main__":
    CONF = yaml.safe_load(open("conf.yaml"))
    elastic_url = CONF["url"]
    kwargs = CONF["params"]

    # TODO add running examples here 
    
