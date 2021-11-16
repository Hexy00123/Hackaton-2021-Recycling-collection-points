from config import *
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from requests import request, get, post
from additional_functions import *
from model import *
import smtplib


def start(update, context):
    context.user_data['map_size'] = 12
    context.user_data['map_type'] = 'map'
    context.user_data['additional_points'] = []
    update.message.reply_text(
        '''Привет, я бот для определения ближайших пунктов сбора вторсырья.
Мои команды:
/start - команда, которую вы видите сейчас
/help - отображает все доступные пользователю команды и их описание
 ''')


def help(update, context):
    update.message.reply_text(f'''
/all - отображает все точки приема любого вторсырья

/near <type>;<address> - Взамен <addres> вставьте адрес относительно которого вы хотите получить ближайшие точки приема. Взамен <type> - типы вторсырья: {", ".join(RECYCLING_TYPES)}. Бот выведет вам ближайшие пункты сбора вторсырья к этой точке

/user_data - Данные, дополнительно введеные вами

/change_size <size> - Взамен <size> впишите размер карты от 1 до 16, где 16 - очень близко к точке, 1 - очень далеко от точки, 11 - по размеру сопоставима с размерами карты Самары.

/add_point <address> <type> - Взамен <address> - адрес точки; <type> - может принимать значения:
  org — голубая метка с хвостиком;
  comma — голубая метка с кругом в центре;
  round — голубая метка в виде круга;
  home — значок дома;
  work — значок работы;
  vkbkm — черная кнопка;
  vkgrm — серая кнопка;
  ya_ru — значок с логотипом Яндекса.
  Создает новую точку на карте, которая видна только вам, можете использовать это в личных целях.

/change_map_type <type> Взамен <type> впишите тип карты: {'; '.join(MAP_TYPES)};

/new_recycling_point <description> - Взамен <description> вставьте описание. Если вы нашли точку сбора мусора, которая не отмечена на нашей карте, то вы можете отправить запрос модераторам, они рассмотрят вашу заявку и в скором времени добавят новую точку на карту.
''')


def user_data(update, context):
    try:
        temp = '\n'
        update.message.reply_text(f'''
Размер карты: {context.user_data['map_size']}
Тип карты: {context.user_data['map_type']}
Дополнительные точки:
{f"{temp}".join(f"{num}) Адрес: {x[0]}; Тип: {x[2]}" for num,
                x in enumerate(context.user_data["additional_points"],1))}

''')
    except Exception as e:
        if e == 'map_size':
            update.message.reply_text('Введите /start')
        else:
            print(e)


def change_size(update, context):
    size = update.message.text.replace('/change_size', '')
    print(size)
    if 1 <= int(size) <= 16:
        context.user_data['map_size'] = int(size)
        update.message.reply_text(f'Размер карты изменен на {size}')
    else:
        update.message.reply_text('Неправильный ввод')


def change_map_type(update, context):
    type = update.message.text.replace('/change_map_type', '').strip()
    print(type)
    if type in MAP_TYPES:
        context.user_data['map_type'] = type
        update.message.reply_text(f'Тип карты изменен на {type}')
    else:
        update.message.reply_text('Неправильный ввод')


def echo(update, context):
    text = update.message.text
    coords = get_coords(text)
    if coords[0]:
        update.message.reply_text(f'{coords[1]}')
        # [('50.197912,53.207394', 'org')] - если надо прилепить точку
        try:
            image = get_image(coords[1], size=context.user_data['map_size'],
                              map_type=context.user_data['map_type'],
                              dots=context.user_data['additional_points'])
            update.message.reply_photo(photo=image)
        except:
            update.message.reply_text('Введите /start')

    else:
        update.message.reply_text(f'По вашему запросу ничего не найдено')


def add_point(update, context):
    try:
        text = update.message.text
        address, type = ' '.join(text.split()[1:-1]), text.split()[-1]
        coords = get_coords(address)
        if not coords[0]:
            update.message.reply_text('Неверно указан адрес точки')
        elif type not in POINTS:
            update.message.reply_text('Неверно указан тип точки')
        else:
            ll = coords[1]
            print(f'Адрес: {address}\n type: {type}\n coords: {ll}')
            update.message.reply_text(f'''
Добавлена точка.
Адрес: {address}
Координаты: {ll}
Тип: {type}''')
            context.user_data['additional_points'].append([address, ll, type])

    except Exception as e:
        print(e)


def remove_point(update, context):
    try:
        text = update.message.text.split()[-1]
        id = int(text)-1
        if id < len(context.user_data['additional_points']) and \
                context.user_data['additional_points'] and text != '0':
            point = context.user_data['additional_points'].pop(id)
            update.message.reply_text(f'''
Удалена точка под номером {id+1}
Адрес: {point[0]}; Тип: {point[2]}''')
        else:
            update.message.reply_text('Такой точки не существует.')

    except Exception as e:
        print(e)


