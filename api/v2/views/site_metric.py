"""
 RESTful Site Metrics API
"""
import ipaddress

from dateutil.parser import parse
from django.db.models import Q
from django.utils import timezone

from rest_framework import exceptions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings

from api.renderers import PandasExcelRenderer
from api.v2.exceptions import failure_response
from api.v2.views.base import AuthAPIViewset
from core.models import Instance, Provider
from service.driver import get_account_driver


class SiteMetricViewSet(AuthAPIViewset):
    ordering_fields = ('id', 'start_date')
    http_method_names = ['get', 'head', 'options', 'trace']

    def list(self, request, format=None):
        """
        Force an abnormal behavior for 'details' calls (force a list call)
        """
        last_week = timezone.now() - timezone.timedelta(days=7)
        two_weeks_ago = timezone.now() - timezone.timedelta(days=14)
        last_month = timezone.now() - timezone.timedelta(days=30)
        two_months_ago = timezone.now() - timezone.timedelta(days=60)
        last_week_metrics = self._get_metrics(last_week)
        prev_week_metrics = self._get_metrics(two_weeks_ago, last_week)
        last_month_metrics = self._get_metrics(last_month)
        prev_month_metrics = self._get_metrics(two_months_ago, last_month)
        provider_metrics = self._get_provider_metrics()
        site_metric = {
            "provider": provider_metrics,
            "last_week": last_week_metrics,
            "last_month": last_month_metrics,
            "previous_week": prev_week_metrics,
            "previous_month": prev_month_metrics
        }
        return Response([site_metric])

    def _get_provider_metrics(self):
        prov_metrics = {}
        for prov in Provider.get_active():
            if prov.type.name.lower() != 'openstack':
                continue
            search_public_network_args = {
                "router:external": True,
                "shared": True,
                }
            accounts = get_account_driver(prov)
            public_networks = accounts.network_manager.list_networks(
                **search_public_network_args)
            public_subnet_ids = []
            for pub_net in public_networks:
                public_subnet_ids.extend(pub_net['subnets'])
            subnets = accounts.network_manager.list_subnets()
            public_subnets = [sn for sn in subnets if sn['id'] in public_subnet_ids]
            ip_space = []
            for psn in public_subnets:
                ip_space.extend(ipaddress.ip_network(psn['cidr']))
            ip_allocated = accounts.network_manager.list_floating_ips()
            prov_metrics[str(prov.uuid)] = {
                "floating_ips_total": len(ip_space),
                "floating_ips_allocated": len(ip_allocated),
            }
        return prov_metrics

    def _get_metrics(self, start_date, start_date_end=None):
        instances = Instance.objects.filter(start_date__gt=start_date)
        if start_date_end:
            instances.filter(start_date__lt=start_date_end)
        instances_launched = instances.count()
        launch_failure = len([i for i in instances if not i.launch_success()])
        metrics = {
            "instances_launched": instances_launched,
            "launch_failure": launch_failure,
        }
        return metrics
