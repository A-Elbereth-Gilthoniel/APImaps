import os
import sys

import requests

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QMainWindow, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        self.z_value = 10
        self.modes = [
            "map",
            "sat",
            "sat,skl"
        ]
        self.mode = 0
        self.cords = "37.732504,55.753215"
        self.pt = None
        self.postal_code = ''
        uic.loadUi('map.ui', self)
        self.setWindowTitle('Maps API')

        self.lBtn.setFlat(True)
        self.lBtn.setStyleSheet("background-image : url(data/map.png)")
        self.lBtn.clicked.connect(self.change_l)

        self.addressBtn.clicked.connect(self.address_find)

        self.resetBtn.clicked.connect(self.reset)
        self.indexBtn.clicked.connect(self.change_postal_code)
        self.label.setFocus()

        self.render_map()

    def getImage(self):
        map_params = {
            "ll": f"{self.cords}",
            "z": f"{self.z_value}",
            "l": f"{self.modes[self.mode]}",
            "pt": self.pt
        }
        map_request = "http://static-maps.yandex.ru/1.x/"
        response = requests.get(map_request, params=map_params)

        if not response:
            print("Ошибка выполнения запроса:")
            print(map_request)
            print("Http статус:", response.status_code, "(", response.reason, ")")
            sys.exit(1)

        self.map_file = "map.png"
        with open(self.map_file, "wb") as file:
            file.write(response.content)

    def closeEvent(self, event):
        os.remove(self.map_file)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_PageUp:
            if self.z_value < 17:
                self.z_value += 1
        elif event.key() == Qt.Key_PageDown:
            if self.z_value > 0:
                self.z_value -= 1
        elif event.key() == Qt.Key_Left:
            x, y = self.cords.split(",")
            x = float(x) - (180 / (2 ** self.z_value))
            x = x + 360 if x < -180 else x
            self.cords = f"{x},{y}"
        elif event.key() == Qt.Key_Right:
            x, y = self.cords.split(",")
            x = float(x) + (180 / (2 ** self.z_value))
            x = x - 360 if x >= 180 else x
            self.cords = f"{x},{y}"
        elif event.key() == Qt.Key_Up:
            x, y = self.cords.split(",")
            if float(y) + (180 / (2 ** self.z_value)) < 84:
                y = float(y) + (180 / (2 ** self.z_value))
            self.cords = f"{x},{y}"
        elif event.key() == Qt.Key_Down:
            x, y = self.cords.split(",")
            if float(y) - (180 / (2 ** self.z_value)) > -84:
                y = float(y) - (180 / (2 ** self.z_value))
            self.cords = f"{x},{y}"

        self.render_map()

    def render_map(self):
        self.getImage()
        self.pixmap = QPixmap(self.map_file)
        self.label.setPixmap(self.pixmap)

    def change_l(self):
        self.mode = (self.mode + 1) % 3
        self.lBtn.setStyleSheet(f"background-image : url(data/{self.modes[self.mode]}.png)")
        self.render_map()

    def address_find(self):
        text = self.address.text()
        if text:
            geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
            geocoder_params = {
                "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
                "geocode": text,
                "format": "json"}
            response = requests.get(geocoder_api_server, params=geocoder_params)
            if not response:
                print("Ошибка выполнения запроса:")
                print(geocoder_api_server)
                print("Http статус:", response.status_code, "(", response.reason, ")")
                sys.exit(1)
            self.json_response = response.json()
            if self.json_response["response"]["GeoObjectCollection"]["metaDataProperty"] \
                    ["GeocoderResponseMetaData"]["found"] != "0":
                toponym_cords = self.json_response["response"]["GeoObjectCollection"][
                    "featureMember"][0]["GeoObject"]["Point"]["pos"]
                toponym_longitude, toponym_lattitude = toponym_cords.split(" ")
                self.cords = f"{toponym_longitude},{toponym_lattitude}"
                self.pt = f"{toponym_longitude},{toponym_lattitude},ya_ru"
                self.addressTxt.setPlainText(', '.join(self.json_response["response"]
                                                           ["GeoObjectCollection"]
                                                           ["featureMember"][0]["GeoObject"]
                                                           ["metaDataProperty"]["GeocoderMetaData"]
                                                           ["text"].split(', ')[:-1]))
                self.render_map()

    def reset(self):
        self.z_value = 10
        self.mode = 0
        self.cords = "37.732504,55.753215"
        self.pt = None
        self.address.setText("")
        self.lBtn.setStyleSheet("background-image : url(data/map.png)")
        self.addressTxt.setPlainText('')
        self.render_map()

    def mouseReleaseEvent(self, event):
        if event.x() >= 300:
            self.label.setFocus()

    def change_postal_code(self):
        try:
            if self.postal_code == '':
                self.postal_code = '\nПочтовый индекс: {}'.format(self.json_response["response"]['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['Address']['postal_code'])
                self.addressTxt.setPlainText(self.addressTxt.toPlainText() + self.postal_code)
            else:
                self.postal_code = ''
                self.addressTxt.setPlainText(self.addressTxt.toPlainText().split('\nПочтовый индекс: ')[0])
        except:
            QMessageBox.warning(self, 'Внимание!', 'Почтовый индекс данного объекта неизвестен.\
             Все вопросы к Яндексу.')
            self.postal_code = ''



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec())
