import httplib2
import requests

from oauth2client.service_account import ServiceAccountCredentials
from apiclient import discovery

class GoogleSheet():
    spreadsheet_id = "1AwqAZzx9BEY85W05wn6s8A6cl3pxsZLNyrq8yQ9LLKE"
    
    def get_credentials(self):
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            '/home/pi/.credentials/gaia.json', scopes)
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        return discovery.build('sheets', 'v4', http=http,
                               discoveryServiceUrl=discoveryUrl)
    
    def publish(self, reading):
        last_reading = [
            reading["timestamp"],
            reading["name"],
            reading["temp"],
            reading.get("humidity", ""),
        ]
    
        service = self.get_credentials()
        request = service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range="Readings!A:A",
            valueInputOption="USER_ENTERED",
            body={
                "majorDimension": "ROWS",
                "values": [last_reading]
            })
        response = request.execute()
        print(response)
