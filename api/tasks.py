from celery import shared_task
from time import sleep

@shared_task
def import_task(bro_object, kvk_number):
    pass