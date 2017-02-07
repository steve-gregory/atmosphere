"""
 RESTful Site Metrics API
"""
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
from core.models import Instance


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
        site_metric = {
            "last_week": last_week_metrics,
            "last_month": last_month_metrics,
            "previous_week": prev_week_metrics,
            "previous_month": prev_month_metrics
        }
        return Response([site_metric])

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
