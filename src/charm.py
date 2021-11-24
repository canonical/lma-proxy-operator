#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright 2021 Canonical Ltd.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
# Learn more at: https://juju.is/docs/sdk

"""Hello, Juju example charm.

This charm is a demonstration of a machine charm written using the Charmed
Operator Framework. It deploys a simple Python Flask web application and
implements a relation to the PostgreSQL charm.
"""

import logging

from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardAggregator
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointAggregator
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus

logger = logging.getLogger(__name__)


class LMAProxyCharm(CharmBase):
    """This charm provides an interface between machine/reactive charms and Charmed Operators."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        self._stored.set_default(
            have_grafana=False, have_dashboards=False, have_prometheus=False, have_targets=False
        )

        self._dashboard_aggregator = GrafanaDashboardAggregator(self)

        self.framework.observe(
            self.on.dashboards_relation_joined,
            self._dashboards_relation_joined,
        )

        self.framework.observe(
            self.on.dashboards_relation_broken,
            self._dashboards_relation_broken,
        )

        self.framework.observe(
            self.on.downstream_grafana_dashboard_relation_joined,
            self._downstream_grafana_dashboard_relation_joined,
        )

        self.framework.observe(
            self.on.downstream_grafana_dashboard_relation_broken,
            self._downstream_grafana_dashboard_relation_broken,
        )

        self._metrics_aggregator = MetricsEndpointAggregator(
            self,
            {
                "prometheus": "downstream-prometheus-scrape",
                "scrape_target": "prometheus-target",
                "alert_rules": "prometheus-rules",
            },
        )

        self.framework.observe(
            self.on.prometheus_target_relation_joined,
            self._prometheus_target_relation_joined,
        )

        self.framework.observe(
            self.on.prometheus_target_relation_broken,
            self._prometheus_target_relation_broken,
        )

        self.framework.observe(
            self.on.downstream_prometheus_scrape_relation_joined,
            self._downstream_prometheus_scrape_relation_joined,
        )

        self.framework.observe(
            self.on.downstream_prometheus_scrape_relation_broken,
            self._downstream_prometheus_scrape_relation_broken,
        )

        self._set_status()

    def _dashboards_relation_joined(self, _):
        self._stored.have_dashboards = True
        self._set_status()

    def _dashboards_relation_broken(self, _):
        self._stored.have_dashboards = False
        self._set_status()

    def _downstream_grafana_dashboard_relation_joined(self, _):
        self._stored.have_grafana = True
        self._set_status()

    def _downstream_grafana_dashboard_relation_broken(self, _):
        self._stored.have_grafana = False
        self._set_status()

    def _prometheus_target_relation_joined(self, _):
        self._stored.have_targets = True
        self._set_status()

    def _prometheus_target_relation_broken(self, _):
        self._stored.have_targets = False
        self._set_status()

    def _downstream_prometheus_scrape_relation_joined(self, _):
        self._stored.have_prometheus = True
        self._set_status()

    def _downstream_prometheus_scrape_relation_broken(self, _):
        self._stored.have_prometheus = False
        self._set_status()

    def _set_status(self):
        message = ""
        if (self._stored.have_grafana and not self._stored.have_dashboards) or (
            self._stored.have_dashboards and not self._stored.have_grafana
        ):
            message = " one of (Grafana|dashboard) relation(s) "

        if (self._stored.have_prometheus and not self._stored.have_targets) or (
            self._stored.have_targets and not self._stored.have_prometheus
        ):
            message += "{} one of (Prometheus|target) relation(s)".format("and" if message else "")

        message = "Missing {}".format(message.strip()) if message else ""

        if message:
            self.unit.status = BlockedStatus(message)
        else:
            self.unit.status = ActiveStatus()


if __name__ == "__main__":  # pragma: no cover
    main(LMAProxyCharm)
