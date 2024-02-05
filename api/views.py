from rest_framework.decorators import api_view
from rest_framework.response import Response
from . import tasks

@api_view(['POST'])
def import_view(request):
    data = request.data
    bro_object = data.get('bro_object')
    kvk_number = data.get('kvk_number')

    tasks.import_bro_data_task.delay(bro_object, kvk_number)

    return Response({'message': 'Task scheduled successfully'})
