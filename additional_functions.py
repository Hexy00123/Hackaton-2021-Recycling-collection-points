from requests import request, get, post
import math


def get_coords(address):
    response = request(method='GET', url='https://geocode-maps.yandex.ru/1.x', params={
                       'geocode': address, 'apikey': "40d1649f-0493-4b70-98ba-98533de7710b", 'format': 'json', })
    try:
        response = response.json(
        )['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        return (True, ','.join(response.split()))

    except:
        return (False, response.reason)


def get_image(ll, size=12, map_type='map', dots=[]):
    try:
        if ll:
            points = [(ll, 'ya_ru')]+[(i[1], i[2]) for i in dots]
        else:
            points = [(i[1], i[2]) for i in dots]
        pt = '~'.join(','.join(i) for i in points).replace('\t', '')
        if len(points) == 1:
            response = request(method='GET', url='https://static-maps.yandex.ru/1.x/',
                               params={'ll': ll, 'z': str(size),
                                       'l': map_type, 'size': '450,450', 'pt': pt})
        else:
            response = request(method='GET', url='https://static-maps.yandex.ru/1.x/',
                               params={'l': map_type, 'size': '450,450', 'pt': pt})
        if response.status_code == 400:
            print(response.text)
        print(response.url)
        return response.url
    except Exception as e:
        print(e)
        exit(0)


def count_lenght(s1, d1, s2, d2):
    degree_to_meters_factor = 111 * 1000
    a_lon, a_lat = float(d1), float(s1)
    b_lon, b_lat = float(d2), float(s2)
    radians_lattitude = math.radians((a_lat + b_lat) / 2.)
    lat_lon_factor = math.cos(radians_lattitude)
    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor
    distance = math.sqrt(dx * dx + dy * dy)
    return round(distance)


POINTS = [
    'org',
    'comma',
    'round',
    'home',
    'work',
    'vkbkm',
    'vkgrm',
    'ya_ru', ]

MAP_TYPES = [
    'sat',
    'map',
    'sat,skl',
]

RECYCLING_TYPES = [
    'Батарейки',
    'Бумажная_мукулатура',
    'Галогеновые_лампы',
    'Металлолом',
    'ПЭТ',

]
