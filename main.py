import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon
from ui import Ui_MainWindow
from yandex_geocoder import Client
from urllib.request import urlopen
import requests
import json
import os


class MapCreator(QtWidgets.QMainWindow):
    def __init__(self):
        super(MapCreator, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.init_UI()
        self.coord = ()
        self.scale = 16

    # configurating UI
    def init_UI(self):
        # setting up images
        self.setWindowTitle("Карта и погода")
        self.setWindowIcon(QIcon(resource_path("map.png")))
        self.ui.image.setPixmap(QtGui.QPixmap(resource_path("newyork.jpg")))
        self.ui.label_4.setPixmap(QtGui.QPixmap(resource_path("temp.png")))
        self.ui.label_5.setPixmap(QtGui.QPixmap(resource_path("humidity.png")))
        self.ui.condition_icon.setPixmap(QtGui.QPixmap(resource_path("ovc.svg")))

        # placeholder for address
        self.ui.address_input.setPlaceholderText('Адрес:')

        # press enter instead of "MAP" button
        self.ui.button.setAutoDefault(True)

        # buttons call functions on click
        self.ui.address_input.returnPressed.connect(self.ui.button.click)
        self.ui.button.clicked.connect(self.get_link)
        self.ui.button.clicked.connect(self.get_weather)
        self.ui.plus.clicked.connect(self.get_link)
        self.ui.minus.clicked.connect(self.get_link)


        # add data to comboboxes - lang
        self.model = QtGui.QStandardItemModel()
        language_data = {
            'Русский': ('Российские', 'Украинские'),
            'Английский': ('Американские', 'Российские'),
            'Украинский': ('Украинские'),
            'Турецкий': ('Турецкие'),
        }

        # making comboboxes depended
        self.ui.measurement.setModel(self.model)
        self.ui.language.setModel(self.model)

        for k, v in language_data.items():
            state = QtGui.QStandardItem(k)
            self.model.appendRow(state)
            if isinstance(v, tuple):
                for value in v:
                    language = QtGui.QStandardItem(value)
                    state.appendRow(language)
            else:
                language = QtGui.QStandardItem(v)
                state.appendRow(language)

        self.ui.language.currentIndexChanged.connect(self.updateStateCombo)
        self.updateStateCombo(0)

    # updating comboboxes when user chooses another option
    def updateStateCombo(self, index):
        index = self.model.index(index, 0, self.ui.language.rootModelIndex())
        self.ui.measurement.setRootModelIndex(index)
        self.ui.measurement.setCurrentIndex(0)


    # getting link from static API
    def get_link(self):

        # format text to api request
        type_dict = {
            'Схема': 'map', 'Спутник': 'sat', 'Гибрид': 'sat,skl',
            'Русский': 'ru', 'Российские': 'RU',
            'Украинский': 'uk', 'Украинские': 'UA',
            'Турецкий': 'tr', 'Турецкие': 'TR',
            'Английский': 'en', 'Американские': 'US'
        }

        # geocoder
        API_KEY = ""
        client = Client(API_KEY)
        size = (640, 440)

        # find which button called function
        # zoom out and in
        sender = self.sender()
        if sender == self.ui.minus and self.scale > 0:
            self.scale -= 1
        elif sender == self.ui.plus and self.scale < 17:
            self.scale += 1
        elif sender == self.ui.minus or sender == self.ui.plus:
            print(self.scale)
            return

        # input read
        address = self.ui.address_input.text()
        map_type = type_dict[self.ui.type.currentText()]
        language = type_dict[self.ui.language.currentText()]
        measurement = type_dict[self.ui.measurement.currentText()]

        # traffic check
        if self.ui.traffic_check.isChecked():
            map_type += ',trf'

        # bad request check or no internet
        try:
            self.coord = client.coordinates(address)
            URL = f"https://static-maps.yandex.ru/1.x/?ll={self.coord[0]},{self.coord[1]}&size={size[0]},{size[1]}" \
                  f"&z={self.scale}&l={map_type}&pt={self.coord[0]},{self.coord[1]},pm2gnm&lang={language}_{measurement}"
            print(URL)
            data = urlopen(URL).read()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            self.ui.image.setPixmap(pixmap)
        except:
            self.ui.image.setText("Ничего не найдено!")

    # weather api request
    def get_weather(self):

        # format text to api request
        weather_dict = {'clear': ('Ясно', 11),
                        'partly-cloudy': ('Малооблачно', 8),
                        'cloudy': ('Облачно с прояснениями', 5),
                        'overcast': ('Пасмурно', 11),
                        'drizzle': ('Морось', 11),
                        'light-rain': ('Небольшой дождь', 7),
                        'rain': ('Дождь', 11),
                        'moderate-rain': ('Умеренно сильный дождь', 5),
                        'heavy-rain': ('Сильный дождь', 7),
                        'continuous-heavy-rain': ('Длительный сильный дождь', 5),
                        'showers': ('Ливень', 11),
                        'wet-snow': ('Дождь со снегом', 7),
                        'light-snow': ('Небольшой снег', 7),
                        'snow': ('Снег', 11),
                        'snow-showers': ('Снегопад', 11),
                        'hail': ('Град', 11),
                        'thunderstorm': ('Гроза', 11),
                        'thunderstorm-with-rain': ('Дождь с грозой', 7),
                        'thunderstorm-with-hail': ('Гроза с градом', 7)
                        }
        
        # Yandex MAPS API
        api_key = ""

        #check for bad request or no internet
        try:
            #getting information from api
            response = requests.get(f'https://api.weather.yandex.ru/v2/forecast?lat={self.coord[1]}&lon={self.coord[0]}&extra=true',
                                    headers={'X-Yandex-API-Key': api_key})
            weather_json = json.loads(response.text)
            condition = weather_json["fact"]["condition"]
            icon = weather_json['fact']['icon']
            humidity = weather_json["fact"]["humidity"]
            temp = weather_json['fact']['temp']

            # getting weather icon depending on weather
            url = f'https://yastatic.net/weather/i/icons/blueye/color/svg/{icon}.svg'
            data = urlopen(url).read()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            self.ui.condition_icon.setPixmap(pixmap)

            # set weather description (humidity, condition, etc.)
            self.ui.conditionlabel.setText(weather_dict[condition][0])
            font = QtGui.QFont()
            font.setFamily("Arial Black")
            font.setPointSize(weather_dict[condition][1])
            font.setBold(True)
            font.setWeight(75)
            self.ui.conditionlabel.setFont(font)
            self.ui.humidity_label.setText(str(humidity) + '%')
            self.ui.temp_label.setText(str(temp) + '°C')
            print(condition, icon, humidity)
            print(self.coord)
        except:
            pass


# for packing to .exe
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


app = QtWidgets.QApplication([])
application = MapCreator()
application.show()

sys.exit(app.exec())
