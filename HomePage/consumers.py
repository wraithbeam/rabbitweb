import copy
import json
from threading import Thread

from asgiref.sync import sync_to_async, async_to_sync
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from .models import Participant, MeetingParticipants, Meeting

from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is not None:
            text_data_json = json.loads(text_data)
            image = text_data_json["webcam"]
            person_id = text_data_json["person"]
            meeting = text_data_json["meeting"]
            if image is not None:
                try:
                    participant = await Participant.objects.aget(person=person_id)
                    participant.webcam_meta = image
                    await sync_to_async(participant.save)()
                    await sync_to_async(self.send_data)(meeting)
                except ObjectDoesNotExist:
                    print("Объект не сушествует")
                except MultipleObjectsReturned:
                    print("Найдено более одного объекта")

    def send_data(self, meeting_link):
        print(meeting_link)
        meeting = Meeting.objects.filter(link=meeting_link).get()
        data = {}
        for meeting_participant in MeetingParticipants.objects.filter(meeting=meeting.id):
            person = meeting_participant.person
            data[person.person.last_name + "_" + person.person.first_name] = {
                'mic': person.mic,
                'spk': True,
                'webcam': person.webcam,
                'mic_meta': person.mic_meta,
                'webcam_meta': person.webcam_meta
            }
        async_to_sync(self.send)(json.dumps(data))