def near(update, context):
    try:
        type, address = update.message.text.replace('/near', '').split(';')
        type = type.strip().lower()
        if len(type) == 3:
            type = type.upper()
        else:
            type = type.capitalize()
        ll = get_coords(address)
        if ll[0]:
            ll = ll[1].split(',')
            points = [(point[1], point[2].replace(' ', '').split(',')[::-1], point[3])
                      for point in db.find_all(type)]
            nearest = min(points, key=lambda point: count_lenght(
                ll[1], ll[0], point[1][1], point[1][0]))
            lenght = count_lenght(ll[1], ll[0], nearest[1][1], nearest[1][0])
            if type == 'Батарейки':
                dot_type = 'pmdbs'
            elif type == 'Бумажная_мукулатура':
                dot_type = 'pmwts'
            elif type == 'Галогеновые_лампы':
                dot_type = 'pmyws'
            elif type == 'Металлолом':
                dot_type = 'pmgrs'
            elif type == 'ПЭТ':
                dot_type = 'pmgns'
            image = get_image(','.join(ll), size=context.user_data['map_size'],
                              map_type=context.user_data['map_type'],
                              dots=[['', ','.join(nearest[1]), dot_type]])

            update.message.reply_photo(photo=image,
                                       caption=f'Адрес: {nearest[0]}\nВремя работы: {nearest[2]}\nРасстояние: {lenght} метров')
        else:
            update.message.reply_text('Неверно указан адрес')
    except Exception as e:
        print('here', e)


def new_recycling_point(update, context):
    update.message.reply_text('Ваша заявка принята, в скором времени её рассмотрят')
    text = update.message.text.replace('/new_recycling_point', '')

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(post_login, post_password)

    text = "\r\n".join([
        "Subject: Новая точка переработки вторсырья",
        str(text)
    ])

    server.sendmail(post_login, 'r.izmajlov2018@yandex.ru', text.encode('utf-8'))
    server.quit()


def all(update, context):
    try:
        Batteries = [(','.join(point[2].replace(' ', '').replace('\t', '').split(',')[::-1]))
                     for point in db.find_all('Батарейки')]
        Paper_maculature = [(','.join(point[2].replace(' ', '').replace('\t', '').split(',')[::-1]))
                            for point in db.find_all('Бумажная_мукулатура')]
        Halogen_lamps = [(','.join(point[2].replace(' ', '').replace('\t', '').split(',')[::-1]))
                         for point in db.find_all('Галогеновые_лампы')]
        Scrap_metal = [(','.join(point[2].replace(' ', '').replace('\t', '').split(',')[::-1]))
                       for point in db.find_all('Металлолом')]
        PAT = [(','.join(point[2].replace(' ', '').replace('\t', '').split(',')[::-1]))
               for point in db.find_all('ПЭТ')]

        dot_b = [['', i, 'pmdbs'] for i in Batteries]
        dot_p = [['', i, 'pmwts'] for i in Paper_maculature]
        dot_h = [['', i, 'pmyws'] for i in Halogen_lamps]
        dot_m = [['', i, 'pmgrs'] for i in Scrap_metal]
        dot_pat = [['', i, 'pmgns'] for i in PAT]

        text = update.message.text.replace('/all', '')
        temp = {
            'Батарейки': (dot_b, 'Батарейки - синие метки'),
            'Бумажная_мукулатура': (dot_p, 'Бумажная_мукулатура - белые метки'),
            'Галогеновые_лампы': (dot_h, 'Галогеновые_лампы - желтые метки'),
            'Металлолом': (dot_m, 'Металлолом - серые метки'),
            'ПЭТ': (dot_pat, 'ПЭТ - зеленые метки'),
        }
        if not text:
            image = get_image('', dots=dot_b+dot_h+dot_m+dot_pat+dot_p)
            update.message.reply_photo(photo=image, caption='''
Батарейки - синие метки
Бумажная_мукулатура - белые метки
Галогеновые_лампы - желтые метки
Металлолом - серые метки
ПЭТ - зеленые метки''')
        else:
            caption = ''
            res = []
            for type in temp:
                if type.lower() in text.lower():
                    res += temp[type][0]
                    caption += temp[type][1]+'\n'
            if res:
                image = get_image('', dots=res)
                update.message.reply_photo(photo=image, caption=caption)
            else:
                image = get_image('', dots=dot_b+dot_h+dot_m+dot_pat+dot_p)
                update.message.reply_photo(photo=image, caption='''Не найдено ни 1 метки удовлетворяющей вашему запросу
Батарейки - синие метки
Бумажная_мукулатура - белые метки
Галогеновые_лампы - желтые метки
Металлолом - серые метки
ПЭТ - зеленые метки''')

    except Exception as e:
        print(e)


db = Database('database.db')


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("user_data", user_data))
    dp.add_handler(CommandHandler("change_size", change_size))
    dp.add_handler(CommandHandler("change_map_type", change_map_type))
    dp.add_handler(CommandHandler("add_point", add_point))
    dp.add_handler(CommandHandler("remove_point", remove_point))
    dp.add_handler(CommandHandler("near", near))
    dp.add_handler(CommandHandler("new_recycling_point", new_recycling_point))
    dp.add_handler(CommandHandler("all", all))

    dp.add_handler(MessageHandler(Filters.text, echo))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
