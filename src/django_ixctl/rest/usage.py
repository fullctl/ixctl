from fullctl.django.rest.usage import UsageMetric, register

import django_ixctl.models as models

@register
class Members(UsageMetric):

    class Meta:
        name = "fullctl.ixctl.members"

    def calc(self, start, end):
        return models.InternetExchangeMember.objects.filter(ix__instance__org=self.org).count()

