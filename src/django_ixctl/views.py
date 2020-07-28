from django.http import HttpResponse

from django_ixctl.models import Exchange, ExchangeMember

def index(request):
    output = ', '.join([e.name for e in Exchange.objects.all()])
    output += "\n"
    output += ', '.join([e.name for e in ExchangeMember.objects.all()])
    return HttpResponse(output)
